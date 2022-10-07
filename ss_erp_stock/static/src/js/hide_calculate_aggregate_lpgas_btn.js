odoo.define('ss_erp_stock.hide_aggregate_lpgas_btn', function (require) {
    "use strict";
    var FormController = require('web.FormController');
    var MyFormController = FormController.include({
        updateButtons: function () {
            this._super.apply(this, arguments);
            var edit_mode = (this.mode === 'edit');

            if (edit_mode){
                if(this.renderer.$('.o_aggregate_lpgas_btn')){
                    this.renderer.$('.o_aggregate_lpgas_btn').addClass('d-none');
                }

            }

        },

    });
});