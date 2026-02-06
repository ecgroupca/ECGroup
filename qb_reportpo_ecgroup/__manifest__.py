{
    'name': 'Vendor PO Report',
    'description': 'Vendor PO Report',
    'sequence': 1,
    'version': '18.0.1',
    'author': 'Quickbeam ERP: Sahil Navadiya <nsahil@quickbeamllc.com>, Adam OConnor <aoconnor@quickbeamllc.com>',
    'website': 'https://quickbeamllc.com',
    'depends': ['purchase','report_xlsx'],
    'data': [
        'reports/report_template_open_po.xml',
        'reports/report_po.xml',
        'wizard/po_report_wizard_view.xml',
    ],
    'qweb': [],
    'application': True,
    'installable': True,
}
