odoo.define('ss_erp.web_notify', function (require) {
"use strict";
var core = require('web.core');
var ListRenderer = require('web.ListRenderer');
var BasicController = require("web.BasicController");
var _t = core._t;

    ListRenderer.include({
        _notifyInvalidFields: function (invalidFields) {
            var fields = this.state.fields;
            var warnings = invalidFields.map(function (fieldName) {
                var fieldStr = fields[fieldName].string;
                return _.str.sprintf('<li>%s</li>', _.escape(fieldStr));
            });
            warnings.unshift('<ul>');
            warnings.push('</ul>');
            this.do_warn(_t("Invalid fields:"), warnings.join(''));
        },
        canBeSaved: function (recordID) {
            var self = this;
//            console.log('canBeSavedrecordID',this.state.model);
            if (this.state.model === 'ss_erp.inventory.order.line') {
                recordID = this.getEditableRecordID();
                if (recordID === null) {
                    return [];
                }
            var fieldNames = this._super(recordID);
            this._notifyInvalidFields(fieldNames);
            return fieldNames;
            }
            return Promise.resolve(true);
        },
    });

    BasicController.include({
        canBeDiscarded: function (recordID) {
            var self = this;
//            console.log('canBeDiscardedrecordID',this.model.loadParams.modelName);
            if  (this.model.loadParams.modelName === 'ss_erp.inventory.order.line'){
                if (this.isDirty(recordID)) {
                    return Promise.resolve(false);
                }
                // discard dialog is already close
                if (this.discardingDef) {
                    return Promise.resolve(true);
                }
            }

            return Promise.resolve(true);

        },

    });

});

