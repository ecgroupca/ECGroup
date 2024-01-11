# -*- coding: utf-8 -*-
##############################################################################
#
#    Global Creative Concepts Tech Co Ltd.
#    Copyright (C) 2018-TODAY iWesabe (<https://www.iwesabe.com>).
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Send Low Stock Alert To Inventory Manager",
    'summary': """Send Low Stock Alert To Inventory Manager""",
    'description': """
        This module is used to Send Low Stock Alert To Inventory Manager.
    """,
    'author': "iWesabe",
    'website': "https://www.iwesabe.com/",
    'license': 'AGPL-3',
    'category': 'Inventory/',
    'version': '14.0.1',

    'depends': ['stock'],

    'data': [
        'data/ir_cron.xml',
        'security/security.xml',
        'views/config_view.xml',
        'views/stock_location_view.xml',
    ],
    'images': ['static/description/banner.png'],

    'demo': [],

    'installable': True,
    'application': True,
    'auto_install': False,
    
}
