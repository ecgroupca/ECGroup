# -*- coding: utf-8 -*-
"""
For inter_company_transfer_ept module.
"""
import base64
import csv
from csv import DictWriter
from io import StringIO, BytesIO
import xlrd

from odoo import models, fields, api
from odoo.exceptions import Warning

try:
    import xlwt
except ImportError:
    xlwt = None


class ImportExportProducts(models.TransientModel):
    """
    Model for importing and exporting products to/from ICT.
    @author: Maulik Barad on Date 04-Oct-2019.
    """
    _name = "import.export.products.ept"
    _description = 'Import Export Products'

    file = fields.Binary("Select File")
    datas = fields.Binary('File')
    file_name = fields.Char()

    report_type = fields.Selection(selection=[('csv', 'CSV'), ('xls', 'Xls')], default='xls', 
        string='Report Type',ondelete={'xls': 'set_default', 'csv': 'set_default'},required=True)
    file_delimiter = fields.Selection([(',', ',')], default=",", string="Delimiter",
                                      help="Select a delimiter to process CSV file.",
                                      ondelete={',': 'set_default'})
    update_existing = fields.Boolean("Do you want to update existing record?")
    # Updated by Udit on 18th December 2019
    update_existing_by = fields.Selection([('add', 'Add quantity to existing'),
                                           ('replace', 'Replace with file quantity')],
                                           default="add",
                                           ondelete={'add': 'set_default', 'replace': 'set_default'},)
    # replace_product_qty = fields.Boolean("Do you want to replace product quantity?",
    #                                      help="If you select this option then it will replace "
    #                                      "product quantity by csv quantity field data, it will not "
    #                                      "perform addition like 2 quantity is there in line and "
    #                                      "csv contain 3,then it will replace 2 by 3, it won't be "
    #                                      "updated by 5.If you have not selected this option then "
    #                                      "it will increase (addition) line quantity with csv "
    #                                      "quantity field data like 2 quantity in line and csv have "
    #                                      "3 quantity then it will update line with 5 quantity.")

    def import_product_list(self):
        """
        imports products from the uploaded file as XML or CSV.
        @author: Maulik Barad on Date 04-Oct-2019.
        """
        ict_log_obj = self.env['inter.company.transfer.log.book.ept']

        if not self.file:
            raise Warning('Unable to process..! Please select file to process...')

        # Checks file extension for the format of file.
        file_name = self.file_name
        index = file_name.rfind('.')
        flag = 0
        if index == -1:
            flag = 1
        extension = file_name[index + 1:]

        if flag or extension not in ['csv', 'xls', 'xlsx']:
            raise Warning("""Incorrect file format found..! Please provide only .csv or
            .xls file format to import data!!!""")

        # Checks ICT's state and calls import method as per file type.
        inter_company_transfer_id = self.env['inter.company.transfer.ept'].browse(
            self._context.get('active_id', False))
        if inter_company_transfer_id:
            log_book = ict_log_obj.return_log_record(inter_company_transfer_id,
                                                     operation_type="import")
            if inter_company_transfer_id.state not in ['draft']:
                raise Warning('The record is not in draft state.')

            if self.report_type == 'csv':
                self.import_products_from_csv(inter_company_transfer_id, log_book)

            elif self.report_type == 'xls':
                self.import_products_from_xls(inter_company_transfer_id, log_book)

        if not log_book.ict_log_line_ids:
            # Updated by Udit on 18th December 2019 (Added sudo)
            log_book.sudo().unlink()
        return True

    def import_products_from_csv(self, ict, log_book):
        """
        Imports products from a csv file to an ICT as transfer lines.
        @author: Maulik Barad on Date 07-Oct-2019.
        @param ict: Record of inter company transfer.
        @param log_book: Record of log book.
        """
        # Updated by Udit on 18th December 2019 (Taken required from xml)
        # if not self.file_delimiter:
        #     raise Warning('Unable to process..! Please select File Delimiter...')

        self.write({'datas':self.file})
        self._cr.commit()

        import_file = BytesIO(base64.decodebytes(self.datas))
        csvf = StringIO(import_file.read().decode())
        # Updated by Udit on 18th December 2019 (Removed static ',')
        reader = csv.DictReader(csvf, delimiter=self.file_delimiter)

        for line in reader:
            # Updated by Udit on 18th December 2019 (File column names are different taken.
            # ex. 'default_code' must be 'Default Code' as per the file structure.)
            if not line.get('Default Code') or not line.get('Default Code').strip():
                raise Warning('Unable to process..! Please Provide Default Code of Product...')

            # Checks default code and finds product by that default code.
            # Updated by Udit on 18th December 2019
            default_code = line.get('Default Code').strip()
            product = self.env['product.product'].search([('default_code', '=', default_code),
                                                          ('type', '=', 'product')], limit=1)
            if not product:
                msg = """Product Default code does not match any product, default code is
                %s """ % (default_code)
                log_book.post_log_line(msg, log_type='mismatch')
                continue

            # Takes quantity and creates or updates the ICT line as per the configuration.
            # Updated by Udit on 18th December 2019
            quantity = line.get('Qty', '1').strip()
            if quantity == '0':
                quantity = 1.0
            else:
                quantity = float(quantity)
            ict_line = ict.inter_company_transfer_line_ids.filtered(lambda x:
                                                                    x.product_id == product)
            if ict_line:
                # Updated by Udit on 18th December 2019 (Fixed an issue of delete lines in
                # certain cases)
                self.update_ict_line(ict_line, quantity, log_book)
            else:
                if quantity != 0.0:
                    # Updated by Udit on 18th December 2019
                    price = line.get('Price', 0.0)
                    if price == 0.0:
                        price = product.lst_price
                    vals = {'inter_company_transfer_id':ict.id,
                            'product_id':product.id,
                            'quantity':quantity,
                            'price':price}
                    self.create_ict_line(vals)
                    continue
                msg = """File Qty is %s for this Product %s. So You can not Import Product Due
                to this Qty %s you should increase your Qty""" % (quantity, product.name, quantity)
                log_book.post_log_line(msg, log_type='error')
        return True

    def import_products_from_xls(self, ict, log_book):
        """
        Imports products from a csv file to an ICT as transfer lines.
        @author: Maulik Barad on Date 07-Oct-2019.
        @param ict: Record of inter company transfer.
        @param log_book: Record of log book.
        """
        try:
            worksheet = self.read_xls_file()
            file_header = self.get_xls_header(worksheet)
        except Exception as error:
            raise Warning("Something is wrong.\n %s" % (str(error)))
        self.validate_fields(file_header)
        file_line_data = self.prepare_xls_data(worksheet, file_header)
        for line in file_line_data:
            # Updated by Udit on 18th December 2019
            #ex. It should be 'default code' not 'default_code'
            default_code = line.get('default code', '')
            if isinstance(default_code, float):
                default_code = int(default_code)
            default_code = str(default_code)
            product = self.env['product.product'].search([('default_code', '=', default_code)],
                                                         limit=1)
            if not product:
                msg = """Default code does not match with any Product. Default code is
                %s.""" % (default_code)
                log_book.post_log_line(msg, log_type='mismatch')
                continue
            quantity = line.get('qty', 1.0)
            if isinstance(quantity, str):
                quantity = 1.0
            ict_line = ict.inter_company_transfer_line_ids.filtered(lambda x:
                                                                    x.product_id == product)
            if ict_line:
                # Updated by Udit on 18th December 2019
                self.update_ict_line(ict_line, quantity, log_book)
            if not ict_line:
                if quantity != 0.0:
                    price = line.get('price', 0.0)
                    if price == 0.0:
                        price = product.lst_price
                    vals = {'inter_company_transfer_id':ict.id,
                            'product_id':product.id,
                            'quantity':quantity,
                            'price':price}
                    self.create_ict_line(vals)
                    continue
                msg = """File Qty is %s for this Product %s. So You can not Import Product Due
                to this Qty %s you can high your Qty""" % (quantity, product.name, quantity)
                log_book.post_log_line(msg, log_type='error')
        return True

    def update_ict_line(self, ict_line, quantity, log_book):
        """
        Updates ICT's line's quantity.
        @author: Maulik Barad on Date 10-10-2019.
        # Updated by Udit on 18th December 2019 (lines were delete in certain cases while import)
        """
        if self.update_existing:
            if self.update_existing_by == 'add':
                quantity += ict_line.quantity
            if quantity != 0.0:
                ict_line.write({'quantity':quantity})
                return True
            else:
                msg = """Inter Company Transfer Line remove due to File Qty is %s and Default
                                    Code %s and Product %s""" % (
                quantity, ict_line.default_code, ict_line.product_id.name)
                log_book.post_log_line(msg, log_type='info')
                ict_line.sudo().unlink()

        return False

    @api.model
    def create_ict_line(self, vals):
        """
        Creates ICT line with given vals.
        @author: Maulik Barad on Date 10-10-2019.
        """
        ict_line = self.env['inter.company.transfer.line.ept'].create(vals)
        if not ict_line.price:
            ict_line.default_price_get()
        return True

    def read_xls_file(self):
        """
        Reads excel file, creates workbook's object and opens the first sheet.
        @author: Maulik Barad on Date 07-Oct-2019.
        @return: Object of sheet.
        """
        try:
            xl_workbook = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
            worksheet = xl_workbook.sheet_by_index(0)
        except Exception as error:
            raise error
        return worksheet

    @api.model
    def get_xls_header(self, worksheet):
        """
        Lists out the columns from worksheet.
        @author: Maulik Barad on Date 08-Oct-2019.
        @param worksheet: Object of worksheet created from the file.
        @return: List of columns.
        """
        column_list = []
        for index in range(worksheet.ncols):
            column_list.append(worksheet.cell(0, index).value.lower())
        return column_list

    @api.model
    def validate_fields(self, file_fields):
        """
        Checks for needed columns are available or not in worksheet.
        @author: Maulik Barad on Date 08-Oct-2019.
        @param file_fields: List of available columns in worksheet.
        """
        # Updated by Udit on 18th December 2019
        require_fields = ['default code', 'qty']
        missing_fields = []
        for field in require_fields:
            if field not in file_fields:
                missing_fields.append(field)
        # Updated by Udit on 18th December 2019 (Condition was wrong)
        if missing_fields:
            raise Warning("""Incorrect format found..! Please provide all the required fields in
            file, missing fields => %s.""" % (missing_fields))
        return True

    @api.model
    def prepare_xls_data(self, worksheet, columns):
        """
        Prepares list of dictionary with worksheet's data.
        @author: Maulik Barad on Date 08-Oct-2019.
        @param worksheet: Worksheet opened from file.
        @param columns: List of column's names.
        """
        value_list = []
        for row_index in range(1, worksheet.nrows):
            vals_dict = {}
            for col_index in range(worksheet.ncols):
                vals_dict.update({columns[col_index]: worksheet.cell(row_index, col_index).value})
            value_list.append(vals_dict)
        return value_list

    def export_product_list(self):
        """
        Creates product data's file in selected file type.
        @author: Maulik Bard on Date 08-Oct-2019.
        """
        ict_lines = self.env['inter.company.transfer.line.ept'].search([
            ('inter_company_transfer_id', 'in', self.env.context.get('active_ids'))])
        if not ict_lines:
            raise Warning("There is no lines to export.")

        if self.report_type == 'csv':
            self.export_product_list_as_csv(ict_lines)

        elif self.report_type == 'xls':
            self.export_product_list_as_xls(ict_lines)
        # Updated by Udit on 18th December 2019 (Got error while export xls file.)
        return {'type' : 'ir.actions.act_url',
                'url':   """web/content/?model=import.export.products.ept&id=%s&field=datas&download=true&filename=Export_Product_List_%s.%s""" % (self.id, ict_lines[0].inter_company_transfer_id.name, self.report_type),
                'target': 'new'}

    def export_product_list_as_csv(self, ict_lines):
        """
        Makes new excel sheet with data of ICT and generates new workbook.
        @author: Maulik Barad on Date 08-Oct-2019.
        @param ict_lines: Lines of ICT to create row in csv file.
        """
        buffer = StringIO()
        buffer.seek(0)

        # Adds column headers.
        field_names = ['Default Code', 'Qty', 'Price']
        csvwriter = DictWriter(buffer, field_names, delimiter=',')
        csvwriter.writer.writerow(field_names)

        # Added data in rows.
        for line in ict_lines:
            # Updated by Udit on 18th December 2019 (Key name changed)
            data = {
                'Default Code':line.product_id.default_code or "",
                'Qty':line.quantity or 0,
                'Price':line.price or 0
                }
            csvwriter.writerow(data)

        buffer.seek(0)
        file_data = buffer.read().encode()
        file_data = base64.encodebytes(file_data)
        self.write({'datas':file_data})
        return True

    def export_product_list_as_xls(self, ict_lines):
        """
        Makes new excel sheet with data of ICT and generates new workbook.
        @author: Maulik Barad on Date 08-Oct-2019.
        @param ict_lines: Lines of ICT to create row in excel sheet.
        """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("Normal Sales Data", cell_overwrite_ok=True)

        # Adds column headers.
        worksheet.write(0, 0, 'Default Code')
        worksheet.write(0, 1, 'Qty')
        worksheet.write(0, 2, 'Price')

        # Added data in rows.
        row = 1
        for line in ict_lines:
            worksheet.write(row, 0, line.product_id.default_code or "")
            worksheet.write(row, 1, line.quantity or 0)
            worksheet.write(row, 2, line.price or 0)
            row = row + 1

        file_pointer = BytesIO()
        workbook.save(file_pointer)
        file_pointer.seek(0)
        report_data_file = base64.encodebytes(file_pointer.read())
        file_pointer.close()
        self.write({'datas':report_data_file})
        return True
