odoo.define('ss_erp.hide_edit_btn', function (require) {
"use strict";

    var FormController = require('web.FormController');
    var viewRegistry = require('web.view_registry');
    var FormView = require('web.FormView');

    var MyFormController = FormController.extend({
        updateButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
//                console.log('7777',this.renderer.state.data);
                if (this.renderer.state.data.approval_status ==='in_process'|| this.renderer.state.data.approval_status ==='approved'){
                    this.renderer.$('.o_field_x2many_list_row_add').addClass('d-none');
                    this.renderer.$('.o_list_record_remove').addClass('d-none');
                } else {
                    this.renderer.$('.o_field_x2many_list_row_add').show;
                }
            }
        },

    });

    var MyFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: MyFormController,
        }),
    });
    viewRegistry.add('custom_form', MyFormView);

});