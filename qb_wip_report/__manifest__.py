{
    'name': 'EC Group WIP Reports',
    'description': 'EC Group Work in Progress Manufacturing Order Reports',
    'sequence': 1,
    'version': '1.0.0',
    'author': 'Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': [
        'sale_management',
        'stock',
        'delivery',
        'report_xlsx',
    ],
    'data': [
        #'views/templates.xml',
        #'views/wip_report_view.xml',
        'reports/report_template_wip.xml',
        'reports/report_wip.xml',
        'wizard/wip_report_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
}
