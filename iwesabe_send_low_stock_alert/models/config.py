# -*- coding: utf-8 -*-

from odoo import fields,api,models,_

class ResCompany(models.Model):
	_inherit = 'res.company'
	
	low_stock_alert_qty = fields.Float('')

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	low_stock_alert_qty = fields.Float(related="company_id.low_stock_alert_qty", store=True, readonly=False)