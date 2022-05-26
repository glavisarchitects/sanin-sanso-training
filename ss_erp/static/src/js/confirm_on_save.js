odoo.define('ss_erp.web_confirm_on_save', function (require) {
"use strict";

    var ajax = require('web.ajax');
    var AbstractView = require('web.AbstractView');
    var FormController = require('web.FormController');
    var Dialog = require('web.Dialog');
    var session = require('web.session');

AbstractView.include({

	init: function (viewInfo, params) {
    	var self = this;
    	this._super.apply(this, arguments);
    	var confirm =  this.arch.attrs.confirm_partner_custom ? this.arch.attrs.confirm_partner_custom : false;
    	self.controllerParams.activeActions.confirm_partner_custom = confirm;

    },

});

FormController.include({

	check_condition: function (modelName, vals ,data_changed) {
        var def = this._rpc({
            "model": modelName,
            "method": "check_condition_show_dialog",
            "args": [vals ,data_changed]
        });
        return def;
    },

	_onSave: function (ev) {
		var self = this;
		var modelName = this.modelName ? this.modelName : false;
		var record = this.model.get(this.handle, {raw: true});
		var data_changed = record ? record.data : false;
		var vals = data_changed && data_changed.id ? data_changed.id : false;
		var confirm = self.activeActions.confirm_partner_custom;

		function saveAndExecuteAction () {
			ev.stopPropagation(); // Prevent x2m lines to be auto-saved
			self._disableButtons();
			self.saveRecord().then(self._enableButtons.bind(self)).guardedCatch(self._enableButtons.bind(self));
	    }
		if( modelName ==='res.partner' || modelName ==='ss_erp.res.partner.form' && confirm){
			self.check_condition(modelName, vals, data_changed).then(function(opendialog){
	        	if(!opendialog){
	        		saveAndExecuteAction();
	        	}else{
	        		if(confirm && opendialog){
	        			var def = new Promise(function (resolve, reject) {
	        	            Dialog.confirm(self, confirm, {
	        	                confirm_callback: saveAndExecuteAction,
	        	            }).on("closed", null, resolve);
	        	        });
	        		}else{
	        			saveAndExecuteAction();
	        		}
	        	}
	        });
		}
        //	HuuPhong 180522 raise warn when field in line_ids is empty
//		if( modelName ==='ss_erp.inventory.order'){
//		    const record = this.model.get(this.handle, { raw: true });
//		    console.log('Heyo', record);
//
//		    console.log('res ids', record.res_ids);
//		    saveAndExecuteAction();
//		}

		else{
			saveAndExecuteAction();
		}
	},

});

});