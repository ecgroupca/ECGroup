# -*- coding: utf-8 -*-
# Quickbeam ERP 2020

{
  'name': "Sales Commissions ECGroup",

  'summary': """
  Sales commissions as % rate on sale order line and reporting.""",
  'author': "Quickbeam",
  'description': """
Sales Commissions
=============================

Store commission rates on customers and when that customer is added to a sale order, any existing order lines get the commission rate populated and calculated as a subtotal line-by-line as well as a commission total at the order level.

Key Features
------------
* Record commission % on sale order lines and edit them as necessary.
* 
* Integration with the stock moves
* Automatic creation of sales order and invoices

  """,

  # Categories can be used to filter modules in modules listing
  # for the full list
  'category': 'Sales',
  'version': '1.0',

  # any module necessary for this one to work correctly
  'depends': ['base', 'sale_management'],

  # always loaded
  'data': [
      'security/ir.model.access.csv',
      'security/sale_ebay_security.xml',
      'views/res_partner_views.xml',
  ],
  # only loaded in demonstration mode
  'demo': [
  ],
  'js': ['static/src/js/*.js'],
  'css': ['static/src/css/*.css'],
  'qweb': ['static/src/xml/*.xml'],
  'application': False,
    'license': 'OEEL-1',
}
