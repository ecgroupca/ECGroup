from odoo import models


class ReportStockValuationOnhand(models.AbstractModel):
    _name = 'report.stock_valuation_onhand.report_stock_valuation_onhand_template'
    _description = 'Stock Valuation On-Hand PDF Report'

    def _get_report_values(self, docids, data=None):
        # Build the report data server-side from the wizard record rather
        # than receiving it from the browser (large payloads fail with a
        # 500 in /report/download).
        wizards = self.env['stock.valuation.onhand.wizard'].browse(docids)
        wizards.ensure_one()
        return {
            'doc_ids': wizards.ids,
            'doc_model': 'stock.valuation.onhand.wizard',
            'docs': wizards,
            'data': wizards._prepare_report_values(),
        }
