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
                            <th scope="col">Min Quantity</th>
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
                        <td>
                            {min_qty}
                        </td>
                    </tr>
                """.format(product_name=low_stock_quant_id.display_name,
                           available_qty=low_stock_quant_id.product_id.qty_available,
                           min_qty=low_stock_quant_id.product_id.reordering_min_qty)
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

        def _send_mail(location_id,body,company):
            subject = "Low Stock At {location}".format(location=location_id.display_name)
            mail_id = self.env['mail.mail'].create({
                'subject':subject,
                'email_from':company.email,
                'email_to':'aoconnor@quickbeamllc.com',
                'body_html':body,
            })
            mail_id.sudo().send()
            return mail_id


        self = self.sudo()
        location_model = self.env['ir.model'].sudo().search([('model','=','stock.location')])
        activity_type_id = self.env.ref('mail.mail_activity_data_todo')
        company_ids = self.env['res.company'].sudo().search([])
        for company_id in company_ids:
            loc_dom = [('usage','=','internal')]
            loc_dom += [('name','in',['Raw','Finished'])]
            loc_dom += [('company_id','in',[False, company_id.id])]
            internal_loc_ids = self.search(loc_dom)
            for internal_loc_id in internal_loc_ids:
                low_stock_quant_ids = internal_loc_id.quant_ids.filtered(lambda quant:quant.product_id.qty_available <= quant.product_id.reordering_min_qty)              
                if low_stock_quant_ids:
                    html_body = _set_html_body(low_stock_quant_ids)
                    mail_activity = self.env['mail.activity'].create({'activity_type_id': activity_type_id.id,
                                'date_deadline': datetime.today(),
                                'summary': "Alert - Low Stock",
                                'create_uid' : 1,
                                'user_id': 1,
                                'res_id': internal_loc_id.id,
                                'res_model_id': location_model.id,
                                'note':html_body,
                                })
                    _send_mail(internal_loc_id,html_body,company_id)
                lambda_func = lambda quant:'Verano' in quant.product_id.name
                lambda_func |= quant.product_id.categ_id.name == 'Accessories'
                lambda_func |= quant.product_id.categ_id.name == 'Lamps'
                lambda_func |= quant.product_id.categ_id.name == 'Lanterns'
                lambda_func |= quant.product_id.categ_id.name == 'Occassional Tables'
                lambda_func |= quant.product_id.categ_id.name == 'Sconces'
                prod_line_quant_ids = internal_loc_id.quant_ids.filtered(lambda_func)                                
                if prod_line_quant_ids:
                    html_body = _set_html_body(prod_line_quant_ids)
                    mail_activity = self.env['mail.activity'].create({'activity_type_id': activity_type_id.id,
                                'date_deadline': datetime.today(),
                                'summary': "Low Stock - Best Sellers and Accessories",
                                'create_uid' : 1,
                                'user_id': 1,
                                'res_id': internal_loc_id.id,
                                'res_model_id': location_model.id,
                                'note':html_body,
                                })
                    _send_mail(internal_loc_id,html_body,company_id)




