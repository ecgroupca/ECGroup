# -*- coding: utf-8 -*-
{
    'name': 'Inventory Adjustment XLSX Import',
    'version': '16.0.1.1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Create a draft inventory adjustment (physical inventory count) from an XLSX file',
    'description': """
Upload an .xlsx file with the columns
Part Number (default_code) | Location | Lot/Serial Number | Quantity
and a draft inventory adjustment is created for it: the quantities are loaded as
"Counted Quantity" on Inventory > Operations > Physical Inventory and nothing is
applied to stock until someone clicks "Apply". Every upload is kept in a separate list
(Inventory > Operations > Import Inventory (XLSX)) with an Upload button in its header.
    """,
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'external_dependencies': {'python': ['openpyxl']},
    'data': [
        'security/ir.model.access.csv',
        'security/stock_inventory_xlsx_batch_security.xml',
        'data/ir_sequence_data.xml',
        'views/stock_inventory_xlsx_import_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_inventory_xlsx_import/static/src/js/stock_inventory_xlsx_batch_list.js',
            'stock_inventory_xlsx_import/static/src/xml/stock_inventory_xlsx_batch_list.xml',
        ],
    },
    'installable': True,
    'application': False,
}
