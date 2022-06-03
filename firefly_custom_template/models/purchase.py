from odoo import models, fields

class Purchase(models.Model):
    _inherit = 'purchase.order'

    quality_tag_ids = fields.Many2many('quality.tag.po', string="Quality Tags")

    def action_rfq_send(self):
        purchase_obj = super().action_rfq_send()

        ir_model_data = self.env['ir.model.data']
        ctx = purchase_obj['context']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[2]
            else:
                template_id = ir_model_data._xmlid_lookup('firefly_custom_template.email_template_edi_purchase_done_firefly')[2]
        except ValueError:
            template_id = False
        ctx.update({
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
        })
        purchase_obj['context'] = ctx

        return purchase_obj
