# -*- coding: utf-8 -*-
#############################################################################
#
#    Quickbeam ERP.
#
#    Copyright (C) 2021-TODAY, Quickbeam, LLC.
#    Author: Adam O'Connor <aoconnor@quickbeamllc.com>
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
 
    def action_done(self):
        res = super(StockPicking, self).action_done()
        if res:        
            for pick in self:
                sale = pick.sale_id
                if sale:
                    done = True
                    for line in sale.order_line:
                        if line.product_id.type == 'product' and line.product_uom_qty > line.qty_delivered:
                            done = False
                            break
                    sale.fully_shipped_date = done and pick.date_done or False