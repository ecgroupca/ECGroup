{
    'name': 'QB MRP Cancel',
    'description': """Cancel an MO and it cancels all of the pickings and provides a return for each of the done pickings.""",
    'sequence': 1,
    'version': '2',
    'author': 'Adam OConnor, Quickbeam LLC <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'mrp',
        ],
    'data': [
        'views/mrp_views.xml',
    ],
    'application': True,
    'installable': True,
}
