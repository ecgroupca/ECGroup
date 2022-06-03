# Copyright © 2022 Novobi, LLC
# See LICENSE file for full copyright and licensing details.
{
    'name': 'FIREFLY Custom Template',
    'version': '15.0.1',
    'category': 'Customizations',
    'license': 'OPL-1',
    'author': 'Novobi LLC',
    'website': 'https://www.novobi.com',
    'summary': """
        Custom email and PDF template for Firefly's PO
    """,
    'description': """
    """,

    'depends': [
        # Odoo native addons
        'account_accountant',
        'purchase',
        'purchase_stock',
        'stock',
        'purchase_requisition'
    ],

    'data': [

        # ============================================================
        # SECURITY SETTING - GROUP
        # ============================================================
        # 'security/'

        # ============================================================
        # DATA
        # ============================================================
        'data/mail_template_data.xml',

        # ============================================================
        # VIEWS
        # ============================================================
        'reports/report_paperformat.xml',
        'reports/report_purchaseorder.xml',
        'reports/reports.xml',
        'views/custom_purchase_order_form.xml'
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
