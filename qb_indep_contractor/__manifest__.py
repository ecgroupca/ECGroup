# -*- coding: utf-8 -*-
# (c) 2026 Quickbeam ERP
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Independent Contractor Form and Report',
    'description': """
        Search and supporting field to mark Vendors that need 1099.
        Also maybe a report creation.
        Report - PDF - Vendor | Tax ID | Total Paid for the Year (1/1 - 12/31) | Billing Address*
           *first one in the list or the one used in invoices""",
    'version': '18.0.1',
    'author': 'Quickbeam ERP: Adam O\'Connor',
    'license': 'AGPL-3',
    'depends': ['base','account','purchase'],
    'data': [
        #'security/ir.model.access.csv',
        'views/partner_views.xml',
        'wizard/contractor_report_wizard_view.xml',
        'reports/indep_contractor_report.xml',        
    ],
    'installable': True,
    'application': True,
}
