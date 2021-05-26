odoo.define('shipping_reports.print_action_button', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');
var rpc = require('web.rpc');
var session = require('web.session');
var _t = core._t;

ListController.include({
   renderButtons: function($node) {
   this._super.apply(this, arguments);
       if (this.$buttons) {
         this.$buttons.find('.print_button_ex').click(this.proxy('action_def')) ;
       }
   },

	action_def: function () {
		var self =this
		var selected_rec_ids = self.getSelectedIds() || []; 
        //var user = session.uid;
		self.do_action({
            name: 'Shipping Report',
            type: 'ir.actions.act_window',
            res_model: 'shipping.report.wizard',
            target: 'new',
            views: [[false, 'form']],
            context: {'is_modal': true, 'default_stock_move_ids': selected_rec_ids},
        });
	},
	
});

});