# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase, new_test_user, users
from odoo.tools import mute_logger

from .. import hooks


class TestRma(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.user_rma = new_test_user(
            cls.env,
            login="user_rma",
            groups="rma.rma_group_user_own,stock.group_stock_user",
        )
        cls.res_partner = cls.env["res.partner"]
        cls.product_product = cls.env["product.product"]
        cls.company = cls.env.user.company_id
        cls.warehouse_company = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.rma_loc = cls.warehouse_company.rma_loc_id
        cls.product = cls.product_product.create(
            {"name": "Product test 1", "type": "product"}
        )
        cls.account_receiv = cls.env["account.account"].create(
            {
                "name": "Receivable",
                "code": "RCV00",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        cls.partner = cls.res_partner.create(
            {
                "name": "Partner test",
                "property_account_receivable_id": cls.account_receiv.id,
                "property_payment_term_id": cls.env.ref(
                    "account.account_payment_term_30days"
                ).id,
            }
        )
        cls.partner_invoice = cls.res_partner.create(
            {
                "name": "Partner invoice test",
                "parent_id": cls.partner.id,
                "type": "invoice",
            }
        )
        cls.partner_shipping = cls.res_partner.create(
            {
                "name": "Partner shipping test",
                "parent_id": cls.partner.id,
                "type": "delivery",
            }
        )
        cls.finalization_reason_1 = cls.env["rma.finalization"].create(
            {"name": ("[Test] It can't be repaired and customer doesn't want it")}
        )
        cls.finalization_reason_2 = cls.env["rma.finalization"].create(
            {"name": "[Test] It's out of warranty. To be scrapped"}
        )
        cls.env.ref("rma.group_rma_manual_finalization").users |= cls.env.user
        cls.warehouse = cls.env.ref("stock.warehouse0")
        # Ensure grouping
        cls.env.company.rma_return_grouping = True

    def _create_rma(self, partner=None, product=None, qty=None, location=None):
        vals = {}
        if partner:
            vals["partner_id"] = partner.id
        if product:
            vals["product_id"] = product.id
        if qty:
            vals["product_uom_qty"] = qty
        if location:
            vals["location_id"] = location.id
        return self.env["rma"].create(vals)

    def _create_confirm_receive(
        self, partner=None, product=None, qty=None, location=None
    ):
        rma = self._create_rma(partner, product, qty, location)
        rma.action_confirm()
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id._action_done()
        return rma

    def _create_delivery(self):
        picking_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "outgoing"),
                "|",
                ("warehouse_id.company_id", "=", self.company.id),
                ("warehouse_id", "=", False),
            ],
            limit=1,
        )
        picking_form = Form(
            recordp=self.env["stock.picking"].with_context(
                default_picking_type_id=picking_type.id
            ),
            view="stock.view_picking_form",
        )
        picking_form.partner_id = self.partner
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product
            move.product_uom_qty = 10
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product_product.create(
                {"name": "Product 2 test", "type": "product"}
            )
            move.product_uom_qty = 20
        picking = picking_form.save()
        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        return picking


class TestRmaCase(TestRma):
    def test_post_init_hook(self):
        warehouse = self.env["stock.warehouse"].create(
            {
                "name": "Test warehouse",
                "code": "code",
                "company_id": self.env.company.id,
            }
        )
        hooks.post_init_hook(self.env.cr, self.registry)
        self.assertTrue(warehouse.rma_in_type_id)
        self.assertEqual(
            warehouse.rma_in_type_id.default_location_dest_id, warehouse.rma_loc_id
        )
        self.assertEqual(
            warehouse.rma_out_type_id.default_location_src_id, warehouse.rma_loc_id
        )
        self.assertTrue(warehouse.rma_loc_id)
        self.assertTrue(warehouse.rma_in_route_id)
        self.assertTrue(warehouse.rma_out_route_id)

    def test_rma_replace_pick_ship(self):
        self.warehouse.write({"delivery_steps": "pick_ship"})
        rma = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma.action_confirm()
        rma.reception_move_id.quantity_done = 1
        rma.reception_move_id.picking_id._action_done()
        self.assertEqual(rma.reception_move_id.picking_id.state, "done")
        self.assertEqual(rma.state, "received")
        res = rma.action_replace()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.product_id = self.product
        wizard_form.product_uom_qty = rma.product_uom_qty
        wizard = wizard_form.save()
        wizard.action_deliver()
        self.assertEqual(rma.delivery_picking_count, 2)
        out_pickings = rma.mapped("delivery_move_ids.picking_id")
        self.assertIn(
            self.warehouse.pick_type_id, out_pickings.mapped("picking_type_id")
        )
        self.assertIn(
            self.warehouse.out_type_id, out_pickings.mapped("picking_type_id")
        )

    def test_computed(self):
        # If partner changes, the invoice address is set
        rma = self.env["rma"].new()
        rma.partner_id = self.partner
        self.assertEqual(rma.partner_invoice_id, self.partner_invoice)
        # If origin move changes, the product is set
        uom_ten = self.env["uom.uom"].create(
            {
                "name": "Ten",
                "category_id": self.env.ref("uom.product_uom_unit").id,
                "factor_inv": 10,
                "uom_type": "bigger",
            }
        )
        product_2 = self.product_product.create(
            {"name": "Product test 2", "type": "product", "uom_id": uom_ten.id}
        )
        outgoing_picking_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "outgoing"),
                "|",
                ("warehouse_id.company_id", "=", self.company.id),
                ("warehouse_id", "=", False),
            ],
            limit=1,
        )
        picking_form = Form(
            recordp=self.env["stock.picking"].with_context(
                default_picking_type_id=outgoing_picking_type.id
            ),
            view="stock.view_picking_form",
        )
        picking_form.partner_id = self.partner
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = product_2
            move.product_uom_qty = 15
        picking = picking_form.save()
        picking._action_done()
        rma.picking_id = picking
        rma.move_id = picking.move_ids
        self.assertEqual(rma.product_id, product_2)
        self.assertEqual(rma.product_uom_qty, 15)
        self.assertEqual(rma.product_uom, uom_ten)
        # If product changes, unit of measure changes
        rma.move_id = False
        rma.product_id = self.product
        self.assertEqual(rma.product_uom, self.product.uom_id)

    def test_ensure_required_fields_on_confirm(self):
        rma = self._create_rma()
        with self.assertRaises(ValidationError) as e:
            rma.action_confirm()
        self.assertEqual(
            e.exception.args[0],
            "Required field(s):\nCustomer\nShipping Address\nInvoice Address\nProduct",
        )
        rma.partner_id = self.partner.id
        with self.assertRaises(ValidationError) as e:
            rma.action_confirm()
        self.assertEqual(e.exception.args[0], "Required field(s):\nProduct")
        rma.product_id = self.product.id
        rma.location_id = self.rma_loc.id
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")

    def test_confirm_and_receive(self):
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.reception_move_id.picking_id.state, "assigned")
        self.assertEqual(rma.reception_move_id.product_id, rma.product_id)
        self.assertEqual(rma.reception_move_id.product_uom_qty, 10)
        self.assertEqual(rma.reception_move_id.product_uom, rma.product_uom)
        self.assertEqual(rma.state, "confirmed")
        rma.reception_move_id.quantity_done = 9
        with self.assertRaises(ValidationError):
            rma.reception_move_id.picking_id._action_done()
        rma.reception_move_id.quantity_done = 10
        rma.reception_move_id.picking_id._action_done()
        self.assertEqual(rma.reception_move_id.picking_id.state, "done")
        self.assertEqual(rma.reception_move_id.quantity_done, 10)
        self.assertEqual(rma.state, "received")

    def test_cancel(self):
        # cancel a draft RMA
        rma = self._create_rma(self.partner, self.product)
        rma.action_cancel()
        self.assertEqual(rma.state, "cancelled")
        # cancel a confirmed RMA
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        rma.action_cancel()
        self.assertEqual(rma.state, "cancelled")
        # A RMA is only cancelled from draft and confirmed states
        rma = self._create_confirm_receive(self.partner, self.product, 10, self.rma_loc)
        with self.assertRaises(UserError):
            rma.action_cancel()

    def test_lock_unlock(self):
        # A RMA is only locked from 'received' state
        rma_1 = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma_2 = self._create_confirm_receive(
            self.partner, self.product, 10, self.rma_loc
        )
        self.assertEqual(rma_1.state, "draft")
        self.assertEqual(rma_2.state, "received")
        (rma_1 | rma_2).action_lock()
        self.assertEqual(rma_1.state, "draft")
        self.assertEqual(rma_2.state, "locked")
        # A RMA is only unlocked from 'lock' state and it will be set
        # to 'received' state
        (rma_1 | rma_2).action_unlock()
        self.assertEqual(rma_1.state, "draft")
        self.assertEqual(rma_2.state, "received")

    @users("__system__", "user_rma")
    def test_action_refund(self):
        rma = self._create_confirm_receive(self.partner, self.product, 10, self.rma_loc)
        self.assertEqual(rma.state, "received")
        self.assertTrue(rma.can_be_refunded)
        self.assertTrue(rma.can_be_returned)
        self.assertTrue(rma.can_be_replaced)
        rma.action_refund()
        self.assertEqual(rma.refund_id.move_type, "out_refund")
        self.assertEqual(rma.refund_id.state, "draft")
        self.assertFalse(rma.refund_id.invoice_payment_term_id)
        self.assertEqual(rma.refund_line_id.product_id, rma.product_id)
        self.assertEqual(rma.refund_line_id.quantity, 10)
        self.assertEqual(rma.refund_line_id.product_uom_id, rma.product_uom)
        self.assertEqual(rma.state, "refunded")
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        # A regular user can create the refund but only Invoicing users will be able
        # to edit it and post it
        if self.env.user.login != "__system__":
            return
        with Form(rma.refund_line_id.move_id) as refund_form:
            with refund_form.invoice_line_ids.edit(0) as refund_line:
                refund_line.quantity = 9
        with self.assertRaises(ValidationError):
            rma.refund_id.action_post()
        with Form(rma.refund_line_id.move_id) as refund_form:
            with refund_form.invoice_line_ids.edit(0) as refund_line:
                refund_line.quantity = 10
        rma.refund_id.action_post()
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)

    def test_mass_refund(self):
        # Create, confirm and receive rma_1
        rma_1 = self._create_confirm_receive(
            self.partner, self.product, 10, self.rma_loc
        )
        # create, confirm and receive 3 more RMAs
        # rma_2: Same partner and same product as rma_1
        rma_2 = self._create_confirm_receive(
            self.partner, self.product, 15, self.rma_loc
        )
        # rma_3: Same partner and different product than rma_1
        product = self.product_product.create(
            {"name": "Product 2 test", "type": "product"}
        )
        rma_3 = self._create_confirm_receive(self.partner, product, 20, self.rma_loc)
        # rma_4: Different partner and same product as rma_1
        partner = self.res_partner.create(
            {
                "name": "Partner 2 test",
                "property_account_receivable_id": self.account_receiv.id,
                "company_id": self.company.id,
            }
        )
        rma_4 = self._create_confirm_receive(partner, product, 25, self.rma_loc)
        # all rmas are ready to refund
        all_rmas = rma_1 | rma_2 | rma_3 | rma_4
        self.assertEqual(all_rmas.mapped("state"), ["received"] * 4)
        self.assertEqual(all_rmas.mapped("can_be_refunded"), [True] * 4)
        # Mass refund of those four RMAs
        action = self.env.ref("rma.rma_refund_action_server")
        ctx = dict(self.env.context)
        ctx.update(active_ids=all_rmas.ids, active_model="rma")
        action.with_context(**ctx).run()
        # After that all RMAs are in 'refunded' state
        self.assertEqual(all_rmas.mapped("state"), ["refunded"] * 4)
        # Two refunds were created
        refund_1 = (rma_1 | rma_2 | rma_3).mapped("refund_id")
        refund_2 = rma_4.refund_id
        self.assertEqual(len(refund_1), 1)
        self.assertEqual(len(refund_2), 1)
        self.assertEqual((refund_1 | refund_2).mapped("state"), ["draft"] * 2)
        # One refund per partner
        self.assertNotEqual(refund_1.partner_id, refund_2.partner_id)
        self.assertEqual(
            refund_1.partner_id,
            (rma_1 | rma_2 | rma_3).mapped("partner_invoice_id"),
        )
        self.assertEqual(refund_2.partner_id, rma_4.partner_invoice_id)
        # Each RMA (rma_1, rma_2 and rma_3) is linked with a different
        # line of refund_1
        self.assertEqual(len(refund_1.invoice_line_ids), 3)
        self.assertEqual(
            refund_1.invoice_line_ids.rma_id,
            (rma_1 | rma_2 | rma_3),
        )
        self.assertEqual(
            (rma_1 | rma_2 | rma_3).mapped("refund_line_id"),
            refund_1.invoice_line_ids,
        )
        # rma_4 is linked with the unique line of refund_2
        self.assertEqual(len(refund_2.invoice_line_ids), 1)
        self.assertEqual(refund_2.invoice_line_ids.rma_id, rma_4)
        self.assertEqual(rma_4.refund_line_id, refund_2.invoice_line_ids)
        # Assert product and quantities are propagated correctly
        for rma in all_rmas:
            self.assertEqual(rma.product_id, rma.refund_line_id.product_id)
            self.assertEqual(rma.product_uom_qty, rma.refund_line_id.quantity)
            self.assertEqual(rma.product_uom, rma.refund_line_id.product_uom_id)
        # Less quantity -> error on confirm
        with Form(rma_2.refund_line_id.move_id) as refund_form:
            with refund_form.invoice_line_ids.edit(1) as refund_line:
                refund_line.quantity = 14
        with self.assertRaises(ValidationError):
            refund_1.action_post()
        with Form(rma_2.refund_line_id.move_id) as refund_form:
            with refund_form.invoice_line_ids.edit(1) as refund_line:
                refund_line.quantity = 15
        refund_1.action_post()
        refund_2.action_post()

    def test_replace(self):
        # Create, confirm and receive an RMA
        rma = self._create_confirm_receive(self.partner, self.product, 10, self.rma_loc)
        # Replace with another product with quantity 2.
        product_2 = self.product_product.create(
            {"name": "Product 2 test", "type": "product"}
        )
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="replace",
            )
        )
        delivery_form.product_id = product_2
        delivery_form.product_uom_qty = 2
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        self.assertEqual(len(rma.delivery_move_ids.picking_id.move_ids), 1)
        self.assertEqual(rma.delivery_move_ids.product_id, product_2)
        self.assertEqual(rma.delivery_move_ids.product_uom_qty, 2)
        self.assertTrue(rma.delivery_move_ids.picking_id.state, "waiting")
        self.assertEqual(rma.state, "waiting_replacement")
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertTrue(rma.can_be_replaced)
        self.assertEqual(rma.delivered_qty, 2)
        self.assertEqual(rma.remaining_qty, 8)
        self.assertEqual(rma.delivered_qty_done, 0)
        self.assertEqual(rma.remaining_qty_to_done, 10)
        first_move = rma.delivery_move_ids
        picking = first_move.picking_id
        # Replace again with another product with the remaining quantity
        product_3 = self.product_product.create(
            {"name": "Product 3 test", "type": "product"}
        )
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="replace",
            )
        )
        delivery_form.product_id = product_3
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        second_move = rma.delivery_move_ids - first_move
        self.assertEqual(len(rma.delivery_move_ids), 2)
        self.assertEqual(rma.delivery_move_ids.mapped("picking_id"), picking)
        self.assertEqual(first_move.product_id, product_2)
        self.assertEqual(first_move.product_uom_qty, 2)
        self.assertEqual(second_move.product_id, product_3)
        self.assertEqual(second_move.product_uom_qty, 8)
        self.assertTrue(picking.state, "waiting")
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 0)
        self.assertEqual(rma.remaining_qty_to_done, 10)
        # remaining_qty is 0 but rma is not set to 'replaced' until
        # remaining_qty_to_done is less than or equal to 0
        first_move.quantity_done = 2
        second_move.quantity_done = 8
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 10)
        self.assertEqual(rma.remaining_qty_to_done, 0)
        # The RMA is now in 'replaced' state
        self.assertEqual(rma.state, "replaced")
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        # Despite being in 'replaced' state,
        # RMAs can still perform replacements.
        self.assertTrue(rma.can_be_replaced)

    def test_return_to_customer(self):
        # Create, confirm and receive an RMA
        rma = self._create_confirm_receive(self.partner, self.product, 10, self.rma_loc)
        # Return the same product with quantity 2 to the customer.
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="return",
            )
        )
        delivery_form.product_uom_qty = 2
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        picking = rma.delivery_move_ids.picking_id
        self.assertEqual(len(picking.move_ids), 1)
        self.assertEqual(rma.delivery_move_ids.product_id, self.product)
        self.assertEqual(rma.delivery_move_ids.product_uom_qty, 2)
        self.assertTrue(picking.state, "waiting")
        self.assertEqual(rma.state, "waiting_return")
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_replaced)
        self.assertTrue(rma.can_be_returned)
        self.assertEqual(rma.delivered_qty, 2)
        self.assertEqual(rma.remaining_qty, 8)
        self.assertEqual(rma.delivered_qty_done, 0)
        self.assertEqual(rma.remaining_qty_to_done, 10)
        first_move = rma.delivery_move_ids
        picking = first_move.picking_id
        # Validate the picking
        first_move.quantity_done = 2
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(rma.delivered_qty, 2)
        self.assertEqual(rma.remaining_qty, 8)
        self.assertEqual(rma.delivered_qty_done, 2)
        self.assertEqual(rma.remaining_qty_to_done, 8)
        # Return the remaining quantity to the customer
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="return",
            )
        )
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        second_move = rma.delivery_move_ids - first_move
        second_move.quantity_done = 8
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 2)
        self.assertEqual(rma.remaining_qty_to_done, 8)
        self.assertEqual(rma.state, "waiting_return")
        # remaining_qty is 0 but rma is not set to 'returned' until
        # remaining_qty_to_done is less than or equal to 0
        picking_2 = second_move.picking_id
        picking_2.button_validate()
        self.assertEqual(picking_2.state, "done")
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 10)
        self.assertEqual(rma.remaining_qty_to_done, 0)
        # The RMA is now in 'returned' state
        self.assertEqual(rma.state, "returned")
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)

    def test_finish_rma(self):
        # Create, confirm and receive an RMA
        rma = self._create_confirm_receive(self.partner, self.product, 10, self.rma_loc)
        rma.action_finish()
        finalization_form = Form(
            self.env["rma.finalization.wizard"].with_context(
                active_ids=rma.ids,
                rma_finalization_type="replace",
            )
        )
        finalization_form.finalization_id = self.finalization_reason_2
        finalization_wizard = finalization_form.save()
        finalization_wizard.action_finish()
        self.assertEqual(rma.state, "finished")
        self.assertEqual(rma.finalization_id, self.finalization_reason_2)

    def test_mass_return_to_customer(self):
        # Create, confirm and receive rma_1
        rma_1 = self._create_confirm_receive(
            self.partner, self.product, 10, self.rma_loc
        )
        # create, confirm and receive 3 more RMAs
        # rma_2: Same partner and same product as rma_1
        rma_2 = self._create_confirm_receive(
            self.partner, self.product, 15, self.rma_loc
        )
        # rma_3: Same partner and different product than rma_1
        product = self.product_product.create(
            {"name": "Product 2 test", "type": "product"}
        )
        rma_3 = self._create_confirm_receive(self.partner, product, 20, self.rma_loc)
        # rma_4: Different partner and same product as rma_1
        partner = self.res_partner.create({"name": "Partner 2 test"})
        rma_4 = self._create_confirm_receive(partner, product, 25, self.rma_loc)
        # all rmas are ready to be returned to the customer
        all_rmas = rma_1 | rma_2 | rma_3 | rma_4
        self.assertEqual(all_rmas.mapped("state"), ["received"] * 4)
        self.assertEqual(all_rmas.mapped("can_be_returned"), [True] * 4)
        all_in_pickings = all_rmas.mapped("reception_move_id.picking_id")
        self.assertEqual(
            all_in_pickings.mapped("picking_type_id"), self.warehouse.rma_in_type_id
        )
        self.assertEqual(
            all_in_pickings.mapped("location_dest_id"), self.warehouse.rma_loc_id
        )
        # Mass return of those four RMAs
        delivery_wizard = (
            self.env["rma.delivery.wizard"]
            .with_context(active_ids=all_rmas.ids, rma_delivery_type="return")
            .create({})
        )
        delivery_wizard.action_deliver()
        # Two pickings were created
        pick_1 = (rma_1 | rma_2 | rma_3).mapped("delivery_move_ids.picking_id")
        pick_2 = rma_4.delivery_move_ids.picking_id
        self.assertEqual(pick_1.picking_type_id, self.warehouse.rma_out_type_id)
        self.assertEqual(pick_1.location_id, self.warehouse.rma_loc_id)
        self.assertEqual(pick_2.picking_type_id, self.warehouse.rma_out_type_id)
        self.assertEqual(pick_2.location_id, self.warehouse.rma_loc_id)
        self.assertEqual(len(pick_1), 1)
        self.assertEqual(len(pick_2), 1)
        self.assertNotEqual(pick_1, pick_2)
        self.assertEqual((pick_1 | pick_2).mapped("state"), ["assigned"] * 2)
        # One picking per partner
        self.assertNotEqual(pick_1.partner_id, pick_2.partner_id)
        self.assertEqual(
            pick_1.partner_id,
            (rma_1 | rma_2 | rma_3).mapped("partner_shipping_id"),
        )
        self.assertEqual(pick_2.partner_id, rma_4.partner_id)
        # Each RMA of (rma_1, rma_2 and rma_3) is linked to a different
        # line of picking_1
        self.assertEqual(len(pick_1.move_ids), 3)
        self.assertEqual(
            pick_1.move_ids.rma_id,
            (rma_1 | rma_2 | rma_3),
        )
        self.assertEqual(
            (rma_1 | rma_2 | rma_3).mapped("delivery_move_ids"),
            pick_1.move_ids,
        )
        # rma_4 is linked with the unique move of pick_2
        self.assertEqual(len(pick_2.move_ids), 1)
        self.assertEqual(pick_2.move_ids.rma_id, rma_4)
        self.assertEqual(rma_4.delivery_move_ids, pick_2.move_ids)
        # Assert product and quantities are propagated correctly
        for rma in all_rmas:
            self.assertEqual(rma.product_id, rma.delivery_move_ids.product_id)
            self.assertEqual(rma.product_uom_qty, rma.delivery_move_ids.product_uom_qty)
            self.assertEqual(rma.product_uom, rma.delivery_move_ids.product_uom)
            rma.delivery_move_ids.quantity_done = rma.product_uom_qty
        pick_1.button_validate()
        pick_2.button_validate()
        self.assertEqual(all_rmas.mapped("state"), ["returned"] * 4)

    def test_mass_return_to_customer_ungrouped(self):
        """We can choose to avoid the customer returns grouping"""
        self.env.company.rma_return_grouping = False
        # Create, confirm and receive rma_1
        rma_1 = self._create_confirm_receive(
            self.partner, self.product, 10, self.rma_loc
        )
        # create, confirm and receive 3 more RMAs
        # rma_2: Same partner and same product as rma_1
        rma_2 = self._create_confirm_receive(
            self.partner, self.product, 15, self.rma_loc
        )
        # rma_3: Same partner and different product than rma_1
        product = self.product_product.create(
            {"name": "Product 2 test", "type": "product"}
        )
        rma_3 = self._create_confirm_receive(self.partner, product, 20, self.rma_loc)
        # rma_4: Different partner and same product as rma_1
        partner = self.res_partner.create({"name": "Partner 2 test"})
        rma_4 = self._create_confirm_receive(partner, product, 25, self.rma_loc)
        # all rmas are ready to be returned to the customer
        all_rmas = rma_1 | rma_2 | rma_3 | rma_4
        self.assertEqual(all_rmas.mapped("state"), ["received"] * 4)
        self.assertEqual(all_rmas.mapped("can_be_returned"), [True] * 4)
        # Mass return of those four RMAs
        delivery_wizard = (
            self.env["rma.delivery.wizard"]
            .with_context(active_ids=all_rmas.ids, rma_delivery_type="return")
            .create({})
        )
        delivery_wizard.action_deliver()
        self.assertEqual(4, len(all_rmas.delivery_move_ids.picking_id))

    def test_rma_from_picking_return(self):
        # Create a return from a delivery picking
        origin_delivery = self._create_delivery()
        stock_return_picking_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=origin_delivery.ids,
                active_id=origin_delivery.id,
                active_model="stock.picking",
            )
        )
        stock_return_picking_form.create_rma = True
        return_wizard = stock_return_picking_form.save()
        picking_action = return_wizard.create_returns()
        # Each origin move is linked to a different RMA
        origin_moves = origin_delivery.move_ids
        self.assertTrue(origin_moves[0].rma_ids)
        self.assertTrue(origin_moves[1].rma_ids)
        rmas = origin_moves.rma_ids
        self.assertEqual(rmas.mapped("state"), ["confirmed"] * 2)
        # Each reception move is linked one of the generated RMAs
        reception = self.env["stock.picking"].browse(picking_action["res_id"])
        reception_moves = reception.move_ids
        self.assertTrue(reception_moves[0].rma_receiver_ids)
        self.assertTrue(reception_moves[1].rma_receiver_ids)
        self.assertEqual(reception_moves.rma_receiver_ids, rmas)
        # Validate the reception picking to set rmas to 'received' state
        reception_moves[0].quantity_done = reception_moves[0].product_uom_qty
        reception_moves[1].quantity_done = reception_moves[1].product_uom_qty
        reception.button_validate()
        self.assertEqual(rmas.mapped("state"), ["received"] * 2)

    def test_split(self):
        origin_delivery = self._create_delivery()
        rma_form = Form(self.env["rma"])
        rma_form.partner_id = self.partner
        rma_form.picking_id = origin_delivery
        rma_form.move_id = origin_delivery.move_ids.filtered(
            lambda r: r.product_id == self.product
        )
        rma = rma_form.save()
        rma.action_confirm()
        rma.reception_move_id.quantity_done = 10
        rma.reception_move_id.picking_id._action_done()
        # Return quantity 4 of the same product to the customer
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="return",
            )
        )
        delivery_form.product_uom_qty = 4
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        rma.delivery_move_ids.quantity_done = 4
        rma.delivery_move_ids.picking_id.button_validate()
        self.assertEqual(rma.state, "waiting_return")
        # Extract the remaining quantity to another RMA
        self.assertTrue(rma.can_be_split)
        split_wizard = (
            self.env["rma.split.wizard"]
            .with_context(
                active_id=rma.id,
                active_ids=rma.ids,
            )
            .create({})
        )
        action = split_wizard.action_split()
        # Check rma is set to 'returned' after split. Check new_rma values
        self.assertEqual(rma.state, "returned")
        new_rma = self.env["rma"].browse(action["res_id"])
        self.assertEqual(new_rma.origin_split_rma_id, rma)
        self.assertEqual(new_rma.delivered_qty, 0)
        self.assertEqual(new_rma.remaining_qty, 6)
        self.assertEqual(new_rma.delivered_qty_done, 0)
        self.assertEqual(new_rma.remaining_qty_to_done, 6)
        self.assertEqual(new_rma.state, "received")
        self.assertTrue(new_rma.can_be_refunded)
        self.assertTrue(new_rma.can_be_returned)
        self.assertTrue(new_rma.can_be_replaced)
        self.assertEqual(new_rma.move_id, rma.move_id)
        self.assertEqual(new_rma.reception_move_id, rma.reception_move_id)
        self.assertEqual(new_rma.product_uom_qty + rma.product_uom_qty, 10)
        self.assertEqual(new_rma.move_id.quantity_done, 10)
        self.assertEqual(new_rma.reception_move_id.quantity_done, 10)

    @mute_logger("odoo.models.unlink")
    def test_rma_to_receive_on_delete_invoice(self):
        rma = self._create_confirm_receive(self.partner, self.product, 10, self.rma_loc)
        rma.action_refund()
        self.assertEqual(rma.state, "refunded")
        rma.refund_id.unlink()
        self.assertFalse(rma.refund_id)
        self.assertEqual(rma.state, "received")
        self.assertTrue(rma.can_be_refunded)
        self.assertTrue(rma.can_be_returned)
        self.assertTrue(rma.can_be_replaced)

    def test_rma_picking_type_default_values(self):
        warehouse = self.env["stock.warehouse"].create(
            {"name": "Stock - RMA Test", "code": "SRT"}
        )
        self.assertFalse(warehouse.rma_in_type_id.use_create_lots)
        self.assertTrue(warehouse.rma_in_type_id.use_existing_lots)

    def test_quantities_on_hand(self):
        rma = self._create_confirm_receive(self.partner, self.product, 10, self.rma_loc)
        self.assertEqual(rma.product_id.qty_available, 0)

    def test_autoconfirm_email(self):
        self.company.send_rma_confirmation = True
        self.company.send_rma_receipt_confirmation = True
        self.company.send_rma_draft_confirmation = True
        self.company.rma_mail_confirmation_template_id = self.env.ref(
            "rma.mail_template_rma_notification"
        )
        self.company.rma_mail_receipt_confirmation_template_id = self.env.ref(
            "rma.mail_template_rma_receipt_notification"
        )
        self.company.rma_mail_draft_confirmation_template_id = self.env.ref(
            "rma.mail_template_rma_draft_notification"
        )
        previous_mails = self.env["mail.mail"].search(
            [("partner_ids", "in", self.partner.ids)]
        )
        self.assertFalse(previous_mails)
        # Force the context to mock an RMA created from the portal, which is
        # feature that we get on `rma_sale`. We drop it after the RMA creation
        # to avoid uncontrolled side effects
        ctx = self.env.context
        self.env.context = dict(ctx, from_portal=True)
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        self.env.context = ctx
        mail_draft = self.env["mail.message"].search(
            [("partner_ids", "in", self.partner.ids)]
        )
        rma.action_confirm()
        mail_confirm = (
            self.env["mail.message"].search([("partner_ids", "in", self.partner.ids)])
            - mail_draft
        )
        self.assertTrue(rma.name in mail_confirm.subject)
        self.assertTrue(rma.name in mail_confirm.body)
        self.assertEqual(
            self.env.ref("rma.mt_rma_notification"), mail_confirm.subtype_id
        )
        # Now we'll confirm the incoming goods picking and the automatic
        # reception notification should be sent
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id.button_validate()
        mail_receipt = (
            self.env["mail.message"].search([("partner_ids", "in", self.partner.ids)])
            - mail_draft
            - mail_confirm
        )
        self.assertTrue(rma.name in mail_receipt.subject)
        self.assertTrue("products received" in mail_receipt.subject)
