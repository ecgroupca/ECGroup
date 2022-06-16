# -*- coding: utf-8 -*-
{

    "name": "MRP Substitute Products",
    "summary": "Substitute MRP Products",
    "category": "Manufacturing",
    "version": "15.0.1",
    "sequence": 1,
    "author": "Brindsoft Technologies",
    "license": "AGPL-3",
    "website": "http://brindsoft.com",
    "depends": [
        'mrp',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/mrp_view.xml'
    ],
    "images": ['static/description/banner.png'],
    "price": 12,
    "currency": 'EUR',
    "application": False,
    "installable": True,
    "auto_install": False,

}
