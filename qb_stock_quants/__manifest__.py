{
    'name': 'Stock Quants Customization',
    'description': 'Update Qty Mods.',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['stock','product'],
    'data': [
        'views/stock_views.xml',
        'views/product_views.xml',
        'security/security.xml',
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}