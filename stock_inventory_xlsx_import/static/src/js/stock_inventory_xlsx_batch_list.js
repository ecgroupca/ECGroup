/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";

/**
 * List controller of the "Import Inventory (XLSX)" list: adds an Upload button
 * to the header (control panel) that opens the upload dialog.
 */
export class StockInventoryXlsxBatchListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    onClickUpload() {
        this.actionService.doAction(
            "stock_inventory_xlsx_import.stock_inventory_xlsx_import_action"
        );
    }
}

export const stockInventoryXlsxBatchListView = {
    ...listView,
    Controller: StockInventoryXlsxBatchListController,
    buttonTemplate: "stock_inventory_xlsx_import.BatchListView.Buttons",
};

registry.category("views").add("stock_inventory_xlsx_batch_list", stockInventoryXlsxBatchListView);
