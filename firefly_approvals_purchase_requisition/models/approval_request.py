# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    purchase_agreement_count = fields.Integer(compute='_compute_purchase_agreement_count')
    vendor_bill_count = fields.Integer(compute='_compute_vendor_bill_count')

    has_agreement_type = fields.Selection(related="category_id.has_agreement_type")
    has_vendor = fields.Selection(related="category_id.has_vendor")
    has_bill_reference = fields.Selection(related="category_id.has_bill_reference")
    has_price = fields.Selection(related="category_id.has_price")
    has_account = fields.Selection(related="category_id.has_account")
    has_analytic_account = fields.Selection(related="category_id.has_analytic_account")
    has_analytic_tag = fields.Selection(related="category_id.has_analytic_tag")
    has_quality_tag = fields.Selection(related="category_id.has_quality_tag")

    agreement_type_id = fields.Many2one('purchase.requisition.type')
    agreement_type_quantity_copy = fields.Selection(related='agreement_type_id.quantity_copy', readonly=True)
    vendor_id = fields.Many2one('res.partner', check_company=True)
    bill_reference = fields.Char('Bill Reference')
    quality_tag_ids = fields.Many2many('quality.tag.po', string="Quality Tags")

    @api.depends('product_line_ids.purchase_requisition_line_id')
    def _compute_purchase_agreement_count(self):
        for request in self:
            purchase_agreements = request.product_line_ids.purchase_requisition_line_id.requisition_id
            request.purchase_agreement_count = len(purchase_agreements)

    @api.depends('product_line_ids.account_move_line_id')
    def _compute_vendor_bill_count(self):
        for request in self:
            vendor_bills = request.product_line_ids.account_move_line_id.move_id
            request.vendor_bill_count = len(vendor_bills)

    def action_approve(self, approver=None):
        if self.approval_type == 'purchase_agreement' and any(not line.product_id for line in self.product_line_ids):
            raise UserError(_("You must select a product for each line of requested products."))
        return super().action_approve(approver)

    def action_cancel(self):
        """ Override to notify Purchase Agreements when the Approval Request is cancelled. """
        result = super().action_cancel()
        purchase_agreements = self.product_line_ids.purchase_requisition_line_id.requisition_id
        for purchase_agreement in purchase_agreements:
            product_lines = self.product_line_ids.filtered(
                lambda line: line.purchase_requisition_line_id.requisition_id.id == purchase_agreement.id
            )
            purchase_agreement._activity_schedule_with_view(
                'mail.mail_activity_data_warning',
                views_or_xmlid='firefly_approvals_purchase_requisition.exception_approval_request_canceled_for_purchase_agreement',
                user_id=self.env.user.id,
                render_context={
                    'approval_requests': self,
                    'product_lines': product_lines,
                }
            )
        return result

    def action_confirm(self):
        for request in self:
            if not request.product_line_ids:
                if request.approval_type == 'purchase_agreement':
                    raise UserError(_("You cannot create an empty purchase request."))
                elif request.approval_type == 'vendor_bill':
                    raise UserError(_("You cannot create an empty vendor bill request."))
        return super().action_confirm()

    def action_open_purchase_agreement(self):
        """ Return the form of purchase agreement the approval request created or affected in quantity. """
        self.ensure_one()
        purchase_agreement_id = self.product_line_ids.purchase_requisition_line_id.requisition_id.id
        return {
            'name': _('Purchase Agreement'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition',
            'res_id': purchase_agreement_id,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'current',
        }

    def action_create_purchase_agreement(self):
        """ Create a Purchase Agreement """
        self.ensure_one()
        new_purchase_agreement = self.env['purchase.requisition'].create({
            'name': 'New',
            'user_id': self.request_owner_id.id if self.request_owner_id else False,
            'type_id': self.agreement_type_id.id,
            'vendor_id': self.vendor_id.id if self.vendor_id else False,
            'state': 'draft',
            'origin': self.name,
        })
        for line in self.product_line_ids:
            new_purchase_agreement_line = self.env['purchase.requisition.line'].create({
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom_id.id if line.product_uom_id else False,
                'product_qty': line.quantity,
                'price_unit': line._get_seller_id().price,
                'account_analytic_id': line.account_analytic_id.id if line.account_analytic_id else False,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)] if line.analytic_tag_ids else False,
                'requisition_id': new_purchase_agreement.id,
            })
            new_purchase_agreement.line_ids = [(4, new_purchase_agreement_line.id)]
            line.purchase_requisition_line_id = new_purchase_agreement_line.id

    def action_create_purchase_orders(self):
        """ Overwrite the orginal function. Creating new line instead of merging line. """

        self.ensure_one()
        self.product_line_ids._check_products_vendor()

        for line in self.product_line_ids:
            seller = line._get_seller_id()
            vendor = seller.name
            po_domain = line._get_purchase_orders_domain(vendor)
            purchase_orders = self.env['purchase.order'].search(po_domain)

            if purchase_orders:
                purchase_order = purchase_orders[0]
                purchase_order.quality_tag_ids |= self.quality_tag_ids
                po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                    line.product_id,
                    line.quantity,
                    line.product_uom_id,
                    line.company_id,
                    seller,
                    purchase_order,
                )
                new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                line.purchase_order_line_id = new_po_line.id
                new_po_line.account_analytic_id = line.account_analytic_id.id if line.account_analytic_id else False
                purchase_order.order_line = [(4, new_po_line.id)]

                new_origin = set([self.name])
                if purchase_order.origin:
                    missing_origin = new_origin - set(purchase_order.origin.split(', '))
                    if missing_origin:
                        purchase_order.write({'origin': purchase_order.origin + ', ' + ', '.join(missing_origin)})
                else:
                    purchase_order.write({'origin': ', '.join(new_origin)})
            else:
                po_vals = line._get_purchase_order_values(vendor)
                new_purchase_order = self.env['purchase.order'].create(po_vals)
                new_purchase_order.quality_tag_ids = [(6, 0, self.quality_tag_ids.ids)] if self.quality_tag_ids else False
                po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                    line.product_id,
                    line.quantity,
                    line.product_uom_id,
                    line.company_id,
                    seller,
                    new_purchase_order,
                )
                new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                line.purchase_order_line_id = new_po_line.id
                new_po_line.account_analytic_id = line.account_analytic_id.id if line.account_analytic_id else False
                new_po_line.analytic_tag_ids = [(6, 0, line.analytic_tag_ids.ids)] if line.analytic_tag_ids else False
                new_purchase_order.order_line = [(4, new_po_line.id)]

    def action_open_vendor_bill(self):
        self.ensure_one()
        vendor_bill_id = self.product_line_ids.account_move_line_id.move_id.id
        context = self.env.context.copy()
        context.update({
            'default_move_journal_types': ['purchase'],
        })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': vendor_bill_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current',
        }

    def action_create_vendor_bill(self):
        """ Create a Vendor Bill """
        self.ensure_one()
        new_vendor_bill = self.env['account.move'].create({
            'name': '/',
            'move_type': 'in_invoice',
            'user_id': self.request_owner_id.id if self.request_owner_id else False,
            'partner_id': self.vendor_id.id if self.vendor_id else False,
            'ref': self.bill_reference if self.bill_reference else False,
            'state': 'draft',
        })        
        for line in self.product_line_ids:
            new_vendor_bill_line = self.env['account.move.line'].with_context({'check_move_validity': False}).create({
                'move_id': new_vendor_bill.id,
                'product_id': line.product_id.id,
                'name': line.description,
                'display_type': False,
                'account_id': line.account_id.id,
                'quantity': line.quantity,
                'product_uom_id': line.product_uom_id.id if line.product_uom_id else False,
                'price_unit': line.price_unit if line.price_unit else line._get_seller_id().price,
                'analytic_account_id': line.account_analytic_id.id if line.account_analytic_id else False,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)] if line.analytic_tag_ids else False,
            })
            new_vendor_bill.invoice_line_ids = [(4, new_vendor_bill_line.id)]
            line.account_move_line_id = new_vendor_bill_line.id
