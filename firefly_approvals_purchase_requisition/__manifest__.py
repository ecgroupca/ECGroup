# Copyright © 2022 Novobi, LLC
# See LICENSE file for full copyright and licensing details.
{
    'name': 'FIREFLY Purchase Agreements',
    'version': '15.0.1',
    'category': 'Customizations',
    'license': 'OPL-1',
    'author': 'Novobi LLC',
    'website': 'https://www.novobi.com',
    'summary': """
        Approvals customizations for Firefly to get approvals to create a purchase agreement
    """,
    'description': """
    """,

    'depends': [
        # Odoo native addons
        'approvals_purchase',
        'purchase_requisition',
        'account_accountant',
        'analytic',
        'firefly_custom_template',
    ],

    'data': [

        # ============================================================
        # SECURITY SETTING - GROUP
        # ============================================================
        # 'security/',

        # ============================================================
        # DATA
        # ============================================================
        'data/approval_category_data.xml',
        'data/mail_data.xml',

        # ============================================================
        # VIEWS
        # ============================================================
        'views/approval_category_views.xml',
        'views/approval_product_line_views.xml',
        'views/approval_request_views.xml',

    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
