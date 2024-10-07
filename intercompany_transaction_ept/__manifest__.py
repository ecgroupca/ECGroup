{
    # App information
    'name': 'Inter Company Transfer and Warehouse',
    'version': '16.0.1.0.2',
    'category': 'Operations/Inventory',
    'license': 'OPL-1',
    'summary': 'Manages Inter Company and Inter Warehouse Transfer along with all required documents with the easiest way by just simple configurations.Customer will get easy interface to exchange stock as well as to return stock.Emipro is also having integration for well known ecommerce solutions or applications named as Woocommerce connector , Shopify connector , magento connector and also we have solutions for Marketplace Integration such as Odoo Amazon connector , Odoo eBay connector , Odoo walmart Connector , Odoo Bol.com connector.Aside from ecommerce integration and ecommerce marketplace integration, we also provide solutions for various operations, such as shipping , logistics , shipping labels , and shipping carrier management with our shipping integration , known as the Shipstation connector.For the customers who are into Dropship business, we do provide EDI Integration that can help them manage their Dropshipping business with our Dropshipping integration or Dropshipper integration It is listed as Dropshipping EDI integration and Dropshipper EDI integration.Emipro applications can be searched with different keywords like Amazon integration , Shopify integration , Woocommerce integration, Magento integration , Amazon vendor center module , Amazon seller center module , Inter company transfer , eBay integration , Bol.com integration , inventory management , warehouse transfer module , dropship and dropshipper integration and other Odoo integration application or module',

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Dependencies
    'depends': ['delivery', 'purchase_stock', 'barcodes'],
    'external_dependencies': {'python': ['xlrd']},
    'data': [
        #'data/ir_sequence.xml',
        #'data/ir_cron.xml',

        'security/inter_company_transfer_security.xml',
        'security/ir.model.access.csv',

        'wizards/reverse_inter_company_transfer_ept.xml',
        'wizards/import_export_products_ept.xml',

        'views/inter_company_transfer_ept.xml',
        'views/inter_company_transfer_config_ept.xml',
        'views/inter_company_transfer_log_line_ept.xml',
        'views/account_move.xml',
        'views/purchase.xml',
        'views/res_company.xml',
        'views/sale.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
    ],

    # Odoo Store Specific
    'images': ['static/description/Inter-Company-Transfer.jpg'],

    # Technical
    'post_init_hook': 'post_init_update_rule',
    'uninstall_hook': 'uninstall_hook_update_rule',
    'live_test_url': 'https://www.emiprotechnologies.com/r/4uC',
    'active': True,
    'installable': True,
    'currency': 'EUR',
    'price': 149.00,
    'auto_install': False,
    'application': True,
}
