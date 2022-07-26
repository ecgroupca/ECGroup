# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd.
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Product Manufacturing Request',
    'currency': 'EUR',
    'license': 'Other proprietary',
    'price': 39.0,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'summary' : 'Allow you to create product manufacturing request',
    'support': 'contact@probuse.com',
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/manufacturing_production_request/841',#'https://youtu.be/H73gHbMec6I',
    'description': """
Manufacturing
Manufacturing 
Request
Product Manufacturing Request
Manufacturing Request
production request
mrp request

""",
    'images': ['static/description/img.jpg'],
    'version': '2.1.2',
    'category' : 'Manufacturing/Manufacturing',
    'depends': [
                'mrp',
                ],
    'data':[
        'data/manufacturing_order_request_sequence.xml',
        'security/ir.model.access.csv',
        'security/request_recorde_view.xml',
        'views/manufacturing_view.xml',
        'views/mrp_production_view.xml',
        'report/manufacturing_production_report.xml',
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:




