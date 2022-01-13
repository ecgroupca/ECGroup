# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaProductionWizard(models.TransientModel):
    _name = "rma.production.wizard"
    _description = "RMA Production Wizard"

    rma_count = fields.Integer()
    product_id = fields.Many2one(
        comodel_name="product.product", string="Product to Repair",
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company",
    )
    mrp_bom_id = fields.Many2one(
        comodel_name="mrp.bom", string="BoM for repair"
    )
    product_uom_qty = fields.Float(
        string="Product qty", digits="Product Unit of Measure",
    )
    product_uom = fields.Many2one(comodel_name="uom.uom", string="Unit of measure")
    scheduled_date = fields.Datetime(required=True, default=fields.Datetime.now())
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse", string="Warehouse", required=True,
    )

    @api.constrains("product_uom_qty")
    def _check_product_uom_qty(self):
        self.ensure_one()
        rma_ids = self.env.context.get("active_ids")
        if len(rma_ids) == 1 and self.product_uom_qty <= 0:
            raise ValidationError(_("Quantity must be greater than 0."))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_ids = self.env.context.get("active_ids")
        rma = self.env["rma"].browse(rma_ids)
        warehouse_id = (
            self.env["stock.warehouse"]
            .search([("company_id", "=", rma[0].company_id.id)], limit=1)
            .id
        )
        delivery_type = self.env.context.get("rma_delivery_type")
        product_id = False
        mrp_bom_id = False
        if len(rma) == 1 and rma.product_id:
            product = rma.product_id
            product_id = product and product.id or False
            mrp_bom_id = (
                self.env['mrp.bom']
               .search([('product_tmpl_id','=',product.product_tmpl_id.id)], limit=1)
               .id
            )
        product_uom_qty = 0.0
        if len(rma) == 1 and rma.remaining_qty > 0.0:
            product_uom_qty = rma.remaining_qty
        res.update(
            rma_count=len(rma),
            warehouse_id=warehouse_id,
            product_id=product_id,
            product_uom_qty=product_uom_qty,
            mrp_bom_id=mrp_bom_id,
        )
        return res

    @api.onchange("product_id")
    def _onchange_product_id(self):
        domain_product_uom = []
        if self.product_id:
            domain_product_uom = [
                ("category_id", "=", self.product_id.uom_id.category_id.id)
            ]
            if not self.product_uom or self.product_id.uom_id.id != self.product_uom.id:
                self.product_uom = self.product_id.uom_id
        return {"domain": {"product_uom": domain_product_uom}}

    def action_repair(self):
        self.ensure_one()
        rma_ids = self.env.context.get("active_ids")
        rma = self.env["rma"].browse(rma_ids)
        rma.create_repair(
            self.scheduled_date,
            self.warehouse_id,
            self.product_id,
            self.product_uom_qty,
            self.product_uom,
            self.company_id,
        )