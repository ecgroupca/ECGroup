{
    'name': 'QB Purchase Approvals',
    'description': 'QB Purchase Approvals',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'approvals_purchase',
    ],
    'data': [
        'views/approvals_purchase.xml',
        'views/purchase_views',
    ],
    'application': True,
    'installable': True,
}
