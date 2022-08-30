{
    'name': 'QB Product Links',
    'description': """Adds a purchase button and an MO button on the product form for link to all POs and MOs for the item.""",
    'sequence': 1,
    'version': '15,1.0.0',
    'author': 'Adam OConnor, Quickbeam LLC <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'product',
        'purchase',
        'mrp',
        'sale',
        ],
    'data': [
        'views/mrp_views.xml',
    ],
    'application': True,
    'installable': True,
}
