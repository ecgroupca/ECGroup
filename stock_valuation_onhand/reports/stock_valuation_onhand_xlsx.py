from odoo import models


class StockValuationOnhandXlsx(models.AbstractModel):
    _name = 'report.stock_valuation_onhand.onhand_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Stock Valuation On-Hand XLSX Report'

    def generate_xlsx_report(self, workbook, data, wizards):
        for wizard in wizards:
            self._generate_sheet(workbook, data)

    def _generate_sheet(self, workbook, data):
        sheet = workbook.add_worksheet('On-Hand Valuation')

        lines = data.get('lines', [])
        date = data.get('date', '')
        company = data.get('company', '')
        grand_total = data.get('grand_total', 0.0)

        # ── Formats ────────────────────────────────────────────────────────
        fmt_title = workbook.add_format({'bold': True, 'font_size': 14})
        fmt_subtitle = workbook.add_format({'italic': True, 'font_size': 10, 'font_color': '#555555'})
        fmt_header = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#2C6496',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
        })
        fmt_text = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        fmt_text_wrap = workbook.add_format({'border': 1, 'valign': 'vcenter', 'text_wrap': True})
        fmt_qty = workbook.add_format({
            'border': 1, 'num_format': '#,##0.0000', 'align': 'right', 'valign': 'vcenter',
        })
        fmt_money = workbook.add_format({
            'border': 1, 'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter',
        })
        fmt_total_label = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'right', 'bg_color': '#F0F0F0',
        })
        fmt_total_money = workbook.add_format({
            'bold': True, 'border': 1, 'num_format': '#,##0.00',
            'align': 'right', 'bg_color': '#F0F0F0',
        })

        # ── Title block ─────────────────────────────────────────────────────
        sheet.write(0, 0, 'Inventory Valuation – On-Hand Stock', fmt_title)
        sheet.write(1, 0, 'Company: %s' % company, fmt_subtitle)
        sheet.write(2, 0, 'As of: %s' % date, fmt_subtitle)

        # ── Column headers (A=0 … O=14) ─────────────────────────────────────
        headers = [
            'Company',                   # A  0
            'Location',                  # B  1
            'PO #',                      # C  2
            'Reference',                 # D  3
            'Created By',                # E  4
            'Created On',                # F  5
            'Product',                   # G  6
            'Product Category',          # H  7
            'Stock Valuation Account',   # I  8
            'Qty On-Hand',               # J  9
            'UoM',                       # K  10
            'Unit Value',                # L  11
            'Total Value',               # M  12
            'Sales Price',               # N  13
            'Cost',                      # O  14
        ]
        header_row = 4
        for col, label in enumerate(headers):
            sheet.write(header_row, col, label, fmt_header)

        # ── Data rows ───────────────────────────────────────────────────────
        row = header_row + 1
        for line in lines:
            sheet.write(row, 0,  line.get('company', ''),           fmt_text)
            sheet.write(row, 1,  line.get('location', ''),          fmt_text_wrap)
            sheet.write(row, 2,  line.get('po_numbers', ''),        fmt_text_wrap)
            sheet.write(row, 3,  line.get('reference', ''),         fmt_text)
            sheet.write(row, 4,  line.get('created_by', ''),        fmt_text)
            sheet.write(row, 5,  line.get('created_on', ''),        fmt_text)
            sheet.write(row, 6,  line.get('product', ''),           fmt_text_wrap)
            sheet.write(row, 7,  line.get('category', ''),          fmt_text)
            sheet.write(row, 8,  line.get('valuation_account', ''), fmt_text_wrap)
            sheet.write_number(row, 9,  line.get('qty', 0.0),        fmt_qty)
            sheet.write(row, 10, line.get('uom', ''),               fmt_text)
            sheet.write_number(row, 11, line.get('unit_cost', 0.0),  fmt_money)
            sheet.write_number(row, 12, line.get('total_value', 0.0),fmt_money)
            sheet.write_number(row, 13, line.get('sales_price', 0.0),fmt_money)
            sheet.write_number(row, 14, line.get('cost', 0.0),       fmt_money)
            row += 1

        # ── Grand total row ─────────────────────────────────────────────────
        sheet.merge_range(row, 0, row, 11, 'Grand Total', fmt_total_label)
        sheet.write_number(row, 12, grand_total, fmt_total_money)
        sheet.write(row, 13, '', fmt_total_label)
        sheet.write(row, 14, '', fmt_total_label)

        # ── Column widths ───────────────────────────────────────────────────
        sheet.set_column(0,  0,  16)   # A  Company
        sheet.set_column(1,  1,  22)   # B  Location
        sheet.set_column(2,  2,  16)   # C  PO #
        sheet.set_column(3,  3,  14)   # D  Reference
        sheet.set_column(4,  4,  16)   # E  Created By
        sheet.set_column(5,  5,  12)   # F  Created On
        sheet.set_column(6,  6,  30)   # G  Product
        sheet.set_column(7,  7,  20)   # H  Category
        sheet.set_column(8,  8,  28)   # I  Valuation Account
        sheet.set_column(9,  9,  12)   # J  Qty
        sheet.set_column(10, 10,  8)   # K  UoM
        sheet.set_column(11, 11, 14)   # L  Unit Value
        sheet.set_column(12, 12, 14)   # M  Total Value
        sheet.set_column(13, 13, 14)   # N  Sales Price
        sheet.set_column(14, 14, 14)   # O  Cost

        sheet.freeze_panes(header_row + 1, 0)
