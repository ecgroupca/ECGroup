# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import api, fields, models, _


class MrpProduction(models.TransientModel):
    _name = "mrp.production.cancel.wizard"
    _description = "Showing wizard to cancel manufacturing order"

    reason = fields.Many2one('production.cancel.reason', 'Reason')
    comment = fields.Text('Comment')

    def cancel_order_button(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        productions = self.env['mrp.production'].browse(active_ids)
        productions._action_cancel_approve(self.reason, self.comment)
