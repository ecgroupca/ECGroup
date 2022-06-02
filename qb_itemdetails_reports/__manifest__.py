{
    'name': 'EC Group Item Details Reports',
    'description': 'EC Group Item Details Reports',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'stock',
        'report_xlsx',
        'qb_stock_quants',
    ],
    'data': [
        'reports/report_template_itemdetails.xml',
        'wizard/item_report_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
}
