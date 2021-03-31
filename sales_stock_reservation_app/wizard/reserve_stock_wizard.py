# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api, _
from odoo.exceptions import Warning, UserError
from datetime import datetime
from email.utils import formataddr

# Res Config
class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	@api.model
	def default_get(self, fields):
		result = super(ResConfigSettings, self).default_get(fields)
		if result:
			config_obj = self.env['stock.location'].search([('name', '=', 'Reserved Stock Location')], limit=1).id
			result.update({ 
				'location_dest_id' : config_obj,
			})
		return result
		
	location_id = fields.Many2one('stock.location', string="Source Location")
	location_dest_id = fields.Many2one('stock.location', string="Destination Location")

	@api.model
	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		ICPSudo = self.env['ir.config_parameter'].sudo()
		location_id = ICPSudo.get_param('sales_stock_reservation_app.location_id')
		location_dest_id = ICPSudo.get_param('sales_stock_reservation_app.location_dest_id')

		res.update(
			location_id=int(location_id) or False,
			location_dest_id=int(location_dest_id) or False,
			stock_move_sms_validation=False)
		return res

	def set_values(self):
		super(ResConfigSettings, self).set_values()
		ICPSudo = self.env['ir.config_parameter'].sudo()
		ICPSudo.set_param('sales_stock_reservation_app.location_id',self.location_id.id)
		ICPSudo.set_param('sales_stock_reservation_app.location_dest_id',self.location_dest_id.id)

# Stock Reserve Wizard
class StockReserve(models.TransientModel):
	_name = 'stock.reserve'
	_description = "Sales Stock Reserve"

	sale_order = fields.Many2one( 'sale.order', String="Sale Order",)
	notify_user = fields.Many2many('res.partner', string='Notify User', required=True)
	stock_reserve_line = fields.One2many('stock.reserve.line', 'stock_reserve_line_id', string='Stock Reserve')

	@api.model
	def default_get(self, fields):
		rec = super(StockReserve, self).default_get(fields)
		record = self.env['sale.order'].browse(self._context.get('active_ids',[]))
		line_ids = []
		for line in record.order_line:
			vals = {
					'product_id': line.product_id.id,
					'product_qty': line.product_uom_qty,
					'product_uom': line.product_uom.id,
					'order_line_id': line.id,
					}
			line_ids.append((0,0, vals))
		rec.update({'stock_reserve_line': line_ids, 'sale_order': record.id})
		return rec


	def reserve_sales_stock(self):
		self.ensure_one()

		res = self.env['reserved.stock']
		source_location = self.env["ir.config_parameter"].sudo().get_param("sales_stock_reservation_app.location_id")
		destination_location = self.env["ir.config_parameter"].sudo().get_param("sales_stock_reservation_app.location_dest_id")
		if source_location and destination_location:
			move_lines = []
			picking_obj = self.env['stock.picking']
			template_id =  self.env['ir.model.data'].get_object_reference('sales_stock_reservation_app',
				   'reserved_stock_email_template')[1]
			template_browse = self.env['mail.template'].browse(template_id)

			body_html = """ Dear """+ str(self.sale_order.partner_id.name) + """,<br />We are pleased to inform you that stock from <b>"""+ str(self.sale_order.name) + """</b>
							as per bellow list is reserved by <b>""" + str(self.env.user.name) +"""</b>.<br /><br />"""

			body_html += """<table style="width: 740px; height: 130px;" border="1">
							<tr style="text-align: center;">
								<th> Name </th>
								<th> Product </th>
								<th> Quantity Reserved </th>
							</tr>"""

			
			for record in self.stock_reserve_line:

				if record.product_id.qty_available == 0.0 or record.product_id.qty_available >= 0.0:
					if str(record.product_id.type) == 'product':
						
						value = {
								'reference': self.sale_order.name,
								'sale_order': self.sale_order.id,
								'order_line_id': record.order_line_id.id,
								'product_id': record.product_id.id,
								'product_qty': record.product_qty,
								'reserve_qty': record.reserve_qty,
								'user_id': self.env.user.id,
								'location_id': int(source_location),
								'location_dest_id': int(destination_location),
								}
						
						reserved_stock = res.create(value)
						reserved_stock.action_reserved()
						reserved_dict =  {
										'name':record.product_id.name,
										'product_id':record.product_id.id,
										'product_uom_qty':record.reserve_qty,
										'quantity_done':record.reserve_qty,
										'product_uom':record.product_uom.id,
										'location_id': int(source_location),
										'location_dest_id': int(destination_location),
										}
						
						move_lines.append((0, 0, reserved_dict))
						body_html += "<tr><td style='text-align: center;'>" + str(reserved_stock.name) + "</td><td>" + str(reserved_stock.product_id.name) + "</td><td style='text-align: center;'>" + str(reserved_stock.reserve_qty) + "</td></tr>"
						
					else:
						raise UserError(_('You can not reserve consumable or service type product !'))
				
				else:
					raise UserError(_('Product not have enough on hand quantity to reserve !'))	
			
			if move_lines:
				values = {
							'partner_id': self.sale_order.partner_id.id,
							'location_id': int(source_location),
							'location_dest_id': int(destination_location),
							'scheduled_date': datetime.now(),
							'date_done': datetime.now(),
							'origin': self.sale_order.name,
							'owner_id': self.sale_order.partner_id.id,
							'picking_type_id': self.env.ref('stock.picking_type_out').id,
							'move_ids_without_package': move_lines,
						}
				
				picking = picking_obj.create(values)
				picking.action_confirm()
				picking.action_assign()
				picking.button_validate()
				body_html += """</table><br />
								Do not hesitate to contact us if you have any question. <br /><br />
								Thanks & Regards.<br />
								from """+ str(self.sale_order.partner_id.company_id.name) + """.
							</p>
						</div> """	
				email_cc_list = []
				for customer in self.notify_user:
					email_to = formataddr((str(customer.name) or 'False', str(customer.email) or 'False'))
					email_cc_list.append(email_to)
				
				email_cc_string = ','.join(email_cc_list)
				values = template_browse.generate_email(self.id, fields=None)
				values['email_from'] = self.env['res.users'].browse(self.env['res.users']._context['uid']).partner_id.email 
				values['email_to'] = email_cc_string
				values['res_id'] = False
				values['subject'] = "Stock Reservation Confirmed : " + str(self.sale_order.name)
				values['author_id'] = self.env['res.users'].browse(self.env['res.users']._context['uid']).partner_id.id 
				values['body_html'] = body_html
				values['auto_delete'] = False



				mail_mail_obj = self.env['mail.mail']
				msg_id = mail_mail_obj.sudo().create(values)

				if msg_id:
					msg_id.sudo().send()
				self.sale_order.check_stock = True
		else:
			raise UserError(_('Please Select Source & Destination Location in Inventory Configuration !'))


# Stock Reserve Wizard Line
class StockReserveLine(models.TransientModel):
	_name = 'stock.reserve.line'
	_description = "Sales Stock Reserve Line"

	stock_reserve_line_id = fields.Many2one('stock.reserve')
	order_line_id = fields.Many2one( 'sale.order.line', String="Sale Order")
	product_id = fields.Many2one( 'product.product', String="Product")
	product_qty = fields.Float("Quantity")
	product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
	reserve_qty = fields.Float("Reserve Quantity", required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: