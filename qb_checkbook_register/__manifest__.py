# Copyright 2021 Quickbeam, LLC - Adam O'Connor <aoconnor@quickbeamllc.com>  
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Checkbook Register",
    "version": "13.0.1.0.1",
    "summary": "Extends account payment view to include routing # and account #, a special tree view with register as well as pdf report.",
    "author": "Adam OConnor, Quickbeam ERP",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": ["account","account_check_printing"],
    "data": [
        "views/account_payment.xml",
        "report/report_checkbook_register.xml",
    ],
    "installable": True,
    "auto_install": False,
}
