# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class Showroom(models.Model):
    _name = 'sale.showroom'
    _description = 'Showroom for commissions purposes.'

    name = fields.Char('Name')
    comm_rate = fields.Float('Commission Rate (%)')
