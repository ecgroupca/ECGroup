{
    'name': 'Update Transfer Locations',
    'description': 'Update transfer locations even after draft state and assign via onchange method, the source and destination to each Operation and Detailed Operation line.',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['stock','mrp','sale','sale_management'],
    'data': [
        'views/sale.xml',
        'views/mrp_views.xml',
        #'views/stock_views.xml'
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}