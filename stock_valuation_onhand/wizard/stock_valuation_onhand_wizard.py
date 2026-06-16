from odoo import api, fields, models, _
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
        Compute on-hand quantity and unit cost per product as of self.date.

        Strategy:
          - On-hand qty : sum of done stock.move.line up to end of date,
                          restricted to internal locations of selected company/warehouses.
          - Unit cost   : weighted-average from stock.valuation.layer as of that date,
                          falling back to product standard_price.
          - Total value : qty * unit_cost  (only products with qty > 0 are shown).
        """
        self.ensure_one()
        date_end = fields.Datetime.to_datetime(
            fields.Date.to_string(self.date) + ' 23:59:59'
        )

        # 1. Determine internal locations in scope
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

        # 2. Compute on-hand qty per product via stock.move.line
        self.env.cr.execute("""
            SELECT
                sml.product_id,
                SUM(
                    CASE WHEN sml.location_dest_id = ANY(%(locs)s) THEN sml.qty_done ELSE 0 END
                    -
                    CASE WHEN sml.location_id = ANY(%(locs)s) THEN sml.qty_done ELSE 0 END
                ) AS qty_onhand
            FROM stock_move_line sml
            WHERE
                sml.state = 'done'
                AND sml.date <= %(date_end)s
                AND (
                    sml.location_dest_id = ANY(%(locs)s)
                    OR sml.location_id    = ANY(%(locs)s)
                )
            GROUP BY sml.product_id
            HAVING SUM(
                CASE WHEN sml.location_dest_id = ANY(%(locs)s) THEN sml.qty_done ELSE 0 END
                -
                CASE WHEN sml.location_id = ANY(%(locs)s) THEN sml.qty_done ELSE 0 END
            ) > 0
        """, {'locs': internal_location_ids, 'date_end': date_end})
        qty_rows = self.env.cr.fetchall()

        if not qty_rows:
            return []

        product_qty = {row[0]: row[1] for row in qty_rows}

        # 3. Filter by product category if requested
        Product = self.env['product.product']
        products = Product.browse(list(product_qty.keys()))
        if self.categ_ids:
            products = products.filtered(
                lambda p: p.categ_id.id in self.categ_ids.ids
            )
            product_qty = {p.id: product_qty[p.id] for p in products}

        if not product_qty:
            return []

        # 4. Compute unit cost from SVL weighted average as of date_end
        self.env.cr.execute("""
            SELECT
                product_id,
                CASE
                    WHEN SUM(quantity) > 0
                    THEN SUM(value) / SUM(quantity)
                    ELSE 0
                END AS unit_cost
            FROM stock_valuation_layer
            WHERE
                product_id = ANY(%(pids)s)
                AND company_id = %(company_id)s
                AND create_date <= %(date_end)s
            GROUP BY product_id
        """, {
            'pids': list(product_qty.keys()),
            'company_id': self.company_id.id,
            'date_end': date_end,
        })
        product_cost = {row[0]: row[1] for row in self.env.cr.fetchall()}

        # 5. Build report lines
        currency = self.company_id.currency_id
        created_by = self.env.user.name
        created_on = fields.Date.to_string(fields.Date.today())

        lines = []
        for product in Product.browse(list(product_qty.keys())):
            qty = product_qty[product.id]
            unit_cost = product_cost.get(product.id) or product.standard_price
            total_value = qty * unit_cost

            categ = product.categ_id
            valuation_account = ''
            if categ.property_stock_valuation_account_id:
                acc = categ.property_stock_valuation_account_id
                valuation_account = '%s %s' % (acc.code, acc.name)

            lines.append({
                'company': self.company_id.name,
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
                'currency_symbol': currency.symbol,
                'currency_position': currency.position,
            })

        lines.sort(key=lambda l: (l['category'], l['product']))
        return lines

    def action_print_report(self):
        self.ensure_one()
        lines = self._get_report_data()
        if not lines:
            raise UserError(_(
                'No on-hand inventory found for the selected criteria as of %s.'
            ) % fields.Date.to_string(self.date))

        grand_total = sum(l['total_value'] for l in lines)

        data = {
            'date': fields.Date.to_string(self.date),
            'company': self.company_id.name,
            'currency_symbol': self.company_id.currency_id.symbol,
            'currency_position': self.company_id.currency_id.position,
            'lines': lines,
            'grand_total': grand_total,
        }
        return self.env.ref(
            'stock_valuation_onhand.action_report_stock_valuation_onhand'
        ).report_action(self, data=data)
