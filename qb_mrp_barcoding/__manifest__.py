{
    'name': 'MRP Barcoding',
    'description': 'Extends Barcoding to Manufacturing and Workorders',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'category': 'Operations/Inventory',
    'depends': [
        'mrp',
        'stock_barcode',
    ],
    'data': [
        'views/mrp_barcoding_views.xml',  
        'data/data.xml',        
    ],
    'application': True,
    'installable': True,
}
