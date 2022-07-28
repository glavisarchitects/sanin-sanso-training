odoo.define('ss_erp.account_payment_list', function (require) {
    "use strict";
    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (!this.noLeaf && this.hasButtons) {
                this.$buttons.on('click', '.o_list_button_fb_general_transfer', this._onBtnMultiUpdate.bind(this)); // add event listener
            }
        },
        _onBtnMultiUpdate: function (ev) {
//            console.log('result',ev);
            if (ev) {
                ev.stopPropagation();
            }
            var self = this;
            self.do_action({
                name: "Zengin General Transfer FB",
                type: "ir.actions.act_window",
                res_model: "account.payment.wizard",
                target: "new",
                views: [[false, "form"]],
                context: {is_modal: true},
            });

        },
    });
});