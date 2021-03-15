# -*- encoding: utf-8 -*-


from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = {}
        for product_tmpl in self:
            write_vals = {}
            if 'uom_po_id' in vals and 'uom_id' not in vals:
                write_vals['uom_po_id'] = vals.pop("uom_po_id", None)
            if vals:
                res = super(ProductTemplate, self).write(vals)
            if write_vals:
                models.Model.write(self, write_vals)
            return res
