odoo.define('ss_erp.account_payment_list', function (require) {
    "use strict";
    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (!this.noLeaf && this.hasButtons) {
                this.$buttons.on('click', '.o_list_button_fb_general_transfer', this._onBtnMultiUpdate.bind(this)); // add event listener
                this.$buttons.on('click', '.o_list_button_account_transfer_request_fb', this._onBtnMultiUpdate2.bind(this)); // add event listener
            }
        },
        _onBtnMultiUpdate: function (ev) {
//            console.log('result',ev);
            if (ev) {
                ev.stopPropagation();
            }
            var self = this;
            self.do_action({
                name: "全銀総合振込FB作成",
                type: "ir.actions.act_window",
                res_model: "comprehensive.create.zengin.fb",
                target: "new",
                views: [[false, "form"]],
                context: {is_modal: true},
            });

        },

        _onBtnMultiUpdate2: function (ev) {
            if (ev) {
                ev.stopPropagation();
            }
            var self = this;
            self.do_action({
                name: "全銀口座振替依頼FB作成",
                type: "ir.actions.act_window",
                res_model: "zengin.account.transfer.request.fb",
                target: "new",
                views: [[false, "form"]],
                context: {is_modal: true},
            });

        },

        updateButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                if (this.renderer.state.context.default_move_type === 'out_invoice'){
                    this.$buttons.find('.o_list_button_account_transfer_request_fb').show();
                } else {
                    this.$buttons.find('.o_list_button_account_transfer_request_fb').hide();
                }

                if (this.renderer.state.context.default_payment_type === 'outbound'){
                    this.$buttons.find('.o_list_button_fb_general_transfer').show();
                } else {
                    this.$buttons.find('.o_list_button_fb_general_transfer').hide();
                }

            }
        },

    });
});

