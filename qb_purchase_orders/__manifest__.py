{
    'name': 'QB Modifications to Purchase Orders',
    'description': 'Modifies the functions and views for PO/RFQs.',
    'sequence': 1,
    'version': '13.1.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['purchase'],
    'data': [
        'views/purchase_order.xml',
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}