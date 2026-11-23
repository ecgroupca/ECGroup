# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockInventoryXlsxBatch(models.Model):
    """One record per uploaded XLSX file: keeps the file, who uploaded it and the
    draft inventory count lines (stock.quant) that the upload created."""
    _name = 'stock.inventory.xlsx.batch'
    _description = 'Inventory Adjustment XLSX Import'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    file_name = fields.Char(string='File Name', readonly=True)
    file = fields.Binary(string='XLSX File', readonly=True, attachment=True)
    date = fields.Datetime(string='Uploaded On', default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='Uploaded By', readonly=True,
                              default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company)
    quant_ids = fields.Many2many(
        'stock.quant', 'stock_inventory_xlsx_batch_quant_rel', 'batch_id', 'quant_id',
        string='Counted Lines', readonly=True)
    line_count = fields.Integer(string='Lines', readonly=True,
                                help="Number of count lines created by the upload.")
    pending_count = fields.Integer(string='Not Applied', compute='_compute_state',
                                   help="Count lines that still wait to be applied to stock.")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             string='Status', compute='_compute_state')

    @api.depends('quant_ids.inventory_quantity_set')
    def _compute_state(self):
        for batch in self:
            pending = len(batch.quant_ids.filtered('inventory_quantity_set'))
            batch.pending_count = pending
            batch.state = 'draft' if pending else 'done'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'stock.inventory.xlsx.batch') or _('New')
        return super().create(vals_list)

    def action_open_lines(self):
        """Open this upload's count lines in a list with a check box on every line and an
        "Apply Selected" button, so all or only some of the lines can be applied."""
        self.ensure_one()
        view = self.env.ref('stock_inventory_xlsx_import.stock_quant_xlsx_line_view_tree')
        search_view = self.env.ref('stock_inventory_xlsx_import.stock_quant_xlsx_line_view_search')
        return {
            'type': 'ir.actions.act_window',
            'name': _("Imported Lines %s") % self.name,
            'res_model': 'stock.quant',
            'view_mode': 'tree',
            'views': [(view.id, 'tree')],
            'search_view_id': [search_view.id, search_view.name],
            'domain': [('id', 'in', self.quant_ids.ids)],
            'context': {'search_default_pending': 1, 'create': False, 'delete': False},
        }

    @api.model
    def action_apply_quants(self, quant_ids):
        """Apply the selected count lines to stock (same as the Apply button of Physical
        Inventory). Only lines that belong to an import and still wait to be applied are
        used; the rest are skipped. Runs with the rights of the current user.

        Returns an action when Odoo needs a confirmation wizard (outdated count, tracked
        product without lot), otherwise {'applied': n, 'skipped': m}."""
        quants = self.env['stock.quant'].browse(quant_ids).exists()
        quants &= self.search([('quant_ids', 'in', quants.ids)]).quant_ids
        pending = quants.filtered('inventory_quantity_set')
        if not pending:
            raise UserError(_("The selected lines are already applied, so there is nothing to apply."))
        result = pending.with_context(inventory_mode=True).action_apply_inventory()
        if isinstance(result, dict):
            return result
        return {'applied': len(pending), 'skipped': len(quant_ids) - len(pending)}

    def action_open_draft_adjustment(self):
        """Open this upload's count lines in the Physical Inventory screen,
        where they can be reviewed, edited and applied."""
        self.ensure_one()
        action = self.env['stock.quant'].action_view_inventory()
        action.update({
            'name': _("Draft Inventory Adjustment %s") % self.name,
            'domain': [('id', 'in', self.quant_ids.ids)],
        })
        return action

    @api.model
    def _place_menu(self):
        """Put the import menu directly above the Physical Inventory / Inventory
        Adjustments menu, wherever that one lives. Called from the module's data
        file on install and on every upgrade; does nothing if it cannot find it."""
        menu = self.env.ref('stock_inventory_xlsx_import.stock_inventory_xlsx_import_menu',
                            raise_if_not_found=False)
        if not menu:
            return
        Menu = self.env['ir.ui.menu']
        target = self.env.ref('stock.menu_action_inventory_tree', raise_if_not_found=False)
        if not target:
            for label in ('Inventory Adjustments', 'Physical Inventory'):
                target = Menu.search([('name', 'ilike', label), ('id', '!=', menu.id),
                                      ('action', '!=', False)], limit=1)
                if target:
                    break
        if target:
            # The menu must stay visible to every Inventory user. If the parent of the
            # target menu is restricted to groups an Inventory user is not in (e.g.
            # Managers only), use the Operations menu instead of hiding the import.
            parent = target.parent_id
            user_group = self.env.ref('stock.group_stock_user')
            reachable_groups = user_group | user_group.trans_implied_ids
            if not parent or (parent.groups_id and not (parent.groups_id & reachable_groups)):
                parent = self.env.ref('stock.menu_stock_warehouse_mgmt')
            menu.write({
                'parent_id': parent.id,
                'sequence': max(target.sequence - 1, 0),
            })
