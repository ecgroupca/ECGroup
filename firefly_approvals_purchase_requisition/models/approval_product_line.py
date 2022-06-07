# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    def _domain_product_id(self):
        """ Filters on product to get only the ones who are available on
        purchase in the case the approval request type is purchase. """
        if 'default_category_id' in self.env.context:
            category_id = self.env.context.get('default_category_id')
        elif self.env.context.get('active_model') == 'approval.category':
            category_id = self.env.context.get('active_id')
        else:
            return []
        category = self.env['approval.category'].browse(category_id)
        if category.approval_type in ['purchase', 'purchase_agreement']:
            return [('purchase_ok', '=', True)]

    purchase_requisition_line_id = fields.Many2one('purchase.requisition.line')
    account_move_line_id = fields.Many2one('account.move.line')
    product_id = fields.Many2one(domain=lambda self: self._domain_product_id())
    price_unit = fields.Float(string="Price")
    account_id = fields.Many2one('account.account', string="Account", check_company=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account", check_company=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string="Analytic Tags", check_company=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super()._onchange_product_id()

        if self.approval_request_id.approval_type in ['purchase', 'purchase_agreement', 'vendor_bill']:
            if self.product_id:
                self.description = self.product_id.display_name

            if self.approval_request_id.approval_type == 'vendor_bill':
                journal_expense_account = self.env['account.account'].search([
                    ('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)

                for line in self:
                    line.price_unit = line.product_id.standard_price
                    if not line.product_id:
                        line.account_id = journal_expense_account
                    else:
                        product_expense_account = line.product_id._get_product_accounts()['expense']
                        if product_expense_account:
                            line.account_id = product_expense_account
                        else:
                            line.account_id = journal_expense_account
