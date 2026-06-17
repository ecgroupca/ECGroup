from odoo import models


class StockValuationOnhandXlsx(models.AbstractModel):
    _name = 'report.stock_valuation_onhand.onhand_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Stock Valuation On-Hand XLSX Report'

    def generate_xlsx_report(self, workbook, data, wizards):
        """
        wizards: recordset of stock.valuation.onhand.wizard (the object the
                 report action was called on).
        data:    dict passed in from action_print_report() containing the
                 already-computed report lines (same data used by the PDF).
        """
        for wizard in wizards:
            self._generate_sheet(workbook, data)

    def _generate_sheet(self, workbook, data):
        sheet = workbook.add_worksheet('On-Hand Valuation')

        groups = data.get('groups', [])
        date = data.get('date', '')
        company = data.get('company', '')
        grand_total = data.get('grand_total', 0.0)

        # ── Formats ────────────────────────────────────────────────────────
        fmt_title = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left',
        })
        fmt_subtitle = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'font_color': '#555555',
        })
        fmt_header = workbook.add_format({
            'bold': True,
            'font_color': '#FFFFFF',
            'bg_color': '#2C6496',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })
        fmt_group_header = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#DDE7EF',
            'border': 1,
            'valign': 'vcenter',
        })
        fmt_text = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
        })
        fmt_text_wrap = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'text_wrap': True,
        })
        fmt_qty = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.0000',
            'align': 'right',
            'valign': 'vcenter',
        })
        fmt_money = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
        })
        fmt_subtotal_label = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'right',
        })
        fmt_subtotal_money = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
        })
        fmt_total_label = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'right',
            'bg_color': '#F0F0F0',
        })
        fmt_total_money = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '#,##0.00',
            'align': 'right',
            'bg_color': '#F0F0F0',
        })

        # ── Title block ────────────────────────────────────────────────────
        sheet.write(0, 0, 'Inventory Valuation – On-Hand Stock', fmt_title)
        sheet.write(1, 0, 'Company: %s' % company, fmt_subtitle)
        sheet.write(2, 0, 'As of: %s' % date, fmt_subtitle)

        # ── Header row ─────────────────────────────────────────────────────
        headers = [
            'Company', 'Reference', 'Created By', 'Created On',
            'Product', 'Product Category', 'Stock Valuation Account',
            'Quantity', 'UoM', 'Unit Value', 'Total Value',
        ]
        header_row = 4
        for col, label in enumerate(headers):
            sheet.write(header_row, col, label, fmt_header)

        # ── Data rows, grouped by warehouse / parent stock location ─────────
        row = header_row + 1
        for group in groups:
            # Warehouse / parent stock location header row
            warehouse_label = '%s  (%s)' % (
                group.get('warehouse', ''), group.get('location', '')
            )
            sheet.merge_range(row, 0, row, 10, warehouse_label, fmt_group_header)
            row += 1

            for line in group.get('lines', []):
                sheet.write(row, 0, line.get('company', ''), fmt_text)
                sheet.write(row, 1, line.get('reference', ''), fmt_text)
                sheet.write(row, 2, line.get('created_by', ''), fmt_text)
                sheet.write(row, 3, line.get('created_on', ''), fmt_text)
                sheet.write(row, 4, line.get('product', ''), fmt_text_wrap)
                sheet.write(row, 5, line.get('category', ''), fmt_text)
                sheet.write(row, 6, line.get('valuation_account', ''), fmt_text_wrap)
                sheet.write_number(row, 7, line.get('qty', 0.0), fmt_qty)
                sheet.write(row, 8, line.get('uom', ''), fmt_text)
                sheet.write_number(row, 9, line.get('unit_cost', 0.0), fmt_money)
                sheet.write_number(row, 10, line.get('total_value', 0.0), fmt_money)
                row += 1

            # Warehouse subtotal row
            sheet.merge_range(
                row, 0, row, 9,
                'Subtotal – %s' % group.get('warehouse', ''),
                fmt_subtotal_label,
            )
            sheet.write_number(row, 10, group.get('subtotal', 0.0), fmt_subtotal_money)
            row += 1

        # ── Grand total row ────────────────────────────────────────────────
        sheet.merge_range(row, 0, row, 9, 'Grand Total', fmt_total_label)
        sheet.write_number(row, 10, grand_total, fmt_total_money)

        # ── Column widths ──────────────────────────────────────────────────
        sheet.set_column(0, 0, 16)   # Company
        sheet.set_column(1, 1, 14)   # Reference
        sheet.set_column(2, 2, 16)   # Created By
        sheet.set_column(3, 3, 12)   # Created On
        sheet.set_column(4, 4, 30)   # Product
        sheet.set_column(5, 5, 20)   # Category
        sheet.set_column(6, 6, 28)   # Valuation Account
        sheet.set_column(7, 7, 12)   # Quantity
        sheet.set_column(8, 8, 8)    # UoM
        sheet.set_column(9, 9, 14)   # Unit Value
        sheet.set_column(10, 10, 14)  # Total Value

        sheet.freeze_panes(header_row + 1, 0)
