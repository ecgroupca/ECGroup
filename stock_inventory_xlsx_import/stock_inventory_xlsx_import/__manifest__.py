# -*- coding: utf-8 -*-
{
    'name': 'Inventory Adjustment XLSX Import',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Create a draft inventory adjustment (physical inventory count) from an XLSX file',
    'description': """
Upload an .xlsx file with the columns
Part Number (default_code) | Location | Lot/Serial Number | Quantity
and a draft inventory adjustment is created for it: the quantities are loaded as
"Counted Quantity" on Inventory > Operations > Physical Inventory and nothing is
applied to stock until someone clicks "Apply".
    """,
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'external_dependencies': {'python': ['openpyxl']},
    'data': [
        'views/stock_inventory_xlsx_import_views.xml',
    ],
    'installable': True,
    'application': False,
}
