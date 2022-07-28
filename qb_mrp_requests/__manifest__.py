{
    'name': 'QB MRP Request Customizations',
    'summary': """Customizes MRP Requests application.  Adds new stages, request lines from which multiple MOs can be made.
       Adds new fields to header such as program, subprogram and department. Adds all new fields to tree and search views.  Adds new buttons 
       that progress the MR to each of the new stages and marks the MR as done when all manufacturing orders are done.""",
    'sequence': 1,
    'version': '2',
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
