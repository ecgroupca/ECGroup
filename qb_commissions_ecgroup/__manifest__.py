# -*- coding: utf-8 -*-
# (c) 2020 Quickbeam ERP
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Sale Commissions for EC Group',
    'version': '1.0',
    'author': 'Quickbeam ERP: Adam O\'Connor',
    'license': 'AGPL-3',
    'depends': ['sale','sale_mods_ecgroup','qb_opensales_reports','qb_transfer_locations'],
    'data': [
        'security/ir.model.access.csv',
        'views/commissions_views.xml',
        'views/product_views.xml',
        'wizard/commission_report_wizard_view.xml',
        'wizard/sale_commission_report.xml',
    ],
    'installable': True,
    'application': True,
}
