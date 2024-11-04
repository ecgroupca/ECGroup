# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import base64
import csv
import logging
from csv import DictWriter
from io import StringIO, BytesIO
import xlrd

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import xlwt
except ImportError:
    xlwt = None

_logger = logging.getLogger("ICT Import/Export")


class ImportExportProducts(models.TransientModel):
    """
    Model for importing and exporting products to/from ICT.
    @author: Maulik Barad.
    """
    _name = "import.export.products.ept"
    _description = "Import Export Products"
    _inherit = ["barcodes.barcode_events_mixin"]

    file = fields.Binary("Select File")
    file_name = fields.Char()
    report_type = fields.Selection(selection=[("csv", "CSV"), ("xls", "Xls")])
    file_delimiter = fields.Selection([(";", "Semicolon (;)"), ("\t", "Tab")], string="Delimiter",
                                      help="Select a delimiter to process CSV file.")
    update_existing = fields.Boolean("Do you want to update existing record?")
    update_existing_by = fields.Selection([("add", "Add quantity to existing"),
                                           ("replace", "Replace with file quantity")])
    loose_lot_transfer = fields.Boolean()
    lot_company_id = fields.Many2one("res.company")
    lot_serial_scan_line_ids = fields.One2many("lot.serial.scan.line.ept", "import_export_products_id")
    message = fields.Char()

    def check_file_extension(self):
        """
        Checks file extension for the format of file.
        @author: Maulik Barad on Date 21-Dec-2020.
        """
        if not self.file:
            raise UserError(_("Unable to process..! Please select a file to process... "))
        file_name = self.file_name
        index = file_name.rfind(".")
        flag = 0
        if index == -1:
            flag = 1
        extension = file_name[index + 1:]

        if flag or extension not in ["csv", "xls", "xlsx"]:
            raise UserError(
                _("""Incorrect file format found..! Please provide only .csv or .xls file format to import data!!!"""))

    def import_product_list(self):
        """
        Imports products from the uploaded file of Excel or CSV.
        @author: Maulik Barad.
        """
        self.check_file_extension()

        # Checks ICT's state and calls import method as per file type.
        inter_company_transfer_id = self.env["inter.company.transfer.ept"].browse(self._context.get("active_id", False))
        if inter_company_transfer_id:
            if inter_company_transfer_id.state not in ["draft"]:
                raise UserError(_("The record is not in draft state."))

            _logger.info("Import products via %s method", self.report_type)
            if self.report_type == "csv":
                self.import_products_from_csv(inter_company_transfer_id)

            elif self.report_type == "xls":
                self.import_products_from_xls(inter_company_transfer_id)

        return True

    def import_products_from_csv(self, ict):
        """
        Imports products from a csv file to an ICT as transfer lines.
        @author: Maulik Barad.
        @param ict: Record of intercompany transfer.
        """
        ict_line_vals_list = []

        import_file = BytesIO(base64.decodebytes(self.file))
        csv_file = StringIO(import_file.read().decode())
        reader = csv.DictReader(csv_file, delimiter=self.file_delimiter)

        for line in reader:
            if not (line.get("Default Code") and line.get("Default Code").strip()) and not (
                    line.get("Barcode") and line.get("Barcode").strip()):
                raise UserError(_("Unable to process..! Please Provide Default Code or Barcode of Product..."))

            default_code = line.get("Default Code").strip()
            barcode = line.get("Barcode").strip()
            product = self.get_product_from_sku_barcode(default_code, barcode, ict)
            if not product:
                continue

            price = line.get("Price", 0.0)
            quantity = line.get("Qty", "1").strip()
            if quantity == "0":
                quantity = 1.0
            else:
                quantity = float(quantity)

            lot_ids = self.get_lot_ids(line.get("Lot/Serial Number"), product, quantity, ict)
            if isinstance(lot_ids, bool):
                continue

            vals = self.prepare_ict_line_vals(ict, product, quantity, price, lot_ids)
            if not vals:
                continue
            ict_line_vals_list.append(vals)

        self.create_ict_line(ict_line_vals_list)
        return True

    def import_products_from_xls(self, ict):
        """
        Imports products from a csv file to an ICT as transfer lines.
        @author: Maulik Barad.
        @param ict: Record of intercompany transfer.
        """
        ict_line_vals_list = []

        file_data = self.get_file_data_for_xls()
        for line in file_data:
            default_code = line.get("default code", "")
            barcode = line.get("barcode", "")
            if isinstance(default_code, float):
                default_code = int(default_code)
            if isinstance(barcode, float):
                barcode = int(barcode)
            default_code = str(default_code)
            barcode = str(barcode)

            product = self.get_product_from_sku_barcode(default_code, barcode, ict)
            if not product:
                continue

            price = line.get("price", 0.0)
            quantity = line.get("qty", 1.0)
            if isinstance(quantity, str):
                quantity = 1.0

            lot_ids = self.get_lot_ids(line.get("lot/serial number"), product, quantity, ict)
            if isinstance(lot_ids, bool):
                continue

            vals = self.prepare_ict_line_vals(ict, product, quantity, price, lot_ids)
            if not vals:
                continue
            ict_line_vals_list.append(vals)

        self.create_ict_line(ict_line_vals_list)
        return True

    def update_ict_line(self, ict_line, quantity, lot_ids):
        """
        Updates ICT's line's quantity.
        @author: Maulik Barad.
        """
        _logger.info("Updating existing line for Product %s", ict_line.product_id.name)
        if self.update_existing_by == "add":
            if ict_line.product_id.tracking == "none":
                self.update_ict_line_data(ict_line[0], quantity)

            elif ict_line.product_id.tracking == "serial" or (
                    ict_line.product_id.tracking == "lot" and not self.loose_lot_transfer):
                self.update_ict_line_data(ict_line[0], quantity, lot_ids)

            elif ict_line.product_id.tracking == "lot" and self.loose_lot_transfer:
                ict_line = ict_line.filtered(lambda x: x.lot_serial_ids.ids == lot_ids)
                if ict_line:
                    self.update_ict_line_data(ict_line[0], quantity)
                else:
                    return False

                # msg = """Inter Company Transfer Line remove due to File Qty is %s and Default Code %s and Product
                # %s""" % (quantity, ict_line.default_code, ict_line.product_id.name)
                # ict_line.sudo().unlink()
        elif self.update_existing_by == "replace":
            ict_line.sudo().unlink()
            return False

        return True

    def update_ict_line_data(self, ict_line, qty, lot_ids=False):
        """
        This method is used to update the existing ict line with quantity and lot/serial ids.
        @param ict_line: Record of the ict line.
        @param qty: Quantity to add.
        @param lot_ids: Lot/Serial ids to add (List).
        @author: Maulik Barad on Date 09-Feb-2021.
        """
        qty += ict_line.quantity
        vals = {"quantity": qty}

        if lot_ids:
            lot_ids += ict_line[0].lot_serial_ids.ids
            vals.update({"lot_serial_ids": [(6, 0, lot_ids)]})
        if qty != 0.0:
            ict_line.write(vals)
            return True
        return False

    def get_file_data_for_xls(self):
        """
        This method reads data from the xls file and validates it.
        @author: Maulik Barad on Date 22-Dec-2020.
        """
        try:
            worksheet = self.read_xls_file()
            file_header = self.get_xls_header(worksheet)
        except Exception as error:
            raise UserError(_("Something is wrong.\n %s") % (str(error)))
        self.validate_fields(file_header)
        file_line_data = self.prepare_xls_data(worksheet, file_header)
        return file_line_data

    def get_product_from_sku_barcode(self, default_code, barcode, ict):
        """
        This method is used to search product from the sku.
        @param ict:
        @param default_code: SKU to find the product.
        @param barcode: Barcode to find the product.
        @author: Maulik Barad on Date 22-Dec-2020.
        """
        product_obj = product = self.env["product.product"]
        if default_code:
            product = product_obj.search([("default_code", "=", default_code)], limit=1)
        elif barcode:
            product = product_obj.search([("barcode", "=", barcode)], limit=1)
        if not product:
            msg = "Product is not found. Default code is '%s'" % default_code
            if not default_code:
                msg += " and Barcode is '%s'." % barcode
            self.env["inter.company.transfer.log.line.ept"].post_log_line(msg, ict, "import", "mismatch")
        return product

    def get_lot_ids(self, lot_numbers, product, quantity, ict):
        """
        This method searches for the lot/serial number added in file for the product and validates it.
        @param ict:
        @param lot_numbers: List of the lot numbers.
        @param product: Product to search lots for.
        @param quantity: Quantity to check with given lot/serial.
        @author: Maulik Barad on Date 21-Dec-2020.
        """
        lot_ids = []
        lot_stock_obj = self.env["stock.lot"]

        if lot_numbers:
            msg = False
            if isinstance(lot_numbers, float):
                lot_numbers = str(int(lot_numbers))
            lot_numbers_list = lot_numbers.split(",")
            lots = lot_stock_obj.search([("name", "in", lot_numbers_list), ("product_id", "=", product.id),
                                         ("company_id", "=", ict.source_company_id.id)])
            if not lots:
                msg = _("Lot/Serial numbers not found for product %s having Lot/Serial %s.") % (product.name,
                                                                                                lot_numbers)

            if product.tracking == "lot":
                lot_qty = sum(lots.mapped("product_qty"))

                if lot_qty < quantity:
                    msg = _("Provided Lot numbers can't fulfil enough quantity for product %s having Lot/Serial %s.") \
                          % (product.name, lot_numbers)

            elif product.tracking == "serial":
                serial_count = len(lots)
                if serial_count:
                    if quantity < serial_count:
                        lots = lots[0:int(quantity)]
                    elif quantity != serial_count:
                        msg = _(
                            "Provided Serial numbers are not enough to fulfil quantity for product %s having "
                            "Lot/Serial %s.") % (product.name, lot_numbers)

            if msg:
                self.env["inter.company.transfer.log.line.ept"].post_log_line(msg, ict, "import", "mismatch")
                return False
            lot_ids = lots.ids
        return lot_ids

    def prepare_ict_line_vals(self, ict, product, quantity, price, lot_ids):
        """
        This method checks for existing line, updates according to selected options and process the data based on that.
        Returns vals if need to create an ict line.
        @param ict: Record of the ict.
        @param product: Record of the product.
        @param quantity: Quantity to transfer.
        @param price: Price to set in line.
        @param lot_ids: List of Lot/Serial number id.
        """
        vals = {}
        no_need_to_create = False

        ict_line = ict.inter_company_transfer_line_ids.filtered(lambda x: x.product_id == product)
        if ict_line and self.update_existing:
            no_need_to_create = self.update_ict_line(ict_line, quantity, lot_ids)

        if not no_need_to_create:
            if quantity != 0.0:
                if price == 0.0:
                    price = product.lst_price
                vals.update({"inter_company_transfer_id": ict.id,
                             "product_id": product.id,
                             "quantity": quantity,
                             "price": price,
                             "lot_serial_ids": [(6, 0, lot_ids)]})
                return vals
            msg = """File Qty is %s for this Product %s. So You can not Import Product Due to this Qty %s you can
            high your Qty""" % (quantity, product.name, quantity)
            self.env["inter.company.transfer.log.line.ept"].post_log_line(msg, ict, "import")
        return vals

    @api.model
    def create_ict_line(self, vals_list):
        """
        Creates ICT lines from given list of values.
        @author: Maulik Barad.
        """
        if vals_list:
            ict_lines = self.env["inter.company.transfer.line.ept"].create(vals_list)
            for ict_line in ict_lines.filtered(lambda x: not x.price):
                ict_line.default_price_get()
        return True

    def read_xls_file(self):
        """
        Reads excel file, creates workbook's object and opens the first sheet.
        @author: Maulik Barad.
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
        @author: Maulik Barad.
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
        @author: Maulik Barad.
        @param file_fields: List of available columns in worksheet.
        """
        require_fields = ["default code", "barcode", "qty"]
        missing_fields = []
        for field in require_fields:
            if field not in file_fields:
                missing_fields.append(field)
        if missing_fields:
            raise UserError(_("""Incorrect format found..! Please provide all the required fields in file,
            missing fields => %s.""") % missing_fields)
        return True

    @api.model
    def prepare_xls_data(self, worksheet, columns):
        """
        Prepares list of dictionary from worksheet's data.
        @author: Maulik Barad.
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
        Creates file in selected file type to export product data from ICT Line.
        @author: Maulik Barad.
        """
        ict_lines = self.env["inter.company.transfer.line.ept"].search(
            [("inter_company_transfer_id", "in", self.env.context.get("active_ids"))])
        if not ict_lines:
            raise UserError(_("There are no lines to export."))

        if self.report_type == "csv":
            self.export_product_list_as_csv(ict_lines)

        elif self.report_type == "xls":
            self.export_product_list_as_xls(ict_lines)

        return {"type": "ir.actions.act_url",
                "url": "web/content/?model=import.export.products.ept&id=%s&field=file&download=true&filename"
                       "=Export_Product_List_%s.%s" % (
                           self.id, ict_lines[0].inter_company_transfer_id.name, self.report_type),
                "target": "new"}

    def export_product_list_as_csv(self, ict_lines):
        """
        Makes new excel sheet with data of ICT and generates new workbook.
        @author: Maulik Barad.
        @param ict_lines: Lines of ICT to create row in csv file.
        """
        buffer = StringIO()
        buffer.seek(0)

        # Adds column headers.
        field_names = ["Default Code", "Barcode", "Qty", "Price", "Lot/Serial Number"]
        csvwriter = DictWriter(buffer, field_names, delimiter=self.file_delimiter)
        csvwriter.writer.writerow(field_names)

        # Added data in rows.
        for line in ict_lines:
            product_id = line.product_id
            lot_numbers_list = line.lot_serial_ids.mapped("name")
            lot_numbers = ",".join(lot_numbers_list)
            data = {
                "Default Code": product_id.default_code or "",
                "Barcode": product_id.barcode or "",
                "Qty": line.quantity or 0,
                "Price": line.price or 0,
                "Lot/Serial Number": lot_numbers
            }
            csvwriter.writerow(data)

        buffer.seek(0)
        file_data = buffer.read().encode()
        file_data = base64.encodebytes(file_data)
        self.write({"file": file_data})
        return True

    def export_product_list_as_xls(self, ict_lines):
        """
        Makes new excel sheet with data of ICT and generates new workbook.
        @author: Maulik Barad.
        @param ict_lines: Lines of ICT to create row in excel sheet.
        """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("Normal Sales Data", cell_overwrite_ok=True)

        # Adds column headers.
        worksheet.write(0, 0, "Default Code")
        worksheet.write(0, 1, "Barcode")
        worksheet.write(0, 2, "Qty")
        worksheet.write(0, 3, "Price")
        worksheet.write(0, 4, "Lot/Serial Number")

        # Added data in rows.
        row = 1
        for line in ict_lines:
            product_id = line.product_id
            lot_numbers_list = line.lot_serial_ids.mapped("name")
            lot_numbers = ",".join(lot_numbers_list)
            worksheet.write(row, 0, product_id.default_code or "")
            worksheet.write(row, 1, product_id.barcode or "")
            worksheet.write(row, 2, line.quantity or 0)
            worksheet.write(row, 3, line.price or 0)
            worksheet.write(row, 4, lot_numbers or "")
            row = row + 1

        file_pointer = BytesIO()
        workbook.save(file_pointer)
        file_pointer.seek(0)
        report_data_file = base64.encodebytes(file_pointer.read())
        file_pointer.close()
        self.write({"file": report_data_file})
        return True

    def on_barcode_scanned(self, barcode):
        """
        Barcode scan handling method.
        @param barcode: Scanned barcode.
        @author: Maulik Barad on Date 06-Jan-2021.
        """
        company_id = self.lot_company_id.id
        lot_serial = self.env["stock.lot"].search_read([("name", "=", barcode),
                                                        ("company_id", "=", company_id)],
                                                       ["id", "product_id", "product_qty"])

        if not lot_serial:
            self.message = "Lot/Serial not found for %s." % barcode
            return
        if len(lot_serial) > 1:
            self.message = "More than one Lot/Serial found."
            return
        lot_serial = lot_serial[0]
        if self.lot_serial_scan_line_ids.filtered(lambda x: lot_serial["id"] in x.lot_serial_ids.ids):
            self.message = "Lot/Serial %s is already added." % barcode
            return

        if not lot_serial["product_qty"]:
            self.message = "Not enough stock available in Lot/Serial %s." % barcode
            return

        self.add_lot_serial_scan_line(lot_serial)
        self.message = False
        return

    def add_lot_serial_scan_line(self, lot_serial):
        """
        This method is used to create or update the scan line of lot serial.
        @param lot_serial: Dictionary of Lot/Serial's id, product_id and product_quantity.
        @author: Maulik Barad on Date 07-Jan-2020.
        """
        product_id = lot_serial["product_id"][0]
        quantity = lot_serial["product_qty"]
        if not self.loose_lot_transfer:
            scan_line = self.lot_serial_scan_line_ids.filtered(lambda x: x.product_id.id == product_id)
            if scan_line:
                quantity += scan_line.quantity
                scan_line.write({"lot_serial_ids": [(4, lot_serial["id"])], "quantity": quantity})
                return True
        self.lot_serial_scan_line_ids = [(0, 0, {"product_id": product_id, "lot_serial_ids": [(4, lot_serial["id"])],
                                                 "quantity": quantity})]

        return True

    def create_ict_lines(self):
        """
        This method is used to create ict lines from the scanned lot/serial lines.
        @author: Maulik Barad on Date 07-Jan-2020.
        """
        if self.loose_lot_transfer:
            for line in self.lot_serial_scan_line_ids:
                lots = line.lot_serial_ids
                lot_qty = sum(lots.mapped("product_qty"))

                if lot_qty < line.quantity:
                    raise UserError(_("Provided Lot/Serial numbers can't fulfil enough quantity for \n%s - Lot/Serial "
                                      "%s.") % (line.product_id.name, ",".join(line.lot_serial_ids.mapped("name"))))

        scanned_line_data = list(map(lambda x: x.copy_data()[0], self.lot_serial_scan_line_ids))

        def update_scan_line_data(line_data):
            """
            It will update the data of scanned line for creating ict line.
            @param line_data: Dictionary of scanned line.
            @author: Maulik Barad on Date 08-Jan-2020.
            """
            line_data.pop("import_export_products_id")
            line_data.update(inter_company_transfer_id=self._context.get("active_id"))
            return line_data

        if scanned_line_data:
            ict_line_vals_list = list(map(update_scan_line_data, scanned_line_data))
            if ict_line_vals_list:
                self.env["inter.company.transfer.line.ept"].create(ict_line_vals_list)
        return True
