# Copyright 2026 Quickbeam, LLC - Adam O'Connor <aoconnor@quickbeamllc.com>  
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Checkbook Register",
    "version": "18.0.2",
    "summary": "Extends account payment view to include routing # and account #, a special tree view with register as well as pdf report.",
    "author": "Adam OConnor, Quickbeam ERP",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": ["account","account_check_printing","l10n_us"],
    "data": [
        "views/account_payment.xml",
        "report/report_checkbook_register.xml",
        "wizard/checkbook_report_wizard_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
