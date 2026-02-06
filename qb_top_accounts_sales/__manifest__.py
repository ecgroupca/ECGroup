{
    'name': 'EC Group Top Accounts Sales Report',
    'description': 'EC Group Top Accounts Sales Report.',
    'sequence': 1,
    'version': '18.0.1',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'sale_management',
        'stock',
        'qb_transfer_locations',
        'sale_mods_ecgroup',
        'qb_opensales_reports',
    ],
    'data': [
        'reports/report_sales.xml',
        'reports/report_template_sales.xml',
        'wizard/sales_report_wizard_view.xml',
        
    ],
    'application': True,
    'installable': True,
}
