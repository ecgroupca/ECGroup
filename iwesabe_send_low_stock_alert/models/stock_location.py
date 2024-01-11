# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _

class StockLocation(models.Model):
    _name = "stock.location"
    _inherit = ["stock.location", 'mail.thread', 'mail.activity.mixin']
    _description = "Low Stock On Locations"

    @api.model
    def _cron_send_alert_for_low_stock(self):
        def _set_html_body(low_stock_quant_ids):
            table_html = """
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th scope="col">Product Name</th>
                            <th scope="col">Available Quantity</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for low_stock_quant_id in low_stock_quant_ids:
                table_html +="""
                    <tr>
                        <td>
                            {product_name}
                        </td>
                        <td>
                            {available_qty}
                        </td>
                    </tr>
                """.format(product_name=low_stock_quant_id.display_name,
                           available_qty=low_stock_quant_id.available_quantity)
            table_html += """
                    </tbody>
                </table>
                """
            html_body = """
                <div class="page">
                    <p>Dear Inventory Manager,</p>
                    <div class="container">
                       <p>The following items are running low on stock:</p>
                        {table_html}
                        
                    </div>
                    <p>Please take appropriate actions to restock these items as soon as possible.</p>
                    <p>Thanks for your attention.</p>
                </div>
            """.format(table_html = table_html)
            return html_body

        def _send_mail(user_id,location_id,body,company):
            subject = "Low Stock At {location}".format(location=location_id.display_name)
            mail_id = self.env['mail.mail'].create({
                'subject':subject,
                'email_from':company.email,
                'email_to':user_id.login,
                'body_html':body,
            })
            mail_id.sudo().send()
            return mail_id


        self = self.sudo()
        group_id = self.env.ref('iwesabe_send_low_stock_alert.group_notify_low_stock')
        location_model = self.env['ir.model'].sudo().search([('model','=','stock.location')])
        activity_type_id = self.env.ref('mail.mail_activity_data_todo')
        user_ids = group_id.users
        if not user_ids:
            return
        company_ids = self.env['res.company'].sudo().search([])
        for company_id in company_ids:
            low_stock_alert_qty = company_id.low_stock_alert_qty
            internal_loc_ids = self.search([('usage','=','internal'),('company_id','in',[False, company_id.id])])
            for internal_loc_id in internal_loc_ids:
                low_stock_quant_ids = internal_loc_id.quant_ids.filtered(lambda quant:quant.available_quantity <= low_stock_alert_qty)
                if low_stock_quant_ids:
                    html_body = _set_html_body(low_stock_quant_ids)
                    for user_id in user_ids:
                        mail_activity = self.env['mail.activity'].create({'activity_type_id': activity_type_id.id,
									'date_deadline': datetime.today(),
									'summary': "Alert - Low Stock",
									'create_uid' : user_id.id,
									'user_id': user_id.id,
									'res_id': internal_loc_id.id,
									'res_model_id': location_model.id,
									'note':html_body,
									})
                        
                        _send_mail(user_id,internal_loc_id,html_body,company_id)




