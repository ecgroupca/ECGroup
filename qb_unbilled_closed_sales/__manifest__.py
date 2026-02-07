{
    'name': 'EC Group Unbilled, Closed Sales',
    'description': 'EC Group Unbilled, Closed Sales Report.',
    'sequence': 1,
    'version': '1.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'sale_management',
        'stock',
        'sale_mrp_link',
        'qb_transfer_locations',
    ],
    'data': [
        'reports/report_sales.xml',
        'reports/report_template_sales.xml',
        'wizard/sales_report_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
}
