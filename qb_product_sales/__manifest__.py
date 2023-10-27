{
    'name': 'EC Group Product Sales Reports',
    'description': 'EC Group Product Sales Reports',
    'sequence': 1,
    'version': '1.5.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'sale_management',
        'stock',
        'delivery',
    ],
    'data': [
        'reports/report_sales.xml',
        'reports/report_template_sales.xml',
        'wizard/sales_report_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
}
