# -*- coding: utf-8 -*-
# (c) 2020 Quickbeam ERP
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Sale Modifications for EC Group',
    'version': '1.1',
    'author': 'Quickbeam ERP: Adam O\'Connor',
    'license': 'AGPL-3',
    'depends': ['sale'],
    'data': [
        'views/sale_views.xml',
        'views/partner_views.xml',
        'report/external_layout.xml',
        #'report/report_invoice_document.xml',
        'report/report_saleorder_document.xml',
    ],
    'installable': True,
    'application': True,
}
