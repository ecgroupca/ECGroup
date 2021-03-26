// product_image_import/static/src/js/increase_max_upload.js
odoo.define('product_image_import.increase_max_upload', function (require) {
    "use strict";
	var core = require('web.core');
	//var _t = core._t;
	//var QWeb = core.qweb;
	var registry = require('web.field_registry');
	
	//console.log(registry);
    
	var basic_fields = require('web.basic_fields');
	
	var FieldBinaryFile = basic_fields.AbstractFieldBinaryFile;
	var FieldBinaryImage = basic_fields.AbstractFieldBinaryImage;
	console.log(FieldBinaryFile);
    var FieldBinaryFileUpdate = basic_fields.FieldBinaryFile.include({
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