{
    'name': 'QB Purchase Requisition Mods',
    'description': """Adds a vendor field to purchase req lines 
    and when a PO is created, it will create one per vendor 
    and aggregate per product.""",
    'sequence': 1,
    'version': '15.1.0.0',
    'author': 'Adam OConnor, Quickbeam LLC <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'purchase_requisition',
        ],
    'data': [
        'views/purchase_requisition.xml',
    ],
    'application': True,
    'installable': True,
}
