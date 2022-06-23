{
    'name': 'QB Workorder Customizations',
    'description': """Modifies record rules for basic MO users 
        so that they can only create and view and not update nor delete them. 
        Adds checkbox to workcenter to denote 'quality' if checked, only allows
        quality user or admins to clock time.""",
    'sequence': 1,
    'version': '15,1.0.0',
    'author': 'Adam OConnor, Quickbeam LLC <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'mrp_workorder',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_views.xml',
    ],
    'application': True,
    'installable': True,
}
