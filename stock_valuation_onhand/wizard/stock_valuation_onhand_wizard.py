import logging
from datetime import datetime, time

import pytz

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

    def _get_date_end(self):
        """End of the selected day in the user's timezone, as the naive
        UTC datetime that stock_move_line.date / stock_valuation_layer.
        create_date are stored in. (Using 23:59:59 as if it were UTC
        cut off the last several hours of the selected day for
        non-UTC users, so e.g. a report run for today in the evening
        missed that afternoon's moves.)"""
        self.ensure_one()
        tz_name = self.env.user.tz or self.env.context.get('tz') or 'UTC'
        tz = pytz.timezone(tz_name)
        local_end = tz.localize(datetime.combine(self.date, time(23, 59, 59)))
        return local_end.astimezone(pytz.utc).replace(tzinfo=None)

    def _get_report_data(self):
        """
        On-hand inventory value as of self.date.

        QUANTITIES come from stock.quant - the same thing Inventory >
        Reporting > Stock / the Quants list shows - one row per
        (location, product, lot). For a past date the current quants
        are rolled BACK by reversing every done move line dated after
        date_end, so a run for today is exactly the quants, and a run
        for a past date is the quants as they stood then.

        This replaced an approach that rebuilt per-location quantities
        by summing ALL done move lines since the beginning of time and
        then plugged any difference against the valuation layers into
        an "Unallocated" line. Both of those produced rows that do not
        exist in the quants: any gap between history and quants
        (archived locations, legacy/adjusted data, stock moved with a
        different lot than it came in with, layers with no matching
        stock such as revaluations or landed costs) showed up as wrong
        quantities or phantom lines.

        VALUE is qty x the product's unit cost from
        stock_valuation_layer (sum(value) / sum(quantity) over layers
        created up to date_end). If a product has no positive layer
        quantity to derive a cost from, its standard_price is used.

        Locations: internal locations of the company (or of the
        selected warehouses, via view_location_id so WH/Input,
        WH/Output etc. are included). Archived locations are included,
        because quants in them still exist.

        Products with valuation layers whose total qty/value does not
        agree with what the quants say are NOT shown as lines; they
        are returned separately as `unreconciled` so the difference
        against Odoo's Valuation report is visible rather than
        silently plugged into the lines. (Not computed when a
        warehouse filter is set, since layers are company-wide.)

        Returns (groups, unreconciled):
          groups: [{'location': str, 'total_value': float, 'lines': [line, ...]}]
          unreconciled: [{'reference', 'product', 'category', 'uom',
                          'svl_qty', 'quant_qty', 'diff_qty',
                          'svl_value', 'quant_value', 'diff_value'}]
        """
        self.ensure_one()
        date_end = self._get_date_end()
        company_id = self.company_id.id

        # 1. Locations in scope (archived ones included).
        Location = self.env['stock.location'].with_context(active_test=False)
        if self.warehouse_ids:
            scope_locations = Location
            for wh in self.warehouse_ids:
                scope_locations |= Location.search([
                    ('id', 'child_of', wh.view_location_id.id),
                    ('usage', '=', 'internal'),
                ])
        else:
            scope_locations = Location.search([
                ('company_id', '=', company_id),
                ('usage', '=', 'internal'),
            ])
        scope_location_ids = scope_locations.ids
        if not scope_location_ids:
            return [], []

        # 2. Current quants per (product, location, lot). Packages and
        #    owners are summed away, so a row is a location/lot total.
        self.env.cr.execute("""
            SELECT product_id, location_id, lot_id, SUM(quantity)
            FROM stock_quant
            WHERE company_id = %(company_id)s
              AND location_id = ANY(%(locs)s)
            GROUP BY product_id, location_id, lot_id
        """, {'company_id': company_id, 'locs': scope_location_ids})
        qty_map = {}  # (product_id, location_id, lot_id|None) -> qty
        for pid, loc_id, lot_id, qty in self.env.cr.fetchall():
            qty_map[(pid, loc_id, lot_id)] = qty or 0.0

        # 3. Roll back: net effect of done move lines AFTER date_end on
        #    each (product, location, lot) - qty into the location minus
        #    qty out of it. Converted to the product's own UoM.
        self.env.cr.execute("""
            SELECT product_id, location_id, lot_id, SUM(qty) AS qty
            FROM (
                SELECT sml.product_id,
                       sml.location_dest_id AS location_id,
                       sml.lot_id,
                       sml.qty_done / su.factor * pu.factor AS qty
                FROM stock_move_line sml
                JOIN product_product pp  ON pp.id = sml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN uom_uom pu          ON pu.id = pt.uom_id
                JOIN uom_uom su          ON su.id = sml.product_uom_id
                WHERE sml.state = 'done'
                  AND sml.company_id = %(company_id)s
                  AND sml.date > %(date_end)s
                  AND sml.location_dest_id = ANY(%(locs)s)
                UNION ALL
                SELECT sml.product_id,
                       sml.location_id AS location_id,
                       sml.lot_id,
                       -(sml.qty_done / su.factor * pu.factor) AS qty
                FROM stock_move_line sml
                JOIN product_product pp  ON pp.id = sml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN uom_uom pu          ON pu.id = pt.uom_id
                JOIN uom_uom su          ON su.id = sml.product_uom_id
                WHERE sml.state = 'done'
                  AND sml.company_id = %(company_id)s
                  AND sml.date > %(date_end)s
                  AND sml.location_id = ANY(%(locs)s)
            ) m
            GROUP BY product_id, location_id, lot_id
        """, {
            'company_id': company_id,
            'date_end': date_end,
            'locs': scope_location_ids,
        })
        for pid, loc_id, lot_id, net_after in self.env.cr.fetchall():
            key = (pid, loc_id, lot_id)
            qty_map[key] = qty_map.get(key, 0.0) - (net_after or 0.0)

        qty_map = {k: q for k, q in qty_map.items() if round(q, 4) != 0}

        # 4. Valuation layers up to date_end, per product - used for
        #    unit cost, and for the reconciliation below.
        self.env.cr.execute("""
            SELECT
                product_id,
                SUM(quantity) AS qty,
                SUM(COALESCE(value, 0)) AS total_value,
                COUNT(*) FILTER (WHERE quantity != 0 AND value IS NULL) AS null_value_layers
            FROM stock_valuation_layer
            WHERE company_id = %(company_id)s
              AND create_date <= %(date_end)s
            GROUP BY product_id
        """, {'company_id': company_id, 'date_end': date_end})
        svl_rows = self.env.cr.fetchall()
        svl_qty = {r[0]: r[1] or 0.0 for r in svl_rows}
        svl_value = {r[0]: r[2] or 0.0 for r in svl_rows}
        products_with_null_layers = {r[0]: r[3] for r in svl_rows if r[3]}
        if products_with_null_layers:
            _logger.warning(
                "Stock Valuation On-Hand: %d product(s) have valuation "
                "layers with a quantity but no value - their value is "
                "understated. product_id: null-valued layer count = %s",
                len(products_with_null_layers), products_with_null_layers,
            )

        # 5. Product filters: storable products only (archived ones
        #    kept), plus the category filter if requested.
        candidate_ids = {k[0] for k in qty_map} | set(svl_qty)
        if not candidate_ids:
            return [], []
        Product = self.env['product.product'].with_context(
            active_test=False).with_company(self.company_id)
        products = {
            p.id: p for p in Product.browse(list(candidate_ids))
            if p.type not in ('service', 'consu')
            and (not self.categ_ids or p.categ_id.id in self.categ_ids.ids)
        }
        qty_map = {k: q for k, q in qty_map.items() if k[0] in products}
        if not qty_map and self.warehouse_ids:
            return [], []

        # 6. Names: locations, lots, and the MO(s) that produced each lot.
        location_names = {
            l.id: l.complete_name
            for l in self.env['stock.location'].browse(
                list({k[1] for k in qty_map}))
        }
        lot_ids = list({k[2] for k in qty_map if k[2]})
        lot_names = {}
        lot_mos = {}
        if lot_ids:
            lot_model = self.env['stock.move.line']._fields['lot_id'].comodel_name
            lot_names = {l.id: l.name for l in self.env[lot_model].browse(lot_ids)}
            if 'mrp.production' in self.env:
                self.env.cr.execute("""
                    SELECT sml.lot_id,
                           STRING_AGG(DISTINCT mp.name, ', ' ORDER BY mp.name) AS mo_numbers
                    FROM stock_move_line sml
                    JOIN stock_move sm        ON sm.id = sml.move_id
                    JOIN mrp_production mp    ON mp.id = sm.production_id
                    WHERE sml.state = 'done'
                      AND sml.company_id = %(company_id)s
                      AND sml.date <= %(date_end)s
                      AND sml.lot_id = ANY(%(lot_ids)s)
                    GROUP BY sml.lot_id
                """, {
                    'company_id': company_id,
                    'date_end': date_end,
                    'lot_ids': lot_ids,
                })
                lot_mos = {r[0]: r[1] for r in self.env.cr.fetchall()}

        # 7. PO receipts per product (and lot), newest first, so each
        #    row can be matched to the POs that plausibly still account
        #    for its stock (see _po_numbers_for_row). Receipts = done
        #    purchase move lines into an internal location, up to
        #    date_end, converted to the product's own UoM.
        po_receipts = {}  # (product_id, lot_id|None) -> [(po_name, qty), ...] newest first
        shown_pids = list({k[0] for k in qty_map})
        if shown_pids:
            self.env.cr.execute("""
                SELECT sml.product_id, sml.lot_id, po.name,
                       SUM(sml.qty_done / su.factor * pu.factor) AS qty,
                       MAX(sml.date) AS last_date
                FROM stock_move_line sml
                JOIN stock_move sm           ON sm.id = sml.move_id
                JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
                JOIN purchase_order po       ON po.id = pol.order_id
                JOIN stock_location dest     ON dest.id = sml.location_dest_id
                JOIN product_product pp      ON pp.id = sml.product_id
                JOIN product_template pt     ON pt.id = pp.product_tmpl_id
                JOIN uom_uom pu              ON pu.id = pt.uom_id
                JOIN uom_uom su              ON su.id = sml.product_uom_id
                WHERE sml.state = 'done'
                  AND sml.company_id = %(company_id)s
                  AND sml.date <= %(date_end)s
                  AND dest.usage = 'internal'
                  AND sml.product_id = ANY(%(pids)s)
                GROUP BY sml.product_id, sml.lot_id, po.name
                ORDER BY last_date DESC, po.name DESC
            """, {
                'company_id': company_id,
                'date_end': date_end,
                'pids': shown_pids,
            })
            for pid, lot_id, po_name, qty, _last in self.env.cr.fetchall():
                po_receipts.setdefault((pid, lot_id), []).append((po_name, qty or 0.0))

        def po_numbers_for_row(product_id, lot_id, row_qty):
            """POs behind the stock on one row. Assumes first-in-first-out
            consumption: the stock still on hand came from the most recent
            receipts, so walk back from the newest receipt until the row's
            quantity is covered. A lot row only considers receipts of that
            lot; a no-lot row only considers receipts without a lot.
            Rows with zero/negative qty get none."""
            if row_qty <= 0:
                return ''
            names, covered = [], 0.0
            for po_name, rec_qty in po_receipts.get((product_id, lot_id), []):
                if rec_qty <= 0:
                    continue
                if po_name not in names:
                    names.append(po_name)
                covered += rec_qty
                if round(covered - row_qty, 4) >= 0:
                    break
            return ', '.join(sorted(names))

        # 8. Build report lines - one per (location, product, lot).
        currency = self.company_id.currency_id
        created_by = self.env.user.name
        created_on = fields.Date.to_string(fields.Date.today())

        groups = {}  # location name -> list of lines
        reported_qty = {}
        reported_value = {}
        for (product_id, loc_id, lot_id), qty in qty_map.items():
            product = products[product_id]
            p_qty = svl_qty.get(product_id, 0.0)
            if p_qty > 0:
                unit_cost = svl_value.get(product_id, 0.0) / p_qty
            else:
                unit_cost = product.standard_price
            value = qty * unit_cost

            categ = product.categ_id
            valuation_account = ''
            if categ.property_stock_valuation_account_id:
                acc = categ.property_stock_valuation_account_id
                valuation_account = '%s %s' % (acc.code, acc.name)

            loc_name = location_names.get(loc_id, str(loc_id))
            groups.setdefault(loc_name, []).append({
                'company': self.company_id.name,
                'location': loc_name,
                'po_numbers': po_numbers_for_row(product_id, lot_id, qty),
                'lot_name': lot_names.get(lot_id, '') if lot_id else '',
                'mo_numbers': lot_mos.get(lot_id, '') if lot_id else '',
                'reference': product.default_code or '',
                'created_by': created_by,
                'created_on': created_on,
                'product': product.display_name,
                'category': categ.complete_name,
                'valuation_account': valuation_account or 'N/A',
                'qty': qty,
                'uom': product.uom_id.name,
                'unit_cost': unit_cost,
                'total_value': value,
                'sales_price': product.lst_price,
                'cost': product.standard_price,
                'currency_symbol': currency.symbol,
                'currency_position': currency.position,
            })
            reported_qty[product_id] = reported_qty.get(product_id, 0.0) + qty
            reported_value[product_id] = reported_value.get(product_id, 0.0) + value

        # 9. Reconciliation against the valuation layers (company-wide,
        #    so not meaningful under a warehouse filter).
        unreconciled = []
        if not self.warehouse_ids:
            for product_id, product in products.items():
                s_qty = svl_qty.get(product_id, 0.0)
                s_val = svl_value.get(product_id, 0.0)
                q_qty = reported_qty.get(product_id, 0.0)
                q_val = reported_value.get(product_id, 0.0)
                if round(s_qty - q_qty, 4) == 0 and round(s_val - q_val, 2) == 0:
                    continue
                unreconciled.append({
                    'reference': product.default_code or '',
                    'product': product.display_name,
                    'category': product.categ_id.complete_name,
                    'uom': product.uom_id.name,
                    'svl_qty': s_qty,
                    'quant_qty': q_qty,
                    'diff_qty': s_qty - q_qty,
                    'svl_value': s_val,
                    'quant_value': q_val,
                    'diff_value': s_val - q_val,
                })
            unreconciled.sort(key=lambda r: (r['category'], r['reference'], r['product']))
            if unreconciled:
                _logger.info(
                    "Stock Valuation On-Hand: %d product(s) where quants "
                    "and valuation layers disagree as of %s (net value "
                    "difference %.2f).",
                    len(unreconciled), self.date,
                    sum(r['diff_value'] for r in unreconciled),
                )

        result = []
        for loc_name in sorted(groups):
            loc_lines = sorted(
                groups[loc_name],
                key=lambda l: (l['category'], l['reference'], l['product'], l['lot_name']))
            result.append({
                'location': loc_name,
                'total_value': sum(l['total_value'] for l in loc_lines),
                'lines': loc_lines,
            })
        return result, unreconciled

    def _prepare_report_values(self):
        """Build the data dict consumed by both PDF and XLSX templates."""
        self.ensure_one()
        groups, unreconciled = self._get_report_data()
        if not groups:
            raise UserError(_(
                'No on-hand inventory found for the selected criteria as of %s.'
            ) % fields.Date.to_string(self.date))

        lines = [l for g in groups for l in g['lines']]
        grand_total = sum(g['total_value'] for g in groups)

        return {
            'date': fields.Date.to_string(self.date),
            'company': self.company_id.name,
            'currency_symbol': self.company_id.currency_id.symbol,
            'currency_position': self.company_id.currency_id.position,
            'groups': groups,
            'unreconciled': unreconciled,
            'lines': lines,
            'grand_total': grand_total,
        }

    def action_print_report(self):
        # No `data` here on purpose: the report is built server-side from
        # this wizard record (see the report parsers). Passing the whole
        # result set as `data` makes the browser POST it back to
        # /report/download, which fails with a 500 once it gets large.
        self.ensure_one()
        return self.env.ref(
            'stock_valuation_onhand.action_report_stock_valuation_onhand'
        ).report_action(self)

    def action_print_xlsx(self):
        self.ensure_one()
        return self.env.ref(
            'stock_valuation_onhand.action_report_stock_valuation_onhand_xlsx'
        ).report_action(self)
