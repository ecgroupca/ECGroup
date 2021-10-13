{
    'name': 'EC Group Sales Reports',
    'description': 'EC Group Open Sales Reports',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'sale_management',
        'stock',
        'delivery',
        'sale_mods_ecgroup',
        'sale_mrp_link',
        'sale_stock',
    ],
    'data': [
        #'views/sales_report_view.xml',
        'reports/report_sales.xml',
        'reports/report_template_sales.xml',
        'wizard/sales_report_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
}
