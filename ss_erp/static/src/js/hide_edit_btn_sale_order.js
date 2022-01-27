/* Copyright 2016 Camptocamp SA
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

 odoo.define("ss_erp.hide_edit_button_sale_order", function (require) {
    "use strict";
    var FormController = require("web.FormController");
    var core = require("web.core");

    FormController.include({
        async _update(state, params) {
            return this._super(state, params).then(this.show_hide_buttons(state));
        },
        show_hide_buttons: function (state) {
            var self = this;
            if (self.modelName === "sale.order" && self.model.loadParams && self.model.loadParams.res_id) {
                self._rpc({
                    model: "sale.order",
                    method: "search_read",
                    domain: [["id", "=", self.model.loadParams.res_id]],
                    fields: ["approval_status","state"],
                    limit: 1,
                    }).then(function (result) {
                        console.log(result)
                        if self.$buttons{
                        var button = self.$buttons.find(".o_form_button_edit");
                        if (result[0].approval_status === "in_process") {
                            button.addClass('o_hidden');
                        } else {
                            button.removeClass('o_hidden')
                        };};
                        });
                };
        },
    });
});
