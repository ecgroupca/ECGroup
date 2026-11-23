/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { sprintf } from "@web/core/utils/strings";

/**
 * List controller of the imported count lines: the standard row check boxes (and the
 * "select all" check box in the header) choose the lines, and the "Apply Selected"
 * button applies exactly those lines to stock.
 */
export class StockInventoryXlsxLineListController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.notificationService = useService("notification");
    }

    async onClickApplySelected() {
        const resIds = this.getSelectedResIds
            ? await this.getSelectedResIds()
            : this.model.root.selection.map((record) => record.resId);
        if (!resIds.length) {
            this.notificationService.add(_t("Select at least one line to apply."), {
                type: "warning",
            });
            return;
        }
        this.dialogService.add(ConfirmationDialog, {
            title: _t("Apply Selected Lines"),
            body: sprintf(
                _t(
                    "Apply %s selected line(s) to stock? The on-hand quantity will be set to " +
                        "the counted quantity. Lines that are already applied are skipped."
                ),
                resIds.length
            ),
            confirm: () => this._applyLines(resIds),
            cancel: () => {},
        });
    }

    async _applyLines(resIds) {
        const result = await this.orm.call(
            "stock.inventory.xlsx.batch",
            "action_apply_quants",
            [resIds]
        );
        if (result && result.type) {
            // Odoo asks for a confirmation (outdated count, tracked product without lot...)
            await this.actionService.doAction(result, { onClose: () => this._reload() });
            return;
        }
        let message = sprintf(_t("%s line(s) applied."), result.applied);
        if (result.skipped) {
            message += " " + sprintf(_t("%s skipped (already applied)."), result.skipped);
        }
        this.notificationService.add(message, { type: "success" });
        await this._reload();
    }

    async _reload() {
        await this.model.root.load();
        this.model.notify();
    }
}

export const stockInventoryXlsxLineListView = {
    ...listView,
    Controller: StockInventoryXlsxLineListController,
    buttonTemplate: "stock_inventory_xlsx_import.LineListView.Buttons",
};

registry.category("views").add("stock_inventory_xlsx_line_list", stockInventoryXlsxLineListView);
