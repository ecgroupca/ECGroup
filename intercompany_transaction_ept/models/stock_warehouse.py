# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_intervalTypes = {
    "minutes": lambda interval: relativedelta(minutes=interval),
    "hours": lambda interval: relativedelta(hours=interval),
    "days": lambda interval: relativedelta(days=interval),
    "weeks": lambda interval: relativedelta(days=7 * interval),
    "months": lambda interval: relativedelta(months=interval)
}


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    auto_create_ict = fields.Boolean("Auto Generate Inter Company/Warehouse Transfer",
                                     help="This will enable a scheduled action to generate a Inter Company/Warehouse "
                                          "Transfer, when there is not enough stock to fulfil a Picking of the "
                                          "Warehouse.")
    ict_resupply_wh_id = fields.Many2one("stock.warehouse", "Auto Resupply From")
    ict_interval_number = fields.Integer(help="Interval Number to Check for Resupply", default=1)
    ict_interval_type = fields.Selection([("minutes", "Minutes"), ("hours", "Hours"),
                                          ("days", "Days"), ("weeks", "Weeks"),
                                          ("months", "Months")], help="Interval Unit", default="days")
    ict_user_id = fields.Many2one("res.users", string="User for Import Order",
                                  help="User for executing the Scheduled action and with Rights with ICT.")

    @api.constrains("ict_interval_number")
    def check_interval_time(self):
        """
        It does not let set the cron execution time to Zero.
        @author: Maulik Barad on Date 03-Dec-2020.
        """
        for record in self:
            if record.auto_create_ict and record.ict_interval_number <= 0:
                raise ValidationError(_("Cron Execution Time can't be set to 0(Zero). "))

    def write(self, vals):
        """
        This method is inherited for managing the auto create ict record cron.
        @author: Maulik Barad on Date 04-Jan-2021.
        """
        if vals.get("ict_resupply_wh_id"):
            resupply_warehouse = {"resupply_wh_ids": [[6, 0, [vals["ict_resupply_wh_id"]] + self.resupply_wh_ids.ids]]}
            if "resupply_wh_ids" in vals:
                vals["resupply_wh_ids"][0][2].append(vals["ict_resupply_wh_id"])
            else:
                vals.update(resupply_warehouse)
        if "auto_create_ict" in vals.keys() and not vals.get("auto_create_ict"):
            vals.update({"ict_resupply_wh_id": False, "ict_interval_number": 1,
                         "ict_interval_type": "", "ict_user_id": False})

        res = super(Warehouse, self).write(vals)

        for record in self:
            record.setup_auto_create_ict_cron()
        return res

    def setup_auto_create_ict_cron(self):
        """
        This method will be used to enable/disable the scheduled action of ICT.
        @author: Maulik Barad on Date 04-Jan-2021.
        """
        cron_exist = self.env.ref("intercompany_transaction_ept.ir_cron_auto_create_ict_warehouse_%d" % self.id, False)

        if self.auto_create_ict:
            vals = self.prepare_val_for_cron()

            if cron_exist:
                vals.update({"name": cron_exist.name})
                cron_exist.write(vals)
            else:
                core_cron = self.check_core_cron()

                name = self.name + " : " + core_cron.name
                vals.update({"name": name})
                new_cron = core_cron.copy(default=vals)
                name = "ir_cron_auto_create_ict_warehouse_%d" % self.id
                self.create_ir_module_data(name, new_cron)
        else:
            if cron_exist:
                cron_exist.write({"active": False})
        return True

    def prepare_val_for_cron(self):
        """
        This method is used to prepare dictionary for the cron configuration.
        @author: Maulik Barad on Date 04-Jan-2021.
        """
        nextcall = datetime.now() + _intervalTypes[self.ict_interval_type](self.ict_interval_number)
        vals = {"active": True,
                "interval_number": self.ict_interval_number,
                "interval_type": self.ict_interval_type,
                "user_id": self.ict_user_id.id,
                "nextcall": nextcall.strftime("%Y-%m-%d %H:%M:%S"),
                "code": "model.create_ict_for_unassigned_moves(%d)" % self.id}
        return vals

    def check_core_cron(self):
        """
        This method will check for the core cron and if doesn't exist, then raise error.
        @author: Maulik Barad.
        """
        core_cron = self.env.ref("intercompany_transaction_ept.ir_cron_auto_create_ict", False)

        if not core_cron:
            raise UserError(_("Core settings of ICT module is deleted, please upgrade Inter Company Transfer and "
                              "Warehouse module to get back this settings."))
        return core_cron

    def create_ir_module_data(self, name, new_cron):
        """
        This method is used to create a record of ir model data
        @author: Maulik Barad on Date 04-Jan-2021.
        """
        self.env["ir.model.data"].create({"module": "intercompany_transaction_ept",
                                          "name": name,
                                          "model": "ir.cron",
                                          "res_id": new_cron.id,
                                          "noupdate": True})

    def create_ict_for_unassigned_moves(self, warehouse_id):
        """
        This method will check for moves in waiting state and creates ICT records as per the configuration.
        @param warehouse_id: Id of the warehouse.
        @author: Maulik Barad on Date 04-Jan-2021.
        """
        if not warehouse_id:
            return True
        stock_move_obj = self.env["stock.move"]
        ict_obj = self.env["inter.company.transfer.ept"]
        log_line_obj = self.env["inter.company.transfer.log.line.ept"]

        warehouse = self.browse(warehouse_id)
        unassigned_moves = stock_move_obj.search([("warehouse_id", "=", warehouse_id), ("auto_ict_id", "=", False),
                                                  ("state", "in", ["confirmed", "partially_available"])])
        moves_to_assign = unassigned_moves.filtered(
            lambda x: not x.picking_id.inter_company_transfer_id and not x.picking_id.sale_id.inter_company_transfer_id)
        products = moves_to_assign.product_id

        ict_lines_list = []
        for product in products:
            moves = moves_to_assign.filtered(lambda x: x.product_id == product)
            qty = sum(moves.mapped("product_uom_qty")) - sum(moves.mapped("reserved_availability"))
            ict_lines_list.append([0, 0, {"product_id": product.id, "quantity": qty}])

        if ict_lines_list:
            source_warehouse = warehouse.ict_resupply_wh_id
            ict_type = "internal" if source_warehouse.company_id == warehouse.company_id else "ict"
            ict_vals = {"source_warehouse_id": source_warehouse.id, "destination_warehouse_id": warehouse_id,
                        "type": ict_type, "inter_company_transfer_line_ids": ict_lines_list}
            ict = ict_obj.with_context(default_type=ict_type).create(ict_vals)

            moves_to_assign.write({"auto_ict_id": ict.id})
            if not ict.auto_workflow_id:
                msg = "No Workflow is set as Default to process the Auto generated %s transfer." % ict_type
                log_line_obj.post_log_line(msg, ict, "auto")
                return False

            if ict_type == "ict":
                ict.onchange_destination_warehouse_id()
                ict.onchange_pricelist_id()
            ict.process_ict()
            moves_to_assign._action_assign()

            stock_not_available = False
            if ict_type == "ict" and ict.auto_workflow_id.auto_validate_delivery:
                if not all([picking.state == "done" for picking in ict.sale_order_ids.picking_ids]):
                    stock_not_available = True
            if ict_type == "ict" and ict.auto_workflow_id.validate_pickings:
                if not all([picking.state == "done" for picking in ict.picking_ids]):
                    stock_not_available = True
            if stock_not_available:
                msg = "Enough Stock is not available in Source Warehouse.\nCouldn't fulfill pickings."
                log_line_obj.post_log_line(msg, ict, "auto")

        return True
