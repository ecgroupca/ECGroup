# Copyright 2018 Alex Comba - Agile Business Group
# Copyright 2016-2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Sale MRP Link',
    'summary': 'Show manufacturing orders generated from sales order',
    'version': '12.0.1.0.1',
    'development_status': 'Production/Stable',
    'category': 'Sales Management',
    'website': 'https://github.com/OCA/sale-workflow',
    'author': 'Akretion, Agile Business Group, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'sale_mrp',
        'purchase',
    ],
    'data': [
        'views/mrp_production.xml',
        'views/sale_order.xml',
        'report/report_mrp_document.xml',
    ],
}
