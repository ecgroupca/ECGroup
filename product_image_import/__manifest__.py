# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<https://www.kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.kanakinfosystems.com/license>
#################################################################################

{
    'name': 'Product Image Import',
    'version': '1.0',
    'summary': 'Allows Product Image import in bulk using reference numbers',
    'description': """
    Import Product Images
    """,
    'category': 'Product',
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'images': ['static/description/main_image.jpg'],
    'depends': ['product', 'stock'],
    'data': [
        'wizard/import_view.xml',
    ],
    'sequence': 1,
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 20,
    'currency': 'EUR'
}
