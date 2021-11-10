odoo.define('ss_erp.BasicController', function (require) {
"use strict";
var Dialog = require('web.Dialog');
var BasicController = require('web.BasicController');
BasicController.include({
    _deleteRecords: function (ids) {
        var self = this;
        var _super = this._super.bind(this, ids);
        if (self.modelName === 'x.partner.rebate') {
            Dialog.confirm(self, _t("Are you sure you want to delete this record ?"), {
                confirm_callback: _super,
            });
            self.confirmOnDelete = false;
        } else {
            _super();
        }
    },
});
});