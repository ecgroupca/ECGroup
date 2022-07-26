{
    'name': 'QB MRP Request Customizations',
    'description': """Adds stages to MRP Request Custom model.""",
    'sequence': 1,
    'version': '15.1.0.1',
    'author': 'Adam OConnor, Quickbeam LLC <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'manufacturing_production_request',
        'hr',
        ],
    'data': [
        'views/mrp_req.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
    'installable': True,
}
