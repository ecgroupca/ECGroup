from odoo import api, fields, models

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[
        ('purchase_agreement', "Create Purchase Agreements"),
        ('vendor_bill', "Create Bills")
    ])

    has_agreement_type = fields.Selection(CATEGORY_SELECTION, string="Has Agreement Type", default="no", required=True)
    has_vendor = fields.Selection(CATEGORY_SELECTION, string="Has Vendor", default="no", required=True)
    has_bill_reference = fields.Selection(CATEGORY_SELECTION, string="Has Bill Reference", default="no", required=True)
    has_price = fields.Selection(CATEGORY_SELECTION, string="Has Price", default="no", required=True)
    has_account = fields.Selection(CATEGORY_SELECTION, string="Has Account", default="no", required=True)
    has_analytic_account = fields.Selection(CATEGORY_SELECTION, string="Has Analytic Account", default="no", required=True)
    has_analytic_tag = fields.Selection(CATEGORY_SELECTION, string="Has Analytic Tag", default="no", required=True)
    has_quality_tag = fields.Selection(CATEGORY_SELECTION, string="Has Quality Tag", default="no", required=True)

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        super()._onchange_approval_type()
        if self.approval_type == 'purchase_agreement':
            self.write({
                'has_product': 'required',
                'has_quantity': 'required',
                'has_agreement_type': 'required',
                'has_vendor': 'optional',
                'has_analytic_account': 'optional',
                'has_analytic_tag': 'optional',
            })
        elif self.approval_type == 'purchase':
            self.write({
                'has_agreement_type': 'no',
                'has_vendor': 'no',
                'has_analytic_account': 'optional',
                'has_analytic_tag': 'optional',
                'has_quality_tag': 'optional',
            })
        elif self.approval_type == 'vendor_bill':
            self.write({
                'has_product': 'optional',
                'has_quantity': 'required',
                'has_vendor': 'optional',
                'has_bill_reference': 'optional',
                'has_price': 'optional',
                'has_account': 'required',
                'has_analytic_account': 'optional',
                'has_analytic_tag': 'optional',
            })
        else:
            self.write({
                'has_product': 'no',
                'has_quantity': 'no',
                'has_agreement_type': 'no',
                'has_vendor': 'no',
                'has_bill_reference': 'no',
                'has_price': 'no',
                'has_account': 'no',
                'has_analytic_account': 'no',
                'has_analytic_tag': 'no',
                'has_quality_tag': 'no',
            })
