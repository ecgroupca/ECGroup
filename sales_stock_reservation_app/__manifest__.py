# -*- coding: utf-8 -*-

{
    "name": 'Odoo Sales Stock Reservation',
    "author": "Edge Technologies",
    "version": '13.0.1.0',
    "live_test_url": "https://youtu.be/ye8IkLcVZpA",
    "images":['static/description/main_screenshot.png'],
    "summary": "Sale reserve stock sale stock reserve sales stock email notification on stock reservation stock reservation email cancel stock reservation product reservation in sale order product Inventory Reservation Auto stock Reservation sales stock booking on sales",
    "description": """ 
                    reserve stock, reserve sales stock, email notification on stock reservation, stock reservation email,
                    stock reservation, cancel reserve stock, cancel stock reservation, stock reserved, cancelled stock,
                    reserved stock pivot view, reserved stock bar graph, reserved stock line chart, reserved stock pie chart
     stock booking
     lock stock
     Pre-Reservation
     Stock reservations
      
     sales stock boooking
     Sale Stock Reservation 
     book stock 
     book orders
     reserve products
     Products for Reservation
     Temporary product reservation
     Sales reservation              
Sales Stock Reservation
Stock Reservation on Sales Flow
reservation from Quotation
Stock reservation records
Reservation of Inventory
Inventory Reservation of 
Stock reservation against Sales order
Stock Material reservation
Stock reservations
stock availability
sales stock availability
reservation of stock
Reserve Stock
Auto stock Reservation

Odoo Stock Reservation

                    """,
    "license" : "OPL-1",
    "depends": ['base','sale_management','sale_stock'],
    "data": [
            'security/ir.model.access.csv',
            'data/ir_sequence_data.xml',
            'data/reserved_stock_email_template.xml',
            'wizard/reserve_stock_wizard_views.xml',
            'views/reserved_stock_view.xml',
            ],
    "installable": True,
    "auto_install": False,
    "price": 12,
    "currency": "EUR",
    "category": 'Sales',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: