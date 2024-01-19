from datetime import datetime
from odoo import models, fields, api, _

class StockLocation(models.Model):
    _name = "stock.location"
    _inherit = ["stock.location", 'mail.thread', 'mail.activity.mixin']
    _description = "Low Stock On Locations"

    @api.model
    def _cron_send_alert_for_low_stock(self,user_names):
        def _set_html_body(low_stock_quant_ids,item_cat=''):
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
                       <p>The following {item_cat} items are running low on stock:</p>
                        {table_html}
                        
                    </div>
                    <p>Please take appropriate actions to restock these items as soon as possible.</p>
                    <p>Thanks for your attention.</p>
                </div>
            """.format(item_cat=item_cat,table_html=table_html)
            return html_body

        def _send_mail(location_id,body,company,recipient_ids,item_cat=''):
            subject = "Low {item_cat} Stock At {location}".format(item_cat=item_cat,location=location_id.display_name)
            mail_id = self.env['mail.mail'].create({
                'subject':subject,
                'email_from':company.email,
                'recipient_ids': [(6, 0, recipient_ids.ids)],
                'body_html':body,
            })
            mail_id.sudo().send()
            return mail_id


        self = self.sudo()
        location_model = self.env['ir.model'].sudo().search([('model','=','stock.location')])
        activity_type_id = self.env.ref('mail.mail_activity_data_todo')
        company_ids = self.env['res.company'].sudo().search([])
        recipient_ids = self.env['res.partner'].sudo().search([('name', 'in', user_names)])
        for company_id in company_ids:
            loc_dom = [('usage','=','internal')]
            loc_dom += [('name','in',['Raw','Finished'])]
            loc_dom += [('company_id','in',[False, company_id.id])]
            internal_loc_ids = self.search(loc_dom)
            for internal_loc_id in internal_loc_ids:
                low_stock_quant_ids = internal_loc_id.quant_ids.filtered(lambda quant:quant.product_id.qty_available <= quant.product_id.reordering_min_qty)    
                
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: quant.product_id.default_code not in ['',False])
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'art'.upper() not in quant.product_id.default_code.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'misc'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'custom'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'Prototype'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'model'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'mold'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'counter sample'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'Master Sample'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'R&D'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'Finish Sample'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'candle'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'Pillow'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'Fabric'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'leather'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'Limited Edition'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'refinish'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'rework'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'repair'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'pavillion'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'hook'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'foam'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'template'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'inactive'.upper() not in quant.product_id.name.upper())
                low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: 'do not use'.upper() not in quant.product_id.name.upper())
                #low_stock_quant_ids = low_stock_quant_ids.filtered(lambda quant: quant.product_id.reordering_min_qty>0)
                
                product_ids = self.env['product.product']
                quant_ids = self.env['stock.quant']
                for quant_id in low_stock_quant_ids:
                    if quant_id.product_id in product_ids:
                        #quant_ids.remove(quant_id)
                        continue
                    else:
                        product_ids |= quant_id.product_id
                        quant_ids |= quant_id
                        
                if quant_ids:
                    html_body = _set_html_body(quant_ids)
                    mail_activity = self.env['mail.activity'].create({'activity_type_id': activity_type_id.id,
                                'date_deadline': datetime.today(),
                                'summary': "Alert - Low Stock",
                                'create_uid' : 1,
                                'user_id': 1,
                                'res_id': internal_loc_id.id,
                                'res_model_id': location_model.id,
                                'note':html_body,
                                })
                    _send_mail(internal_loc_id,html_body,company_id,recipient_ids)

                cat_list = ['Accessories','Lamps','Lanterns','Occassional Tables','Sconces']
                cat_line_quant_ids = quant_ids.filtered(lambda quant: quant.product_id.categ_id.name in cat_list) 
                cat_line_quant_ids = quant_ids.filtered(lambda quant:'Verano'.upper() not in quant.product_id.name.upper())                
                if cat_line_quant_ids:
                    item_cat = "Accessories,Lamps,Lanterns,Occassional Tables,and Sconces"
                    html_body = _set_html_body(cat_line_quant_ids,item_cat=item_cat)
                    mail_activity = self.env['mail.activity'].create({'activity_type_id': activity_type_id.id,
                                'date_deadline': datetime.today(),
                                'summary': "Low Stock - Best Sellers and Accessories",
                                'create_uid' : 1,
                                'user_id': 1,
                                'res_id': internal_loc_id.id,
                                'res_model_id': location_model.id,
                                'note':html_body,
                                })
                    _send_mail(internal_loc_id,html_body,company_id,recipient_ids,item_cat=item_cat)
                    
                verano_line_quant_ids = quant_ids.filtered(lambda quant:'Verano'.upper() in quant.product_id.name.upper())                                
                if verano_line_quant_ids:
                    item_cat = "Verano"
                    html_body = _set_html_body(verano_line_quant_ids,item_cat=item_cat)
                    mail_activity = self.env['mail.activity'].create({'activity_type_id': activity_type_id.id,
                                'date_deadline': datetime.today(),
                                'summary': "Low Stock - Verano Line",
                                'create_uid' : 1,
                                'user_id': 1,
                                'res_id': internal_loc_id.id,
                                'res_model_id': location_model.id,
                                'note':html_body,
                                })
                    item_cat = "Verano"
                    _send_mail(internal_loc_id,html_body,company_id,recipient_ids,item_cat=item_cat)




