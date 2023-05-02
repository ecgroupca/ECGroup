from odoo import api, fields, models


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    parallel_steps = fields.Boolean(string="Parallel Steps")
    barcoding_steps = fields.Boolean(string="Barcoding - All Open Steps")
