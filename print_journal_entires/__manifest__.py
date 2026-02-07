# Copyright (C) 2026 - Quickbeam ERP, Adam O'Connor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Print Journal Entries',
    'version': '1.0',
    'category': 'account',
    'summary': 'Print Journal Entry',
    'description': """
    this module use for print journal Entries in PDF report"
    """,
    'author': "Quickbeam ERP",
    'depends': ['account'],
    'license': 'AGPL-3',
    'data': [
            'report/report_menu.xml'
            ],

    'demo': [],
    "images": [
        'static/description/icon.png'
    ],
    'price': 00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
