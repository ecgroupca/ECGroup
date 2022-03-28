"""
For inter_company_transfer_ept module.
"""
from datetime import datetime
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning


class InterCompanyTransferEpt(models.Model):
    """
    For managing the Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad on Date 24-Sep-2019.
    """
    _name = 'inter.company.transfer.ept'
    _description = "Inter Company Transfer EPT"
    _order = 'id desc'
    _inherit = ['barcodes.barcode_events_mixin']

    name = fields.Char(help="Name of Inter company transfer.")

    source_warehouse_id = fields.Many2one('stock.warehouse', string='From Warehouse',
                                          help="Source warehouse to transfer stock from.")
    source_company_id = fields.Many2one(related='source_warehouse_id.company_id',
                                        string="From Company", store=True,
                                        help="Company of Source warehouse.")
    destination_warehouse_id = fields.Many2one('stock.warehouse', string='To Warehouse',
                                               help="Destination warehouse to transfer stock to.")
    destination_company_id = fields.Many2one(related='destination_warehouse_id.company_id',
                                             string="To Company", store=True,
                                             help="Company of Destination warehouse.")

    inter_company_transfer_line_ids = fields.One2many('inter.company.transfer.line.ept',
                                                      'inter_company_transfer_id',
                                                      string="Transfer Lines",
                                                      help="ICT Lines", copy=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('processed','Awaiting Transfer'),
                              ('transferred', 'Transferred'),
                              ('cancel', 'Cancelled')],
                             string='State', copy=False, default='draft', help="State of ICT.")
    type = fields.Selection([('ict', 'ICT'), ('ict_reverse', 'Reverse ICT'),
                             ('internal', 'Internal')], copy=False, default='ict',
                            help="The type of transfer.")

    log_ids = fields.One2many('inter.company.transfer.log.book.ept', 'inter_company_transfer_id',
                              string="Inter Company Log", help="Logs of ICT.")
    log_count = fields.Integer(compute='_compute_log_ids', help="Count of Logs.")
    message = fields.Char("Message", copy=False, help="Message for ICT.")
    processed_date = fields.Datetime("Processed Date", copy=False,
                                     help="Date when ICT is processed.")

    crm_team_id = fields.Many2one('crm.team', string="Sales Team",
                                  default=lambda self: self.env['crm.team']._get_default_team_id(),
                                  help="Sales team")
    pricelist_id = fields.Many2one('product.pricelist', help="Pricelist for prices of Products.")
    currency_id = fields.Many2one(related="pricelist_id.currency_id",
                                  help="Currency of company or by pricelist.")
    group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)

    inter_company_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT",
                                                copy=False)
    reverse_inter_company_transfer_ids = fields.One2many('inter.company.transfer.ept',
                                                         'inter_company_transfer_id',
                                                         string="Reverse ICT", copy=False,
                                                         help="Reverse ICTs generated from "
                                                         "current ICT.")

    sale_order_ids = fields.One2many('sale.order', 'inter_company_transfer_id', copy=False,
                                     help="Sale orders created by the ICT.")
    purchase_order_ids = fields.One2many('purchase.order', 'inter_company_transfer_id', copy=False,
                                         help="Purchase orders created by the ICT.")
    picking_ids = fields.One2many('stock.picking', 'inter_company_transfer_id', copy=False,
                                  help="Pickings created by the ICT.")
    invoice_ids = fields.One2many('account.move', 'inter_company_transfer_id', copy=False,
                                  help="Invoices and Vendor bills created by the ICT.")
                                  
    shipper_id = fields.Many2one('res.partner', string='Shipper')

    _sql_constraints = [('source_destination_warehouse_uniq',
                         'CHECK(source_warehouse_id != destination_warehouse_id)',
                         'Source and Destination warehouse must be different!')]

    @api.depends('log_ids')
    def _compute_log_ids(self):
        """
        Counts Log books of ICT.
        @author: Maulik Barad on Date 26-Sep-2019.
        """
        for ict in self:
            ict.log_count = len(ict.log_ids)

    def on_barcode_scanned(self, barcode):
        """
        Barcode scan handling method.
        @author: Maulik Barad on Date 26-Sep-2019.
        @param barcode: Scanned barcode.
        """
        ict_line_obj = self.env['inter.company.transfer.line.ept']

        product_id = self.env['product.product'].search(['|', ('barcode', '=', barcode),
                                                         ('default_code', '=', barcode)], limit=1)
        if not product_id:
            return {'warning': {
                'title': _('Warning'),
                'message': _('Product Not Found'),
                'type':'notification'}}

        line = ict_line_obj.search([('inter_company_transfer_id', '=', self._origin.id),
                                    ('product_id', '=', product_id.id)], limit=1)
        if line:
            line.write({'quantity':line.quantity + 1})
        else:
            ict_line_obj.create({'inter_company_transfer_id':self._origin.id,
                                 'product_id':product_id.id, 'quantity':1})
        return True

    @api.onchange('source_warehouse_id')
    def onchange_source_warehouse_id(self):
        """
        Method will be executed when the value of source warehouse will be changed.
        @author: Maulik Barad on Date 26-Sep-2019.
        @return: Domain for destination warehouse.
        """
        if not self.source_warehouse_id:
            self.destination_warehouse_id = False
        if self.source_warehouse_id == self.destination_warehouse_id:
            self.destination_warehouse_id = False
        self.currency_id = self.source_company_id.currency_id

        # If it's not internal type then the both warehouses should have different companies.
        domain_operator = '='
        if self.type != 'internal':
            domain_operator = '!='
        else:
            if self.source_company_id != self.destination_company_id:
                self.destination_warehouse_id = False
        return {'domain': {'destination_warehouse_id':[('company_id', domain_operator,
                                                        self.source_company_id.id),
                                                       ('id', '!=', self.source_warehouse_id.id)
                                                      ]}}

    @api.onchange('destination_warehouse_id')
    def onchange_destination_warehouse_id(self):
        """
        Method will be executed when the value of destination warehouse will be changed.
        @author: Maulik Barad on Date 26-Sep-2019.
        """
        if not self.destination_warehouse_id:
            return

        self.pricelist_id = self.destination_company_id.partner_id.with_context(
            force_company=self.source_company_id.id).property_product_pricelist

        self.crm_team_id = self.destination_company_id.partner_id.with_context(
            force_company=self.source_company_id.id).team_id or self.crm_team_id

        return

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        """
        If pricelist is changed, this method will call default_price_get for changing price in line.
        @author: Maulik Barad on Date 26-Sep-2019.
        """
        for record in self:
            record.inter_company_transfer_line_ids.default_price_get()

    @api.model
    def create(self, vals):
        """
        Inherited Method for giving sequence to ICT.
        @author: Maulik Barad on Date 26-Sep-2019.
        @param vals: Dictionary of values.
        @return: New created record.
        """
        record_name = "New"
        sequence_id = False
        if vals.get('type', '') in ['ict', '']:
            sequence_id = self.env.ref(
                'intercompany_transaction_ept.ir_sequence_inter_company_transaction').ids
        elif vals.get('type', '') == 'ict_reverse':
            sequence_id = self.env.ref(
                'intercompany_transaction_ept.ir_sequence_reverse_inter_company_transaction').ids
        elif vals.get('type', '') == 'internal':
            sequence_id = self.env.ref(
                'intercompany_transaction_ept.ir_sequence_internal_transfer').ids
        if sequence_id:
            record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
        vals.update({'name':record_name})
        res = super(InterCompanyTransferEpt, self).create(vals)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """
        Inherited for removing create functionality from reverse ICT view.
        @author: Maulik Barad on Date 26-Sep-2019.
        """
        context = self._context
        res = super(InterCompanyTransferEpt, self).fields_view_get(view_id=view_id,
                                                                   view_type=view_type,
                                                                   toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type in ['form', 'tree']:
            if context.get('default_type', 'ict_reverse') == 'ict_reverse':
                for node in doc.xpath("//tree[@string='Inter Company Transfer']"):
                    node.set('create', 'false')
                for node in doc.xpath("//form[@string='Inter Company Transfer']"):
                    node.set('create', 'false')
            res['arch'] = etree.tostring(doc)
        return res

    def action_cancel(self):
        """
        Cancels an ict.
        @author: Maulik Barad on Date 03-Oct-2019.
        """
        pickings = self.picking_ids
        invoices = self.invoice_ids
        if self.state == 'processed':
            if pickings.filtered(lambda x: x.state == 'done'):
                raise Warning("You can not cancel Inter Company Transfer which has done "
                              "pickings.")
            if invoices.filtered(lambda x: x.state == 'post'):
                raise Warning("You can not cancel Inter Company Transfer which has posted "
                              "invoices.")
            self.sale_order_ids.action_cancel()
            self.purchase_order_ids.button_cancel()
            pickings.action_cancel()
            invoices.button_cancel()
        self.write({'state':'cancel', 'message' : 'ICT has been cancelled by %s' % (
            self.env.user.name)})

    def process_ict(self):
        """
        This method processes the ict and creates sale and purchase order. Rest will be as per
        configuration.
        @author: Maulik Barad on Date 26-Sep-2019.
        """
        context = self._context.copy() or {}

        for record in self:
            if record.with_context(context).check_user_validation():
                if not record.inter_company_transfer_line_ids:
                    msg = "Please Add the Product to Process ICT."
                    raise ValidationError(msg)

                if record.type == "internal":
                    internal_transfer = record.create_internal_transfer()
                    if internal_transfer:
                        record.write({'state':'processed', 'processed_date':datetime.today(),
                                      'message':'ICT processed successfully by %s' % (
                                          self.env.user.name)})
                    return True

                # context.update({'allowed_company_ids':self.env.user.company_ids.ids})
                record.create_sale_order()
                record.create_purchase_order()

                configuration_record = record.env.ref(
                    'intercompany_transaction_ept.inter_company_transfer_config_record')

                if configuration_record:
                    # Confirms orders, if auto confirm is set True.
                    if configuration_record.auto_confirm_orders:
                        record.confirm_orders()
                    # Creates invoice and vendor bill, if auto create invoice is set True.
                    if configuration_record.auto_create_invoices:
                        record.create_invoice()

                record.write({'state':'processed', 'processed_date':datetime.today(),
                              'message':'ICT processed successfully by %s' % (self.env.user.name)})

        return True

    def create_internal_transfer(self):
        """
        Creates internal transfers for same company.
        @author: Maulik Barad on Date 27-Sep-2019.
        """
        procurement_group_obj = self.env['procurement.group']
        procurements = []

        destination_warehouse = self.destination_warehouse_id

        group_id = procurement_group_obj.create({'name': self.name,
                                                 'partner_id': destination_warehouse.partner_id.id})
        if not group_id:
            raise Warning("Problem with creation of procurement group.")

        self.group_id = group_id
        route_ids = self.env['stock.location.route'].search([
            ('supplied_wh_id', '=', destination_warehouse.id),
            ('supplier_wh_id', '=', self.source_warehouse_id.id)])

        if not route_ids:
            raise ValidationError(_("No routes are found. \n Please configure warehouse routes "
                                    "and set in products."))
        if not self.inter_company_transfer_line_ids:
            raise ValidationError(_("No Products found. \n Please add products to transfer."))

        # Prepares list of tuples for procurement.
        for line in self.inter_company_transfer_line_ids:
            procurements.append(procurement_group_obj.Procurement(
                line.product_id, line.quantity, line.product_id.uom_id,
                destination_warehouse.lot_stock_id, self.name, False,
                destination_warehouse.company_id,
                values={'warehouse_id':destination_warehouse,
                        'route_ids':route_ids[0] if route_ids else [],
                        'group_id':self.group_id}))

        if procurements:
            self.env['procurement.group'].run(procurements)

        pickings = self.env['stock.picking'].search([('group_id', '=', group_id.id)])
        if not pickings:
            raise Warning("No Pickings are created for this record.")
        shipper_id = self.shipper_id and self.shipper_id.id or False              
        pickings.write({'x_shipper_id': shipper_id,
            'inter_company_transfer_id':self.id,
            'note': self.x_studio_internal_notes})
        picking = pickings.filtered(
            lambda x: x.location_id.id == self.source_warehouse_id.lot_stock_id.id)
        if picking:
            picking.action_assign()
        return True

    def create_sale_order(self):
        """
        Creates sale order for ICT of different companies.
        @author: Maulik Barad in Date 28-Sep-2019.
        @return: Recordset of sale order.
        """
        sale_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']

        for record in self:
            customer_partner_id = record.destination_company_id.partner_id

            # Creates sale order.
            order_vals = sale_obj.new({'partner_id':customer_partner_id.id,
                                       'warehouse_id':record.source_warehouse_id.id,
                                       'pricelist_id':self.pricelist_id.id,
                                       'company_id':record.source_company_id.id})
            order_vals.onchange_partner_id()
            order_vals.onchange_partner_shipping_id()
            if record.crm_team_id:
                order_vals.team_id = record.crm_team_id.id

            sale_order = sale_obj.create(order_vals._convert_to_write(order_vals._cache))

            # Creates sale order lines.
            for line in record.inter_company_transfer_line_ids:
                line_vals = sale_order_line_obj.new({'order_id':sale_order.id,
                                                     'product_id':line.product_id})

                # Assigns custom values and calls necessary on_change methods.
                line_vals.product_id_change()
                line_vals.update({'product_uom_qty':line.quantity, 'price_unit':line.price})

                sale_order_line_obj.create(line_vals._convert_to_write(line_vals._cache))

            sale_order.write({'inter_company_transfer_id':record.id})

        return True

    def create_purchase_order(self):
        """
        Creates purchase order for ICT of different companies.
        @author: Maulik Barad in Date 28-Sep-2019.
        @return: Recordset of purchase order.
        """
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']

        for record in self:
            destination_company = record.destination_company_id

            # Creates purchase order.
            order_vals = purchase_obj.new({'currency_id':record.currency_id.id,
                                           'partner_id':record.source_company_id.partner_id.id,
                                           'company_id':destination_company.id})
            order_vals.onchange_partner_id()
            order_vals.currency_id = record.currency_id.id
            order_vals.picking_type_id = record.destination_warehouse_id.in_type_id
            purchase_order = purchase_obj.create(order_vals._convert_to_write(order_vals._cache))

            # Creates purchase order lines.
            for line in record.inter_company_transfer_line_ids:
                line_vals = purchase_line_obj.new({'order_id':purchase_order.id,
                                                   'product_id':line.product_id,
                                                   'currency_id':self.currency_id})

                # Assigns custom values and calls necessary on_change methods.
                line_vals.onchange_product_id()
                line_vals.update({'product_qty':line.quantity,
                                  'price_unit':line.price,
                                  'product_uom':line.product_id.uom_id.id})

                purchase_line_obj.create(line_vals._convert_to_write(line_vals._cache))

            purchase_order.write({'inter_company_transfer_id':record.id})

        return True

    def confirm_orders(self):
        """
        Confirms sale and purchase orders of ict.
        @author: Maulik Barad on Date 26-Sep-2019.
        """
        for record in self:
            sale_orders = record.sale_order_ids.filtered(lambda x:x.state in ['draft', 'sent'])
            sale_orders.write({'origin':record.name or ''})
            sale_orders.with_context(force_company=sale_orders.company_id.id).action_confirm()

            purchase_orders = record.purchase_order_ids.filtered(lambda x:x.state in ['draft', 'sent'])
            purchase_orders.write({'origin':record.name or ''})
            purchase_orders.with_context(force_company=purchase_orders.company_id.id).button_confirm()

        return True

    def create_invoice(self):
        """
        Creates invoice and vendor bill for sale and purchase order respectively.
        @author: Maulik Barad on Date 26-Sep-2019.
        @param purchase_orders: Recordset of purchase.order.
        @param sale_orders: Recordset of sale.order.
        """
        account_move_obj = self.env['account.move']
        configuration_record = self.env.ref(
            'intercompany_transaction_ept.inter_company_transfer_config_record')

        for record in self:
            # Getting ICT Users and Journals.
            sale_journal = record.source_company_id.sale_journal_id
            purchase_journal = record.destination_company_id.purchase_journal_id

            sale_orders = record.sale_order_ids.filtered(
                lambda x:x.state in ['sale', 'done'] and
                not x.invoice_ids.filtered(
                    lambda x:x.type == 'out_invoice' and x.state in ['draft', 'posted']))

            purchase_orders = record.purchase_order_ids.filtered(
                lambda x:x.state in ['purchase', 'done'] and
                not x.invoice_ids.filtered(
                    lambda x:x.type == 'in_invoice' and x.state in ['draft', 'posted']))

            log_book = self.env['inter.company.transfer.log.book.ept'].return_log_record(self,
                                                                                     "invoice")
            # Creating Invoice.
            invoice = False
            for order in sale_orders:
                context = {"active_model": 'sale.order', "active_ids": [order.id],
                           "active_id": order.id, 'open_invoices':True}
                if sale_journal:
                    context.update({'default_journal_id':sale_journal.id})

                advance_payment = self.env['sale.advance.payment.inv'].create({
                    'advance_payment_method': 'delivered'})
                try:
                    result = advance_payment.with_context(context).create_invoices()
                except Exception as error:
                    log_book.post_log_line(error.name)
                    continue
                invoice_id = result.get('res_id', False)
                invoice = account_move_obj.browse(invoice_id)
                if invoice:
                    invoice.write({'invoice_date':fields.Date.context_today(record),
                                   'inter_company_transfer_id':record.id})

            # Creating Vendor Bill.
            vendor_bill = False
            for order in purchase_orders:
                context = {'default_type': 'in_invoice', 'type': 'in_invoice',
                           'journal_type': 'purchase', 'default_purchase_id': order.id}
                context.update({
                    'default_journal_id':purchase_journal.id if purchase_journal else False})

                # Creates new object for vendor bill.
                # Updated by Udit on 18th December 2019 (Added sudo)
                invoice_vals = account_move_obj.with_context(context).sudo().new(record.prepare_invoice_dict(order))

                # Assigns custom values and calls necessary on_change methods.
                invoice_vals.update({
                    'purchase_id':order.id,
                    'journal_id':invoice_vals._get_default_journal(),
                    'invoice_date':fields.Date.context_today(record),
                    'currency_id':record.currency_id.id,
                    'inter_company_transfer_id':record.id
                    })

                invoice_vals._onchange_purchase_auto_complete()
                invoice_vals._onchange_partner_id()
                invoice_vals._onchange_invoice_date()

                for line in invoice_vals.invoice_line_ids:
                    if not line.quantity:
                        invoice_vals.invoice_line_ids -= line

                if invoice_vals.invoice_line_ids:
                    try:
                        vendor_bill = account_move_obj.with_context({
                            'type':'in_invoice'}).create(invoice_vals._convert_to_write(invoice_vals._cache))
                        continue
                    except Exception as error:
                        log_book.post_log_line(error.name)
                        continue
                log_book.post_log_line("No invoicable line found for creating the vendor bill.")

            # Validates invoices if configured.
            if configuration_record.auto_validate_invoices:
                if invoice:
                    invoice.action_post()
                if vendor_bill:
                    vendor_bill.action_post()

            if not log_book.ict_log_line_ids:
                # Updated by Udit on 18th December 2019 (Added sudo)
                log_book.sudo().unlink()

        return True

    def create_reverse_ict(self):
        """
        Creates reverse.inter.company.transfer.ept model's record and opens it's in wizard.
        @author: Maulik Barad on Date 01-Oct-2019.
        @return: Action for opening the reverse ict's wizard.
        """
        reverse_ict_line_obj = self.env['reverse.inter.company.transfer.line.ept']
        created_reverse_line_ids = []

        log_book = self.env['inter.company.transfer.log.book.ept'].return_log_record(self,
                                                                                     "reverse")

        for line in self.inter_company_transfer_line_ids:
            if line.delivered_qty != 0.0 and line.delivered_qty <= line.quantity:
                inter_company_transfer_ids = self.search([('inter_company_transfer_id', '=',
                                                           self.id),
                                                          ('type', '=', 'ict_reverse'),
                                                          ('state', '!=', 'cancel')])

                # If already reverse ICTs are there, then quantity will be decreased.
                if inter_company_transfer_ids:
                    delivered_qty = 0.0
                    total_qty_deliverd = 0.0
                    for ict in inter_company_transfer_ids:
                        for transfer_line in ict.inter_company_transfer_line_ids.filtered(
                                lambda x: x.product_id == line.product_id):
                            total_qty_deliverd += transfer_line.quantity
                    delivered_qty = line.delivered_qty - total_qty_deliverd
                    if delivered_qty > 0.0:
                        created_reverse_line_ids.append(
                            reverse_ict_line_obj.create({
                                'product_id':line.product_id.id, 'quantity':delivered_qty,
                                'delivered_qty': delivered_qty, 'price' : line.price}).id)
                else:
                    created_reverse_line_ids.append(
                        reverse_ict_line_obj.create({
                            'product_id':line.product_id.id, 'quantity':line.delivered_qty,
                            'delivered_qty': line.delivered_qty, 'price' : line.price}).id)
            else:
                msg = """Line is not considered as there is no product is delivered yet.
                Product : %s""" % line.product_id.name
                log_book.post_log_line(msg, log_type='info')

        if not log_book.ict_log_line_ids:
            log_book.sudo().unlink()

        # Opens wizard if reverse lines are found.
        if created_reverse_line_ids:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'reverse.inter.company.transfer.ept',
                'views':[(False, 'form')],
                'context' : {'default_inter_company_transfer_id':self.id,
                             'default_reverse_ict_line_ids':[(6, 0, created_reverse_line_ids)]},
                'target': 'new',
            }
        raise Warning("There are no products found for the Reverse Transaction!!")

    def process_reverse_ict(self):
        """
        Processes reverse ICT created from ICT.
        @author: Maulik Barad on Date 01-Oct-2019.
        """
        return_picking_line_list = []
        pickings = self.env['stock.picking']
        stock_return_picking_obj = self.env['stock.return.picking']

        if not self.inter_company_transfer_line_ids:
            raise Warning("There are no products in the record!!")

        if self.inter_company_transfer_id.type == 'internal':
            # Updated by Udit on 18th December 2019 (Added condition to take only done pickings)
            pickings = self.inter_company_transfer_id.picking_ids.filtered(lambda record:record.state == 'done')
        else:
            # Add picking of sale order.
            # Updated by Udit on 18th December 2019 (Added condition to take only done pickings)
            if self.inter_company_transfer_id.sale_order_ids:
                pickings += self.inter_company_transfer_id.sale_order_ids.mapped("picking_ids") and\
                            self.inter_company_transfer_id.sale_order_ids.mapped("picking_ids").\
                                        filtered(lambda x: x.picking_type_id.code == 'outgoing' and x.state == 'done')
            if not pickings:
                raise ValidationError(_("No pickings are available in sale order."))

            # Add picking of purchase order.
            if self.inter_company_transfer_id.purchase_order_ids:
                pickings += self.inter_company_transfer_id.purchase_order_ids.mapped("picking_ids")\
                                            and self.inter_company_transfer_id.purchase_order_ids.\
                                                mapped("picking_ids").filtered(
                                                    lambda x: x.picking_type_id.code == 'incoming' and x.state == 'done')

        if not pickings:
            raise ValidationError(_("There are no pickings available in %s " % (
                self.inter_company_transfer_id.name)))
        # Updated by Udit on 18th December 2019 (Added condition not to take done and cancel pickings)
        if pickings.filtered(lambda x: x.state not in ['done','cancel']):
            raise ValidationError(_("""%s have some pickings which are not in done state yet!!
                Please done pickings before reverse it. """ % self.inter_company_transfer_id.name))

        processed = False
        for picking in pickings:
            for line in self.inter_company_transfer_line_ids:
                for move_id in picking.move_lines.filtered(
                        lambda x: x.product_id == line.product_id and x.state == 'done'):
                    line_tmp = (0, 0, {'product_id': move_id.product_id.id,
                                       'move_id': move_id.id,
                                       'quantity': line.quantity,
                                       'to_refund': False})
                    return_picking_line_list.append(line_tmp)

            default_vals = stock_return_picking_obj.with_context({
                'active_id':picking.id,
                'active_model':'stock.picking'}).default_get(['move_dest_exists',
                                                              'original_location_id',
                                                              'parent_location_id',
                                                              'location_id',
                                                              'product_return_moves'])
            default_vals.update({'product_return_moves':return_picking_line_list,
                                 'location_id':picking.location_id.id})
            return_picking = stock_return_picking_obj.create(default_vals)
            new_picking_id = return_picking.with_context({'active_id':picking.id}).create_returns()
            stock_picking_id = pickings.browse(new_picking_id.get('res_id'))
            if stock_picking_id:
                stock_picking_id.inter_company_transfer_id = self.id
                processed = True
            return_picking_line_list = []

        # If this is reverse of internal transfer then it will not let create refund.
        if self.inter_company_transfer_id.type == 'internal':
            if processed:
                self.write({'state':'processed', 'processed_date':datetime.today()})
                return True
            return False

        return self.reverse_invoices()

    def reverse_invoices(self):
        """
        Reverses invoices by creating credit notes.
        @author: Maulik Barad on Date 03-Oct-2019.
        """
        invoices = []
        account_move_obj = self.env['account.move']
        account_move_reversal_obj = self.env['account.move.reversal']
        configuration_record = self.env.ref('intercompany_transaction_ept.'
                                            'inter_company_transfer_config_record')

        # Gather all invoices.
        invoices += self.inter_company_transfer_id.sale_order_ids.mapped(
            'invoice_ids').filtered(lambda x: x.type == 'out_invoice')
        invoices += self.inter_company_transfer_id.purchase_order_ids.mapped(
            'invoice_ids').filtered(lambda x: x.type == 'in_invoice')

        for invoice in invoices:
            default_invoice_vals = account_move_reversal_obj.with_context(
                {'active_id':invoice.id}).default_get(['refund_method',
                                                       'reason',
                                                       'date'])
            if configuration_record.refund_method:
                default_invoice_vals['refund_method'] = configuration_record.refund_method
            default_invoice_vals.update({'reason':'%s' % (configuration_record and
                                                          configuration_record.description or
                                                          ('for %s' % self.name))})

            # Creates record of account.move.reveresal model for creating credit note.
            customer_refund = account_move_reversal_obj.create(default_invoice_vals)
            if customer_refund.with_context({'active_model':'account.move',
                                             'active_ids':invoice.id}).reverse_moves():
                invoice_id = account_move_obj.search([
                    ('reversed_entry_id', '=', invoice.id)], order='id desc', limit=1)
                if invoice_id:
                    invoice_id.inter_company_transfer_id = self.id
                    for invoice_line in invoice_id.invoice_line_ids:
                        match_line = self.inter_company_transfer_line_ids.filtered(
                            lambda x: x.product_id == invoice_line.product_id)
                        if match_line:
                            invoice_line.with_context({
                                'check_move_validity':False}).write({
                                    'quantity':match_line.quantity})
                            invoice_id.with_context({
                                'check_move_validity':False})._recompute_dynamic_lines()
                    if invoice_id.state == "draft":
                        invoice_id.action_post()

        self.write({'state':'processed', 'processed_date':datetime.today()})
        return True

    def check_user_validation(self):
        """
        Checks for ICT User configuration and the company.
        @author: Maulik Barad on date 27-Sep-2019.
        """
        for record in self:
            if record.source_warehouse_id.company_id not in self.env.user.company_ids:
                if record.source_warehouse_id.company_id not in\
                                                            self.env.user.company_id.child_ids:
                    raise ValidationError("""User '%s' can not process this Inter Company Transfer.\n User
                    from Source Warehouse Company can Process it !!!!\n\nPlease Process
                    it with User of Source Warehouse Company.""" % (self.env.user.name))
        return True

    def prepare_invoice_dict(self, order):
        """
        Prepares dictionary of values for creating invoice.
        @author: Maulik Barad on Date 27-Sep-2019.
        @param order: Order for setting values according to it.
        @return: Dictionary of values.
        """
        vals = {
            'company_id': self.destination_company_id.id or False,
            'currency_id':self.currency_id.id,
            'partner_id':order.partner_id.id,
            'type': 'in_invoice',
            'purchase_id': order.id,
            }
        return vals

    def reset_to_draft(self):
        """
        Changes state to draft.
        @author: Maulik Barad on Date 01-Oct-2019.
        """
        for record in self:
            record.state = 'draft'
        return True

    def unlink(self):
        """
        Inherited method for preventing the deletion of ICT.
        @author: Maulik Barad on Date 01-Oct-2019.
        """
        for record in self:
            if record.state == 'processed':
                raise Warning("You can not delete transaction, which is in Processed state !!")
        return super(InterCompanyTransferEpt, self).unlink()
