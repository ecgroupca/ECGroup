# -*- coding: utf-8 -*-
import base64
import io
import logging
import math
import re

from odoo import Command, _, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None

MAX_ERRORS_SHOWN = 30

# Accepted header names (lower-cased, everything except a-z/0-9 removed) -> internal key
COLUMN_ALIASES = {
    'code': {'partnumber', 'partnumberdefaultcode', 'defaultcode', 'internalreference'},
    'location': {'location', 'locationname'},
    'lot': {'lotserialnumber', 'lotserial', 'lot', 'serialnumber', 'lotnumber', 'lotserialno'},
    'qty': {'quantity', 'qty', 'countedquantity'},
}
COLUMN_LABELS = {
    'code': 'Part Number',
    'location': 'Location',
    'lot': 'Lot/Serial Number',
    'qty': 'Quantity',
}


def _cell_to_str(value):
    """Text of a cell. Numbers typed into Excel come back as int/float
    (12345 -> 12345.0), so whole floats are turned back into integers."""
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _cell_to_float(value):
    """Float value of a cell, None when blank, ValueError when not a number."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(value)
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip()
        if not text:
            return None
        number = float(text)
    if not math.isfinite(number):
        raise ValueError(value)
    return number


def _normalise_header(value):
    return re.sub(r'[^a-z0-9]', '', _cell_to_str(value).lower())


class StockInventoryXlsxImport(models.TransientModel):
    _name = 'stock.inventory.xlsx.import'
    _description = 'Import Inventory Adjustment from XLSX'

    file = fields.Binary(string='XLSX File', required=True, attachment=False)
    filename = fields.Char(string='File Name')
    create_missing_lots = fields.Boolean(
        string='Create Missing Lots/Serials',
        default=True,
        help="If a Lot/Serial Number in the file does not exist yet for the product, "
             "create it. When unticked, an unknown lot/serial is reported as an error.")

    # ------------------------------------------------------------------
    # File reading
    # ------------------------------------------------------------------
    def _read_rows(self):
        """Return the data rows of the first sheet as a list of dicts:
        {'row': <excel row number>, 'code', 'location', 'lot', 'qty'}"""
        self.ensure_one()
        if openpyxl is None:
            raise UserError(_("The Python library 'openpyxl' is not installed on the server "
                              "(pip install openpyxl)."))
        try:
            workbook = openpyxl.load_workbook(
                io.BytesIO(base64.b64decode(self.file)), data_only=True)
        except Exception as exc:
            _logger.info("Inventory import: unreadable file %s: %s", self.filename, exc)
            raise UserError(_("The uploaded file is not a valid .xlsx spreadsheet.")) from exc
        try:
            sheet = workbook.worksheets[0]
            raw_rows = list(sheet.iter_rows(values_only=True))
        finally:
            workbook.close()

        if not raw_rows:
            raise UserError(_("The spreadsheet is empty."))

        # Locate the four columns by header name.
        headers = [_normalise_header(h) for h in raw_rows[0]]
        columns = {}
        for key, aliases in COLUMN_ALIASES.items():
            for index, header in enumerate(headers):
                if header in aliases:
                    columns[key] = index
                    break
        missing = [COLUMN_LABELS[k] for k in COLUMN_LABELS if k not in columns]
        if missing:
            raise UserError(_(
                "Column(s) not found in the first row of the spreadsheet: %s.\n"
                "The first row must contain: Part Number | Location | Lot/Serial Number | Quantity"
            ) % ', '.join(missing))

        rows = []
        for line_no, raw in enumerate(raw_rows[1:], start=2):
            def cell(key):
                index = columns[key]
                return raw[index] if index < len(raw) else None
            values = {key: cell(key) for key in columns}
            if all(_cell_to_str(v) == '' for v in values.values()):
                continue  # blank line
            rows.append({
                'row': line_no,
                'code': _cell_to_str(values['code']),
                'location': _cell_to_str(values['location']),
                'lot': _cell_to_str(values['lot']),
                'qty': values['qty'],
            })
        return rows

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _build_plan(self, rows):
        """Validate every row without writing anything.
        Returns (plan, lots_to_create, errors)."""
        Product = self.env['product.product']
        Location = self.env['stock.location']
        Lot = self.env['stock.lot']
        plan, errors = [], []

        # Bulk look-ups (one query each instead of one per row)
        codes = list({r['code'] for r in rows if r['code']})
        products = Product.search([('default_code', 'in', codes)]) if codes else Product
        products_by_code = {}
        for product in products:
            products_by_code.setdefault(product.default_code, []).append(product)

        locations = Location.search([('usage', 'in', ('internal', 'transit'))])
        by_path, by_name = {}, {}
        for location in locations:
            by_path.setdefault((location.complete_name or location.name or '').strip().lower(), []).append(location)
            by_name.setdefault((location.name or '').strip().lower(), []).append(location)

        lot_names = list({r['lot'] for r in rows if r['lot']})
        lots = Lot.search([('product_id', 'in', products.ids), ('name', 'in', lot_names)]) \
            if (lot_names and products) else Lot
        lot_map = {}
        for lot in lots:
            lot_map.setdefault((lot.product_id.id, lot.name), lot)

        seen = {}            # (product, location, lot name) -> first row
        serial_seen = {}     # (product, serial) -> first row with qty > 0
        lots_to_create = {}  # (product id, lot name) -> product

        for r in rows:
            prefix = _("Row %s: ") % r['row']

            # --- product -------------------------------------------------
            if not r['code']:
                errors.append(prefix + _("Part Number is empty."))
                continue
            candidates = products_by_code.get(r['code'], [])
            if not candidates:
                errors.append(prefix + _("no active product with Part Number '%s'.") % r['code'])
                continue
            if len(candidates) > 1:
                errors.append(prefix + _("Part Number '%s' matches more than one product.") % r['code'])
                continue
            product = candidates[0]
            if product.type != 'product':
                errors.append(prefix + _("'%s' is not a storable product.") % r['code'])
                continue

            # --- location ------------------------------------------------
            if not r['location']:
                errors.append(prefix + _("Location is empty."))
                continue
            key = r['location'].lower()
            matches = by_path.get(key) or by_name.get(key) or []
            if not matches:
                errors.append(prefix + _(
                    "internal location '%s' not found. Use the full name shown in "
                    "Inventory > Configuration > Locations, e.g. WH/Stock.") % r['location'])
                continue
            if len(matches) > 1:
                errors.append(prefix + _("Location '%s' matches more than one location; "
                                         "use the full name (e.g. WH/Stock/Shelf 1).") % r['location'])
                continue
            location = matches[0]

            # --- quantity ------------------------------------------------
            try:
                qty = _cell_to_float(r['qty'])
            except ValueError:
                errors.append(prefix + _("Quantity '%s' is not a number.") % r['qty'])
                continue
            if qty is None:
                errors.append(prefix + _("Quantity is empty (enter 0 to count zero)."))
                continue
            if qty < 0:
                errors.append(prefix + _("Quantity cannot be negative."))
                continue

            # --- lot / serial -------------------------------------------
            lot_name = r['lot']
            if product.tracking == 'none' and lot_name:
                errors.append(prefix + _("'%s' is not tracked by lot/serial; "
                                         "leave Lot/Serial Number empty.") % r['code'])
                continue
            if product.tracking != 'none' and not lot_name:
                errors.append(prefix + _("'%s' is tracked by lot/serial; "
                                         "Lot/Serial Number is required.") % r['code'])
                continue
            if product.tracking == 'serial' and qty not in (0.0, 1.0):
                errors.append(prefix + _("serial number '%s' must have a quantity of 0 or 1.") % lot_name)
                continue

            lot = None
            if lot_name:
                lot = lot_map.get((product.id, lot_name))
                if not lot and not self.create_missing_lots:
                    errors.append(prefix + _("Lot/Serial Number '%s' does not exist for '%s'.")
                                  % (lot_name, r['code']))
                    continue

            # --- duplicates inside the file -------------------------------
            dup_key = (product.id, location.id, lot_name)
            if dup_key in seen:
                errors.append(prefix + _("duplicate of row %s (same part, location and lot/serial).")
                              % seen[dup_key])
                continue
            seen[dup_key] = r['row']
            if product.tracking == 'serial' and qty > 0:
                serial_key = (product.id, lot_name)
                if serial_key in serial_seen:
                    errors.append(prefix + _("serial number '%s' is already counted in row %s.")
                                  % (lot_name, serial_seen[serial_key]))
                    continue
                serial_seen[serial_key] = r['row']

            if lot_name and not lot:
                lots_to_create[(product.id, lot_name)] = product

            plan.append({
                'row': r['row'],
                'product': product,
                'location': location,
                'lot': lot,
                'lot_key': (product.id, lot_name) if lot_name else None,
                'qty': qty,
            })
        return plan, lots_to_create, errors

    # ------------------------------------------------------------------
    # Main action
    # ------------------------------------------------------------------
    def action_import(self):
        self.ensure_one()
        if not self.env.user.has_group('stock.group_stock_user'):
            raise AccessError(_("Only Inventory users can import inventory adjustments."))

        rows = self._read_rows()
        if not rows:
            raise UserError(_("The spreadsheet does not contain any data rows."))

        plan, lots_to_create, errors = self._build_plan(rows)
        if errors:
            message = _("Nothing was imported. Please fix the following and upload the file again:\n%s") \
                % '\n'.join(errors[:MAX_ERRORS_SHOWN])
            if len(errors) > MAX_ERRORS_SHOWN:
                message += _("\n... and %s more problem(s).") % (len(errors) - MAX_ERRORS_SHOWN)
            raise UserError(message)

        # Everything is valid: create the missing lots, then the counts.
        new_lots = {}
        if lots_to_create:
            created = self.env['stock.lot'].create([{
                'name': name,
                'product_id': product.id,
                'company_id': product.company_id.id or self.env.company.id,
            } for (_pid, name), product in lots_to_create.items()])
            new_lots = {(lot.product_id.id, lot.name): lot for lot in created}

        # inventory_mode=True is what the Physical Inventory screen itself uses: it sets the
        # "Counted Quantity" (inventory_quantity) of the quant - merging with an existing quant
        # for the same product/location/lot - without applying it to the on-hand stock.
        Quant = self.env['stock.quant'].with_context(inventory_mode=True)
        vals_list = []
        for line in plan:
            lot = line['lot'] or (line['lot_key'] and new_lots[line['lot_key']])
            vals = {
                'product_id': line['product'].id,
                'location_id': line['location'].id,
                'inventory_quantity': line['qty'],
            }
            if lot:
                vals['lot_id'] = lot.id
            vals_list.append(vals)
        quants = Quant.create(vals_list)

        # Keep a record of the upload (file, user, date and the count lines it created)
        # so it shows up in Inventory > Operations > Import Inventory (XLSX).
        batch = self.env['stock.inventory.xlsx.batch'].create({
            'file_name': self.filename,
            'file': self.file,
            'line_count': len(quants),
            'quant_ids': [Command.set(quants.ids)],
        })
        _logger.info("Inventory import %s (%s): %s count line(s) created by %s",
                     batch.name, self.filename, len(quants), self.env.user.login)

        return {
            'type': 'ir.actions.act_window',
            'name': batch.name,
            'res_model': 'stock.inventory.xlsx.batch',
            'res_id': batch.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }
