{
    'name': 'Shipping Reports',
    'description': 'Shipping Reports',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Sahil Navadiya <sahil.odoo@gmail.com>',
    'website': 'https://www.upwork.com/fl/sahilnavadiya',
    'depends': [
        'sale_management',
        'stock',
        'delivery',
    ],
    'data': [
        'views/shipping_report_view.xml',
        'reports/report_template_shipping.xml',
        'reports/report_shipping.xml'
    ],
    'application': True,
    'installable': True,
}
