{
    'name': 'Stock Valuation On-Hand Report',
    'version': '16.0.1.0.0',
    'summary': 'Inventory Valuation Report based on On-Hand Quantity at a given date',
    'description': """
        Generates an inventory valuation report showing the value of on-hand stock
        as of a user-specified date. Excludes historical in/out transactions that
        have already been shipped or sold.
    """,
    'category': 'Inventory/Reporting',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>, Quickbeam ERP ',
    'depends': ['stock', 'stock_account', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_valuation_onhand_wizard_views.xml',
        #'reports/stock_valuation_onhand_report_template.xml',
        #'reports/stock_valuation_onhand_report.xml',
        'views/stock_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
