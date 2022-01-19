/* Copyright 2016 Camptocamp SA
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

 odoo.define("ss_erp.hide_edit_btn_with_rule", function (require) {
    "use strict";
    var FormController = require("web.FormController");
    var core = require("web.core");

    FormController.include({
        async _update(state, params) {
            return this._super(state, params).then(this.show_hide_buttons(state));
        },
        show_hide_buttons: function (state) {
            var self = this;
            return self
                ._rpc({
                    model: this.modelName,
                    method: "check_access_rule_all",
                    args: [[state.data.id], ["write"]],
                })
                .then(function (accesses) {
                    self.show_hide_edit_button(accesses.write);
                });
        },
        show_hide_edit_button: function (access) {
            if (this.$buttons) {
                var button = this.$buttons.find(".o_form_button_edit");
                // if (button) {
                //     // button.prop("disabled", !access);
                //     if (!access){
                //         button.addClass('o_hidden');
                //     }
                //     else {
                //         button.removeClass('o_hidden')
                //     }
                // }
            }
        },
        renderButtons: function(param) {
            this._super(param);
            this.showHideApprovalEditButton();
        },
        updateButtons: function() {
            this._super();
            this.showHideApprovalEditButton();
        },
        showHideApprovalEditButton: function() {
            var self = this;
            if (self.modelName === "approval.request" &&
                self.model.loadParams &&
                self.model.loadParams.res_id) {
                self._rpc({
                    model: "approval.request",
                    method: "search_read",
                    domain: [["id", "=", self.model.loadParams.res_id]],
                    fields: ["request_status"],
                    limit: 1,
                }).then(function(result) {
                    if (result.length) {
                        var $recordState = result[0].request_status;
                        if ($recordState !== "new") {
                            self.$buttons.find(".o_form_button_edit").hide(0);
                        } else {
                            self.$buttons.find(".o_form_button_edit").show(0);
                        }
                    }
                });
            }
        },
    });
});
