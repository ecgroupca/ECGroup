# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models


class DataQueueMixinEpt(models.AbstractModel):
    """ Mixin class for delete unused data queue from database."""
    _inherit = "data.queue.mixin.ept"

    def delete_data_queue_ept(self, queue_data=False, is_delete_queue=False):
        """
        This method will delete completed data queues from database.
        """
        if not queue_data:
            queue_data = []
        queue_data += ["shopify_product_data_queue_ept", "shopify_order_data_queue_ept",
                       "shopify_customer_data_queue_ept", "shopify_export_stock_queue_line_ept",
                       "shopify_export_stock_queue_ept"]
        # to delete the records of the shopify_export_stock_queue_line_ept expicitely
        self.delete_data_queue_schedule_activity_ept("shopify_export_stock_queue_line_ept", is_delete_queue)
        return super(DataQueueMixinEpt, self).delete_data_queue_ept(queue_data, is_delete_queue)
