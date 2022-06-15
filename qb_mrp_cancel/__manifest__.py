{
    'name': 'QB MRP Cancel',
    'description': """Cancel an MO and it cancels all of the pickings.""",
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam OConnor, Quickbeam LLC <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'mrp',
        ],
    'data': [
        'wizard/mrp_returns_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
}
