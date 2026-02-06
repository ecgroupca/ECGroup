{
    'name': 'QB Purchase Approvals',
    'description': 'QB Purchase Approvals',
    'sequence': 1,
    'version': '18.0.3',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'approvals_purchase',
    ],
    'data': [
        'views/approvals_purchase.xml',
        'views/purchase_views.xml',
        'views/account_move_views.xml',
    ],
    'application': True,
    'installable': True,
}
