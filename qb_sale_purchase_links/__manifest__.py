{
    'name': 'QB Sale Purchase Linkds',
    'description': 'Provides links from purchase to sales and vice versa.',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['stock','product'],
    'data': [
        'views/purchase_views.xml',
        'views/sale_order.xml'
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}