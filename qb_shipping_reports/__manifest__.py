{
    'name': 'EC Group Shipping Reports',
    'description': 'EC Group Shipping Reports',
    'sequence': 1,
    'version': '15.1.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'sale_management',
        'stock',
        'delivery',
        'sale_mods_ecgroup'
    ],
    'data': [
        'views/shipping_report_view.xml',
        'reports/report_template_shipping.xml',
        'reports/report_shipping.xml',
        'wizard/shipping_report_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
}
