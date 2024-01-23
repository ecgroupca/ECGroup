{
    'name': 'Inventory Levels',
    'description': """Checks reorder points and sends out 
       notification email for all items that have
       available qty lower than min qty on orderpoint.""",
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam O\'Connor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['stock','product'],
    'data': [
        '/wizard/item_report_wizard_view.xml',
        '/reports/report_template_itemdetails.xml',
        ],
    'qweb': [],
    'application': True,
    'installable': True,
}