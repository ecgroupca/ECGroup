from odoo import fields, models, _
from odoo.exceptions import UserError


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
        Compute on-hand qty per (product, internal location) as of self.date.

        Columns returned per line:
          company, location, po_numbers, reference, created_by, created_on,
          product, category, valuation_account, qty, uom,
          unit_cost, total_value, sales_price, cost,
          currency_symbol, currency_position

        Strategy:
          - Qty per (product, location): sum done stock.move.line up to date_end,
            one row per unique (product_id, internal location_dest/src).
          - PO numbers: most recent PO(s) that received this product into any
            internal location in scope, as a comma-separated string.
          - Unit cost: weighted-average SVL as of date_end, fallback to standard_price.
          - Sales price / Cost: pulled directly from product.product / product.template.
        """
        self.ensure_one()
        date_end = fields.Datetime.to_datetime(
            fields.Date.to_string(self.date) + ' 23:59:59'
        )

        # 1. Resolve internal locations in scope
        domain_wh = [('company_id', '=', self.company_id.id)]
        if self.warehouse_ids:
            domain_wh.append(('id', 'in', self.warehouse_ids.ids))
        warehouses = self.env['stock.warehouse'].search(domain_wh)
        if not warehouses:
            raise UserError(_('No warehouse found for the selected company.'))

        Location = self.env['stock.location']
        internal_location_ids = set()
        for wh in warehouses:
            locs = Location.search([
                ('id', 'child_of', wh.lot_stock_id.id),
                ('usage', '=', 'internal'),
            ])
            internal_location_ids.update(locs.ids)

        if not internal_location_ids:
            raise UserError(_('No internal stock locations found for the selected warehouses.'))

        internal_location_ids = list(internal_location_ids)

        # 2. On-hand qty per (product, location)
        self.env.cr.execute("""
            SELECT
                product_id,
                location_id,
                SUM(qty_in - qty_out) AS qty_onhand
            FROM (
                SELECT
                    sml.product_id,
                    sml.location_dest_id  AS location_id,
                    sml.qty_done          AS qty_in,
                    0                     AS qty_out
                FROM stock_move_line sml
                WHERE sml.state = 'done'
                  AND sml.date <= %(date_end)s
                  AND sml.location_dest_id = ANY(%(locs)s)
                UNION ALL
                SELECT
                    sml.product_id,
                    sml.location_id       AS location_id,
                    0                     AS qty_in,
                    sml.qty_done          AS qty_out
                FROM stock_move_line sml
                WHERE sml.state = 'done'
                  AND sml.date <= %(date_end)s
                  AND sml.location_id = ANY(%(locs)s)
            ) sub
            GROUP BY product_id, location_id
            HAVING SUM(qty_in - qty_out) > 0
        """, {'locs': internal_location_ids, 'date_end': date_end})
        qty_rows = self.env.cr.fetchall()  # [(product_id, location_id, qty), ...]

        if not qty_rows:
            return []

        product_ids = list({r[0] for r in qty_rows})

        # 3. Filter by product type (always) and category (if requested)
        Product = self.env['product.product']
        excluded_types = {'service', 'consu'}
        allowed = set(
            Product.browse(product_ids)
            .filtered(lambda p: p.detailed_type not in excluded_types)
            .ids
        )
        if self.categ_ids:
            allowed &= set(
                Product.browse(list(allowed))
                .filtered(lambda p: p.categ_id.id in self.categ_ids.ids)
                .ids
            )
        qty_rows = [r for r in qty_rows if r[0] in allowed]
        product_ids = list({r[0] for r in qty_rows})

        if not qty_rows:
            return []

        # 4. Weighted-average unit cost from SVL as of date_end
        self.env.cr.execute("""
            SELECT
                product_id,
                CASE WHEN SUM(quantity) > 0
                     THEN SUM(value) / SUM(quantity)
                     ELSE 0
                END AS unit_cost
            FROM stock_valuation_layer
            WHERE product_id = ANY(%(pids)s)
              AND company_id = %(company_id)s
              AND create_date <= %(date_end)s
            GROUP BY product_id
        """, {
            'pids': product_ids,
            'company_id': self.company_id.id,
            'date_end': date_end,
        })
        product_cost = {r[0]: r[1] for r in self.env.cr.fetchall()}

        # 5. PO numbers per product: all POs that received this product
        #    into an internal location in scope, up to date_end.
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
            'locs': internal_location_ids,
            'date_end': date_end,
            'pids': product_ids,
        })
        product_po = {r[0]: r[1] for r in self.env.cr.fetchall()}

        # 6. Location display names
        loc_ids = list({r[1] for r in qty_rows})
        loc_names = {
            loc.id: loc.display_name
            for loc in Location.browse(loc_ids)
        }

        # 7. Build report lines
        currency = self.company_id.currency_id
        created_by = self.env.user.name
        created_on = fields.Date.to_string(fields.Date.today())

        products = {p.id: p for p in Product.browse(product_ids)}
        lines = []
        for product_id, location_id, qty in qty_rows:
            product = products[product_id]
            unit_cost = product_cost.get(product_id) or product.standard_price
            total_value = qty * unit_cost

            categ = product.categ_id
            valuation_account = ''
            if categ.property_stock_valuation_account_id:
                acc = categ.property_stock_valuation_account_id
                valuation_account = '%s %s' % (acc.code, acc.name)

            lines.append({
                'company': self.company_id.name,
                'location': loc_names.get(location_id, ''),
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

        lines.sort(key=lambda l: (l['category'], l['product'], l['location']))
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
