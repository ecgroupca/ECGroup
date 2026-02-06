# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Odoo Barcode Labels for All(Products,Templates,Sale,Purchase,Picking)",
    "version" : "18.0.8",
    "category" : "Sales",
    'summary': 'All in one Barcode Labels Product Template barcode label for product barcode label for sale barcode label for purchase barcode label for picking barcode label print Dynamic Barcode Label print product labels print label from sales order print barcode label',
    "description": """
    odoo Print Dynamic Barcode Labels From
    odoo barcode labels for Products odoo
    odoo barcode labels for Product Templates odoo
    odoo barcode labels for Sales order odoo
    odoo barcode labels for Purchase orders odoo
    odoo barcode labels for srock Picking odoo
    odoo BarCode Printing using Label Printer odoo
    odoo Print Dynamic Barcode Labels for Products Templates Sale Purchase Picking
    odoo Print Dynamic Barcode Labels for Templates Sales order Purchase order Picking Print Dynamic Barcode Labels for Sale,Purchase,Picking
    odoo Print Dynamic Barcode Labels for sales order Print Dynamic Barcode Labels for Picking
    odoo Print Dynamic Barcode Labels for purchase order Print Dynamic Barcode Labels for Picking
    odoo barcode label for products Dynamic Barcode Labels for Products,Templates,Sale,Purchase,Picking
    odoo Dynamic Barcode Labels for Picking Dynamic Barcode Labels for Sale,Purchase,Picking
    odoo print product barcode labels product barcode labels odoo barcode label for serial number
    odoo print picking barcode labels picking barcode labels
    odoo print sale barcode labels sale barcode labels
    odoo print sale barcode labels barcode product labels
    odoo printing barcode labels Odoo Dynamic Barcode Labels for All(Products,Templates,Sale,Purchase,Picking) 
    odoo Barcode Labels print barcode labels print multiple barcode labels print quantity barcode labels print
    odoo picking labels picking barcode labels
    odoo product labels barcode for all product barcode labels
This Odoo app module helps to print all sort dynamic barcode labels from Products Templates Sale Purchase 
and Pickings for printing barcode in Odoo.
This Odoo apps helps to generate label according to each companies  specification each company has its own label size standard here with this help user can have option for 
customized label size template feature which is one time configurable. Based on configure barcode label height 
and width barcode label prints from Products Variants ,Product Templates,Sales Orders,Purchase Orders and Picking. 
Also it has most useful features to print multiple labels as per the quantity allocated on Orders or on Print section.

Barcode Labels for Products,Templates,Sale,Purchase,Picking

    odoo Dynamic Product Label Print Dynamic Barcode Label Print Dynamic Product Barcode Label Print
    odoo Dynamic Barcode Product Label Print odoo print Product Label print Barcode Label Print
    odoo print Product Barcode Label print Barcode Product Label print product small label print
    odoo print product dynamic Label print dyanamic product label print product label dynamic
    odoo Product Label Print barcode Dynamic Product Label Print barcode Product Label Print
    odoo barcode Label Print Product Label Print odoo
    odoo Barcode print Based Print All Product label and barcode print
    odoo Print Number of label Product Barcodes and Label Printing
    odoo Barcode labels Printing Barcodes
    odoo Barcode Products Barcode Labels Product and Barcode Labeling
    odoo Label Printing odoo print barcode labels for products odoo Product label printing with barcode


                """,
    "author": "BROWSEINFO",
    "website" : "https://www.browseinfo.com/demo-request?app=bi_dynamic_barcode_labels&version=16&edition=Community",
    'price': 25,
    "currency": 'EUR',
    "depends" : ['base','web','sale_management','stock','purchase'],
    "data": [
        'security/ir.model.access.csv',
        'data/barcode_config_data.xml',
        'views/barcode_config_views.xml',
        'report/report_barcode_product_labels_temp.xml',
        'report/report_barcode_product_temp_labels.xml',
        'report/report_barcode_sale_labels.xml',
        'report/report_barcode_purchase_labels.xml',
        'report/report_barcode_stock_labels.xml',
        'report/report_barcode_mrp_labels.xml',
        'report/report.xml',
        'wizard/barcode_product_labels_view.xml',
        'wizard/barcode_product_temp_labels_view.xml',
        'wizard/barcode_sales_labels_view.xml',
        'wizard/barcode_purchase_labels_view.xml',
        'wizard/barcode_stock_labels_view.xml',
        'wizard/barcode_mrp_labels_view.xml',
         ],
    "license":'OPL-1',
    "auto_install": False,
    "installable": True,
    'live_test_url' :'https://www.browseinfo.com/demo-request?app=bi_dynamic_barcode_labels&version=16&edition=Community',
    "images":['static/description/Banner.gif'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
