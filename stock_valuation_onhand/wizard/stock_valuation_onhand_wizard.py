import logging

from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockValuationOnhandWizard(models.TransientModel):
    _name = 'stock.valuation.onhand.wizard'
    _description = 'Stock Valuation On-Hand Report Wizard'

    date = fields.Date(
        string='As of Date',
        required=True,
        default=fields.Date.context_today,
        help='Report will show on-hand inventory value as of end of this date.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Warehouses',
        help='Leave empty to include all warehouses.',
    )
    categ_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        help='Leave empty to include all categories.',
    )

    def _get_report_data(self):
        """
        On-hand inventory value as of self.date. qty and value both
        come straight from stock_valuation_layer, summed per product
        for the company for every layer with create_date <= date_end -
        one source of truth for both numbers, matching how Odoo 16's
        own Inventory > Reporting > Valuation computes a CURRENT total.

        This deliberately replaced an earlier approach that derived
        qty from a separate stock_move_line query and only pulled cost
        from stock_valuation_layer - two independently-tracked numbers
        that can drift apart (manual quant adjustments, negative
        stock, non-owned stock, etc.), which is what caused this
        report's total to run ~$200k under Odoo's own valuation
        report.

        IMPORTANT: this sums quantity/value (each layer's original,
        immutable amount as recorded at creation), NOT
        remaining_qty/remaining_value (Odoo's live running balance,
        which gets decremented on an OLD layer by a NEWER
        delivery/consumption regardless of that consumption's own
        date). Using remaining_qty/remaining_value made this report's
        "as of a past date" totals silently drift every day forward as
        ordinary business activity kept consuming older layers -
        running the same date_end on two different days could give two
        different answers. quantity/value never change after a layer
        is created, so summing them for everything up to date_end is a
        standard ledger-balance calculation that gives the same answer
        no matter when you run it. (For date_end = today, this and the
        remaining_*-based total should normally match anyway, since
        both describe the same current on-hand position - only a
        report for a PAST date_end actually depends on which of the
        two you use.)

        IMPORTANT BEHAVIOR CHANGE: stock_valuation_layer has no
        location field - Odoo's own valuation is a company-wide,
        per-product figure, not a per-warehouse one. So warehouse_ids
        here no longer scopes the VALUE (that wouldn't match Odoo's
        logic even if we tried) - it now scopes which PRODUCTS appear
        at all (only products currently on-hand in the selected
        warehouse(s), via stock.quant), each still shown at its full
        company-wide valuation. The Location column is similarly now
        an informational per-location quantity breakdown pulled from
        stock.quant for display only - it plays no part in qty/cost/
        total_value, which always come from stock_valuation_layer.

        Columns returned per line:
          company, location, po_numbers, reference, created_by, created_on,
          product, category, valuation_account, qty, uom,
          unit_cost, total_value, sales_price, cost,
          currency_symbol, currency_position
        """
        self.ensure_one()
        date_end = fields.Datetime.to_datetime(
            fields.Date.to_string(self.date) + ' 23:59:59'
        )

        # 1. Core valuation numbers - straight from stock_valuation_layer,
        #    grouped by product, same as Odoo's own valuation report.
        #    No location involved at all here.
        #IMPORTANT: this deliberately sums quantity/value, NOT
        #remaining_qty/remaining_value. remaining_qty/remaining_value
        #are LIVE running balances - Odoo decrements them on an old
        #layer whenever ANY later delivery/consumption (FIFO/AVCO)
        #draws from it, regardless of what date that consumption
        #itself happened on. So a report run "as of 8/31" that reads
        #remaining_qty/remaining_value keeps drifting every day
        #forward, because a delivery next week that consumes from an
        #8/20 layer reduces that layer's remaining_* TODAY - even
        #though we're asking what was on hand back on 8/31. That's
        #what was causing this report to return different numbers for
        #the exact same as-of date depending on which day you ran it.
        #
        #quantity/value, by contrast, are each layer's original
        #amounts as recorded when it was created (positive for
        #receipts, negative for deliveries/consumption) - they never
        #get mutated after the fact. Summing quantity/value for every
        #layer with create_date <= date_end is a standard ledger-
        #balance calculation: it reconstructs on-hand qty/value at
        #that exact point in time, and stays stable no matter when you
        #run the report afterward, since it only ever reads immutable,
        #already-final numbers.
        #
        #COALESCE is still on the individual value column (not
        #wrapped around the whole SUM), so one layer with a null value
        #contributes 0 rather than poisoning the entire product's SUM
        #(NULL + anything = NULL in SQL) - see products_with_null_layers.
        self.env.cr.execute("""
            SELECT
                product_id,
                SUM(quantity) AS qty,
                SUM(COALESCE(value,0)) AS total_value,
                COUNT(*) FILTER (WHERE quantity != 0 AND value IS NULL) AS null_value_layers
            FROM stock_valuation_layer
            WHERE company_id = %(company_id)s
              AND create_date <= %(date_end)s
            GROUP BY product_id
            HAVING SUM(quantity) != 0
        """, {'company_id': self.company_id.id, 'date_end': date_end})
        svl_rows = self.env.cr.fetchall()  # [(product_id, qty, total_value, null_value_layers), ...]

        #Products where at least one layer up to date_end has no
        #recorded value at all - their total_value is understated by
        #whatever that layer's real value should have been. Surfaced
        #in the warning below rather than silently masked.
        products_with_null_layers = {r[0]: r[3] for r in svl_rows if r[3]}
        if products_with_null_layers:
            #Not raised as a UserError - the report should still
            #generate, just understated for these specific products -
            #but this needs to be visible somewhere, since it's very
            #likely the same root cause behind day-to-day total
            #swings: which products have a null-valued layer, and how
            #many, can change from one day's data to the next.
            _logger.warning(
                "Stock Valuation On-Hand: %d product(s) have on-hand "
                "stock_valuation_layer rows with remaining_qty != 0 but "
                "remaining_value IS NULL - their reported value is "
                "understated by whatever those layers should have been "
                "worth. product_id: null-valued layer count = %s",
                len(products_with_null_layers), products_with_null_layers,
            )

        if not svl_rows:
            return []

        product_qty = {r[0]: r[1] for r in svl_rows}
        product_value = {r[0]: r[2] for r in svl_rows}
        product_ids = list(product_qty.keys())

        # 2. Product type filter (always) + active filter (Odoo's own
        #    valuation views default to active products only, and this
        #    was previously an outstanding gap in this report - closing
        #    it here since it's now a one-line addition).
        Product = self.env['product.product']
        excluded_types = {'service', 'consu'}
        products_all = Product.browse(product_ids)
        allowed = set(
            products_all
            .filtered(lambda p: p.active and p.detailed_type not in excluded_types)
            .ids
        )

        # 3. Category filter, if requested.
        if self.categ_ids:
            allowed &= set(
                Product.browse(list(allowed))
                .filtered(lambda p: p.categ_id.id in self.categ_ids.ids)
                .ids
            )

        # 4. Warehouse filter, if requested - narrows WHICH products
        #    show up (must currently have on-hand qty somewhere in the
        #    selected warehouse(s)), does NOT change their value.
        scope_location_ids = None
        if self.warehouse_ids:
            warehouses = self.env['stock.warehouse'].browse(self.warehouse_ids.ids)
            Location = self.env['stock.location']
            scope_location_ids = set()
            for wh in warehouses:
                #view_location_id, not lot_stock_id - lot_stock_id only
                #covers WH/Stock; view_location_id also reaches
                #WH/Input, WH/Output, WH/Quality Control, WH/Packing
                #Zone, etc. Using lot_stock_id here previously caused
                #this report to miss stock sitting in those buffer
                #locations entirely.
                locs = Location.search([
                    ('id', 'child_of', wh.view_location_id.id),
                    ('usage', '=', 'internal'),
                ])
                scope_location_ids.update(locs.ids)
            scope_location_ids = list(scope_location_ids)

            self.env.cr.execute("""
                SELECT DISTINCT product_id
                FROM stock_quant
                WHERE company_id = %(company_id)s
                  AND location_id = ANY(%(locs)s)
                  AND quantity != 0
                  AND product_id = ANY(%(pids)s)
            """, {
                'company_id': self.company_id.id,
                'locs': scope_location_ids,
                'pids': list(allowed),
            })
            allowed &= {r[0] for r in self.env.cr.fetchall()}

        product_ids = [pid for pid in product_ids if pid in allowed]
        if not product_ids:
            return []

        # 5. Informational location breakdown per product (display only -
        #    does not feed qty/cost/total_value). Scoped to the selected
        #    warehouse(s) if any were chosen, otherwise every internal
        #    location for the company.
        if scope_location_ids is None:
            self.env.cr.execute("""
                SELECT id FROM stock_location
                WHERE company_id = %(company_id)s AND usage = 'internal'
            """, {'company_id': self.company_id.id})
            scope_location_ids = [r[0] for r in self.env.cr.fetchall()]

        self.env.cr.execute("""
            SELECT sq.product_id, sl.complete_name, sq.quantity
            FROM stock_quant sq
            JOIN stock_location sl ON sl.id = sq.location_id
            WHERE sq.company_id = %(company_id)s
              AND sq.location_id = ANY(%(locs)s)
              AND sq.quantity != 0
              AND sq.product_id = ANY(%(pids)s)
            ORDER BY sq.product_id, sl.complete_name
        """, {
            'company_id': self.company_id.id,
            'locs': scope_location_ids,
            'pids': product_ids,
        })
        product_locations = {}
        for pid, loc_name, qty in self.env.cr.fetchall():
            product_locations.setdefault(pid, []).append('%s: %.4f' % (loc_name, qty))

        # 6. PO numbers per product - same scope as the location
        #    breakdown above, up to date_end.
        self.env.cr.execute("""
            SELECT
                sml.product_id,
                STRING_AGG(DISTINCT po.name, ', ' ORDER BY po.name) AS po_numbers
            FROM stock_move_line sml
            JOIN stock_move sm         ON sm.id = sml.move_id
            JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
            JOIN purchase_order po      ON po.id = pol.order_id
            WHERE sml.state = 'done'
              AND sml.date <= %(date_end)s
              AND sml.location_dest_id = ANY(%(locs)s)
              AND sml.product_id = ANY(%(pids)s)
            GROUP BY sml.product_id
        """, {
            'locs': scope_location_ids,
            'date_end': date_end,
            'pids': product_ids,
        })
        product_po = {r[0]: r[1] for r in self.env.cr.fetchall()}

        # 7. Build report lines - one row per product now (not per
        #    product+location), since valuation itself is per-product.
        currency = self.company_id.currency_id
        created_by = self.env.user.name
        created_on = fields.Date.to_string(fields.Date.today())

        products = {p.id: p for p in Product.browse(product_ids)}
        lines = []
        for product_id in product_ids:
            product = products[product_id]
            qty = product_qty[product_id]
            total_value = product_value[product_id]
            unit_cost = (total_value / qty) if qty else 0.0

            categ = product.categ_id
            valuation_account = ''
            if categ.property_stock_valuation_account_id:
                acc = categ.property_stock_valuation_account_id
                valuation_account = '%s %s' % (acc.code, acc.name)

            lines.append({
                'company': self.company_id.name,
                'location': ', '.join(product_locations.get(product_id, [])),
                'po_numbers': product_po.get(product_id, ''),
                'reference': product.default_code or '',
                'created_by': created_by,
                'created_on': created_on,
                'product': product.display_name,
                'category': categ.complete_name,
                'valuation_account': valuation_account or 'N/A',
                'qty': qty,
                'uom': product.uom_id.name,
                'unit_cost': unit_cost,
                'total_value': total_value,
                'sales_price': product.lst_price,
                'cost': product.standard_price,
                'currency_symbol': currency.symbol,
                'currency_position': currency.position,
            })

        lines.sort(key=lambda l: (l['category'], l['product']))
        return lines

    def _prepare_report_values(self):
        """Build the data dict consumed by both PDF and XLSX templates."""
        self.ensure_one()
        lines = self._get_report_data()
        if not lines:
            raise UserError(_(
                'No on-hand inventory found for the selected criteria as of %s.'
            ) % fields.Date.to_string(self.date))

        grand_total = sum(l['total_value'] for l in lines)

        return {
            'date': fields.Date.to_string(self.date),
            'company': self.company_id.name,
            'currency_symbol': self.company_id.currency_id.symbol,
            'currency_position': self.company_id.currency_id.position,
            'lines': lines,
            'grand_total': grand_total,
        }

    def action_print_report(self):
        self.ensure_one()
        data = self._prepare_report_values()
        return self.env.ref(
            'stock_valuation_onhand.action_report_stock_valuation_onhand'
        ).report_action(self, data=data)

    def action_print_xlsx(self):
        self.ensure_one()
        data = self._prepare_report_values()
        return self.env.ref(
            'stock_valuation_onhand.action_report_stock_valuation_onhand_xlsx'
        ).report_action(self, data=data)
