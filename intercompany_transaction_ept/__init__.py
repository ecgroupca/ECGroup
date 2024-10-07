# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo.api import Environment, SUPERUSER_ID
from . import models
from . import report
from . import wizards

MULTI_COMPANY_RULES = {'stock.stock_warehouse_comp_rule': 'stock.group_stock_user',
                       'stock.stock_location_comp_rule': 'stock.group_stock_user',
                       'stock.stock_picking_type_rule': 'stock.group_stock_user'}


def uninstall_hook_update_rule(cursor, registry):
    """
    Method to execute at module uninstallation time.
    """
    env = Environment(cursor, SUPERUSER_ID, {})
    for rule_xml_id, group_xml_id in MULTI_COMPANY_RULES.items():
        rule = env.ref(rule_xml_id)
        group = env.ref(group_xml_id)
        if group in rule.groups:
            rule.write({'groups': [(3, group.id)]})


def post_init_update_rule(cursor, registry):
    """
    Method to execute right after module installation.
    """
    env = Environment(cursor, SUPERUSER_ID, {})
    for rule_xml_id, group_xml_id in MULTI_COMPANY_RULES.items():
        rule = env.ref(rule_xml_id)
        group = env.ref(group_xml_id)
        if rule and group:
            if group not in rule.groups:
                rule.write({'groups': [(4, group.id)]})
        # Makes company_id False in partners of companies.
        # Added by Maulik Barad.
        companies = env['res.company'].search([])
        companies.mapped('partner_id').write({'company_id': False})
