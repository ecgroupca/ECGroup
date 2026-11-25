from odoo import models


class StockValuationOnhandXlsx(models.AbstractModel):
    _name = 'report.stock_valuation_onhand.onhand_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Stock Valuation On-Hand XLSX Report'

    def generate_xlsx_report(self, workbook, data, wizards):
        # `data` is not used: the result set is built here, server-side,
        # instead of being posted back by the browser.
        for wizard in wizards:
            self._generate_sheet(workbook, wizard._prepare_report_values())

    def _generate_sheet(self, workbook, data):
        sheet = workbook.add_worksheet('On-Hand Valuation')

        groups = data.get('groups', [])
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
        fmt_group = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#DCE6F1', 'valign': 'vcenter',
        })
        fmt_sub_label = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'right', 'bg_color': '#EEF3F9',
        })
        fmt_sub_money = workbook.add_format({
            'bold': True, 'border': 1, 'num_format': '#,##0.00',
            'align': 'right', 'bg_color': '#EEF3F9',
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

        # ── Column headers (A=0 … Q=16) ─────────────────────────────────────────────────
        headers = [
            'Company',                   # A  0
            'Location',                  # B  1
            'Lot/Serial #',              # C  2
            'MO #',                      # D  3
            'PO #',                      # E  4
            'Reference',                 # F  5
            'Created By',                # G  6
            'Created On',                # H  7
            'Product',                   # I  8
            'Product Category',          # J  9
            'Stock Valuation Account',   # K  10
            'Qty On-Hand',               # L  11
            'UoM',                       # M  12
            'Unit Value',                # N  13
            'Total Value',               # O  14
            'Sales Price',               # P  15
            'Cost',                      # Q  16
        ]
        header_row = 4
        for col, label in enumerate(headers):
            sheet.write(header_row, col, label, fmt_header)

        # ── Data rows, grouped by location ──────────────────────────────────────
        # Each location gets a header row, its product rows (outline
        # level 1, so Excel's +/- buttons can collapse them) and a
        # subtotal row.
        row = header_row + 1
        last_col = len(headers) - 1
        for group in groups:
            sheet.merge_range(row, 0, row, last_col,
                              'Location: %s' % group['location'], fmt_group)
            row += 1
            for line in group['lines']:
                sheet.set_row(row, None, None, {'level': 1})
                sheet.write(row, 0,  line.get('company', ''),           fmt_text)
                sheet.write(row, 1,  line.get('location', ''),          fmt_text_wrap)
                sheet.write(row, 2,  line.get('lot_name', ''),          fmt_text_wrap)
                sheet.write(row, 3,  line.get('mo_numbers', ''),        fmt_text_wrap)
                sheet.write(row, 4,  line.get('po_numbers', ''),        fmt_text_wrap)
                sheet.write(row, 5,  line.get('reference', ''),         fmt_text)
                sheet.write(row, 6,  line.get('created_by', ''),        fmt_text)
                sheet.write(row, 7,  line.get('created_on', ''),        fmt_text)
                sheet.write(row, 8,  line.get('product', ''),           fmt_text_wrap)
                sheet.write(row, 9,  line.get('category', ''),          fmt_text)
                sheet.write(row, 10, line.get('valuation_account', ''), fmt_text_wrap)
                sheet.write_number(row, 11, line.get('qty', 0.0),        fmt_qty)
                sheet.write(row, 12, line.get('uom', ''),               fmt_text)
                sheet.write_number(row, 13, line.get('unit_cost', 0.0),  fmt_money)
                sheet.write_number(row, 14, line.get('total_value', 0.0),fmt_money)
                sheet.write_number(row, 15, line.get('sales_price', 0.0),fmt_money)
                sheet.write_number(row, 16, line.get('cost', 0.0),       fmt_money)
                row += 1
            sheet.merge_range(row, 0, row, 13,
                              'Total – %s' % group['location'], fmt_sub_label)
            sheet.write_number(row, 14, group['total_value'], fmt_sub_money)
            sheet.write(row, 15, '', fmt_sub_label)
            sheet.write(row, 16, '', fmt_sub_label)
            row += 1

        # ── Grand total row ────────────────────────────────────────────────────────────────
        sheet.merge_range(row, 0, row, 13, 'Grand Total', fmt_total_label)
        sheet.write_number(row, 14, grand_total, fmt_total_money)
        sheet.write(row, 15, '', fmt_total_label)
        sheet.write(row, 16, '', fmt_total_label)

        # ── Column widths ─────────────────────────────────────────────────────────────
        sheet.set_column(0,  0,  16)   # A  Company
        sheet.set_column(1,  1,  22)   # B  Location
        sheet.set_column(2,  2,  18)   # C  Lot/Serial #
        sheet.set_column(3,  3,  16)   # D  MO #
        sheet.set_column(4,  4,  16)   # E  PO #
        sheet.set_column(5,  5,  14)   # F  Reference
        sheet.set_column(6,  6,  16)   # G  Created By
        sheet.set_column(7,  7,  12)   # H  Created On
        sheet.set_column(8,  8,  30)   # I  Product
        sheet.set_column(9,  9,  20)   # J  Category
        sheet.set_column(10, 10, 28)   # K  Valuation Account
        sheet.set_column(11, 11, 12)   # L  Qty
        sheet.set_column(12, 12,  8)   # M  UoM
        sheet.set_column(13, 13, 14)   # N  Unit Value
        sheet.set_column(14, 14, 14)   # O  Total Value
        sheet.set_column(15, 15, 14)   # P  Sales Price
        sheet.set_column(16, 16, 14)   # Q  Cost

        sheet.outline_settings(True, False, True, False)  # subtotal row below detail
        sheet.freeze_panes(header_row + 1, 0)
