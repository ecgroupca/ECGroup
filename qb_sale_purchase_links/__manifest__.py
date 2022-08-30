{
    'name': 'QB Sale Purchase Links',
    'description': 'Provides links from purchase to sales and vice versa.',
    'sequence': 1,
    'version': '13.2.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['sale_management','purchase','qb_product_links'],
    'data': [
        'views/purchase_order.xml',
        'views/sale_order.xml'
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}