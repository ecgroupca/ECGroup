{
    'name': 'QB Quality Alerts',
    'description': """Adds quality alerts for items on MOs, POs and Approvals.
    Adds a badge on MOs and POs and Approvals that links to any quality alerts for items (not void)
    POs - items in PO lines
	MOs - either items in consumption lines or the item to be manufactured.
	Approvals - items on approval lines.
	
    Adds badge on Quality Alerts to link to any MOs, Approvals or POs (not done nor cancelled).""",
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam OConnor, Quickbeam LLC <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'quality_control',
        'mrp',
        'purchase',
        'approvals',
        ],
    'data': [
        'views/purchase_views.xml',
        'views/quality_views.xml',
        'views/mrp_views.xml',
        'views/approvals_views.xml',
    ],
    'application': True,
    'installable': True,
}
