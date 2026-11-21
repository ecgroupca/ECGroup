# Inventory Adjustment XLSX Import (Odoo 16)

Upload an `.xlsx` file and a **draft** inventory adjustment is created.

## Install
1. `pip install openpyxl` on the Odoo server (if not already present).
2. Copy the `stock_inventory_xlsx_import` folder into your addons path.
3. Restart Odoo, Apps > Update Apps List, install **Inventory Adjustment XLSX Import**.

## Upgrading from 16.0.1.0.0
Copy the new files over the old ones and upgrade the module
(`odoo-bin -u stock_inventory_xlsx_import -d <db>`), then restart and reload the browser
so the new JavaScript is picked up.

## Use
Inventory > Operations > **Import Inventory (XLSX)** - a list of all uploads, kept
separate from the Physical Inventory screen, placed right above it in the menu.
Click **Upload** in the list header, choose the file and click **Import**. The new
import opens with an **Open Draft Adjustment** button that takes you to the count
lines in Physical Inventory, where they can be reviewed and applied.

Each import record keeps the uploaded file, who uploaded it and when, the count lines
it created, and a status (*Draft* while any of its lines are still unapplied, *Done*
once all have been applied).

The first sheet of the file is read; the first row must contain the headers:

| Part Number (default_code) | Location | Lot/Serial Number | Quantity |
|---|---|---|---|

* **Part Number** - product Internal Reference, exact match, product must be storable.
* **Location** - full internal location name (e.g. `WH/Stock/Shelf 1`); a short name
  is accepted if it is unique.
* **Lot/Serial Number** - required for tracked products, empty for untracked ones.
  Missing lots/serials are created (can be switched off in the wizard).
* **Quantity** - counted quantity, 0 or more (serials: 0 or 1).

## What "draft" means in Odoo 16
Odoo 16 no longer has an Inventory Adjustment document. An adjustment is a set of
`stock.quant` lines with a *Counted Quantity* that has not been applied. The import
sets exactly that, the same way the Physical Inventory screen does, so stock levels
are untouched until someone clicks **Apply** (single line or *Apply All*). Counts
for a product/location/lot that already has a pending count are overwritten.

## Validation
All rows are checked before anything is written. If any row is invalid nothing is
imported and the problems are listed with their row numbers (unknown part or
location, tracking mismatch, bad quantity, duplicate rows, ...).

Tip: format the Part Number / Location / Lot columns as Text (the template already
does) so Excel keeps leading zeros and long numbers.
