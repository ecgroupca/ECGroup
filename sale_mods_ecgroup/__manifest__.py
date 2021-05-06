# -*- coding: utf-8 -*-
# (c) 2020 Quickbeam ERP
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Sale Modifications for EC Group',
    'version': '1.0',
    'author': 'Quickbeam ERP: Adam O\'Connor',
    'license': 'AGPL-3',
    'depends': ['sale','sale_stock','delivery','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
        'views/partner_views.xml',
        'views/commissions_views.xml',
        'wizard/commission_report_wizard_view.xml',
        'report/external_layout.xml',
        'views/product_views.xml',
        'report/report_saleorder_document.xml',
        'wizard/sale_commission_report.xml',
    ],
    'installable': True,
    'application': True,
}
