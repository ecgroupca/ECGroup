# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Odoo Cancel Manufacturing Orders",
  "summary"              :  """Cancel manufacturing orders in bulk.""",
  "category"             :  "Manufacturing",
  "version"              :  "1.0.0",
  "sequence"             :  10,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/",
  "description"          :  """Cancel manufacturing orders in bulk
Cancel manufacturing order with reason
Send mail of order's cancellation to the responsible person
Cancel manufacturing order in done state""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=wk_cancel_manufacturing_orders",
  "depends"              :  ['mrp'],
  "data"                 :  [
                             'security/security.xml',
                             'security/ir.model.access.csv',
                             'data/mail_templates.xml',
                             'data/production_cancel_reason_data.xml',
                             'wizard/mrp_production_cancel_view.xml',
                             'views/production_cancel_reason_view.xml',
                             'views/mrp_production_view.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  45,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}