# Copyright 2023 Quickbeam, LLC - Adam O'Connor <aoconnor@quickbeamllc.com>  
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "ACH Payments",
    "version": "13.0.2.0.1",
    "summary": """Extends account payment view to include routing # and account # and other ACH Details. 
    Sends ACH payments to Wells Fargo.""",
    "author": "Adam OConnor, Quickbeam ERP",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_payment.xml",
        "wizard/report_pmt_wizard_view.xml",
        "wizard/ach_pmt_wizard_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "auto_install": False,
}
