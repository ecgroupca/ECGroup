{
    # App information
    'name': 'Inter Company Transfer and Warehouse Transfer',
    'version': '13.0.1.0',
    'category': 'Operations/Inventory',
    'license': 'OPL-1',
    'summary' : 'Manages Inter Company and Inter Warehouse Transfer.',
    'description':"""
        Module to manage Inter Company Transfer and Inter Warehouse Transfer along with all required documents with easiest way by just simple configurations.
        """,

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Dependencies
    'depends': ['delivery', 'purchase_stock', 'barcodes'],
    'data': [
        #'data/ir_sequence.xml',
        #'data/inter_company_transfer_config.xml',

        #'views/inter_company_transfer_ept.xml',
        #'views/inter_company_transfer_config_ept.xml',
        #'views/res_company.xml',
        #'views/sale.xml',
        #'views/purchase.xml',
        #'views/stock_picking.xml',
        #'views/account_move.xml',
        #'views/inter_company_transfer_log_book_ept.xml',

        #'security/inter_company_transfer_security.xml',
        #'security/ir.model.access.csv',

        #'wizards/reverse_inter_company_transfer_ept.xml',
        #'wizards/import_export_products_ept.xml',

        ],

    # Odoo Store Specific
    'images': ['static/description/Inter-Company-Transfer-cover.jpg'],

    # Technical
    'post_init_hook': 'post_init_update_rule',
    'uninstall_hook': 'uninstall_hook_update_rule',
    'live_test_url': 'https://www.emiprotechnologies.com/free-trial?app=inter-company-transfer-ept&version=13&edition=enterprise',
    'active': True,
    'installable': True,
    'currency': 'EUR',
    'price': 149.00,
    'auto_install': False,
    'application': True,
}
