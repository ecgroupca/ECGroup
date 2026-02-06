{
    'name': "Parallel Routing Steps",
    'version': '18.0.1',
    'author': "Jake Robinson",
    'website': "https://programmedbyjake.com",
    'category': 'Manufacturing',
    'summary': "Multiple Active Work Orders per Manufacturing Order",
    'description': """Increase productivity with parallel routing for manufacturing.
        This allows multiple work orders to be active at once for each manufacturing order.""",
    'depends': [
        'base',
        'mrp',
    ],
    'data': [
        #'views/mrp_routing.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'application': False,
    'installable': True,

    'license': 'OPL-1',
    'price': 100,
    'currency': 'EUR',
    'support': 'support@programmedbyjake.com',
}
