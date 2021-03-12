odoo.define('max.upload', function (require) {
    "use strict";
	var core = require('web.core');
	bus = core.bus;
	var FieldBinaryFile = core.form_widget_registry.get('binary');
	var FieldBinaryImage = core.form_widget_registry.get('image');
	console.log('Called: ' + FieldBinaryFile + bus);

	FieldBinaryFile.include({

		init: function(field_manager, node) {

			this._super(field_manager, node);

			this.max_upload_size = 500 * 1024 * 1024; // 50Mo

		}

	});

	FieldBinaryImage.include({

		init: function(field_manager, node) {

			this._super(field_manager, node);

			this.max_upload_size = 500 * 1024 * 1024; // 50Mo

		}

});

});