{
    'name': 'QB Sale Purchase Links',
    'description': 'Provides links from purchase to sales and vice versa as well as purchase to MOs.',
    'sequence': 1,
    'version': '13.3.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['sale_management','purchase'],
    'data': [
        'views/purchase_order.xml',
        'views/sale_order.xml'
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}