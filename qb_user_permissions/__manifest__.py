{
    'name': 'User Permissions Mods',
    'description': 'Adds group for Floor Sales and modifies the forms with that have product pricing.',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['sale','stock','product',
        'sale_mods_ecgroup','stock_picking_sale_order_link',
        'sale_margin',
        'qb_commissions_ecgroup'],
    'data': [
        'views/sale_views.xml',
        'views/stock_views.xml',
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}