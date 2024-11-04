{
    'name': 'EC Group Sales Taxes to Lines',
    'description': 'EC Group Sales Tax on Header to Sales Lines.',
    'sequence': 1,
    'version': '16.0.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'sale',
        'sale_management',
        # 'qb_transfer_locations',
    ],
    'data': [
        'views/sales_views.xml',
    ],
    'application': True,
    'installable': True,
}
