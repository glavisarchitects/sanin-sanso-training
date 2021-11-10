odoo.define('ss_erp.hide_edit_btn', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var core = require('web.core');
    var _t = core._t;

    FormController.include({
        async _update(state, params) {
            return this._super(state, params).then(this.hide_button(state));
        },
        show_hide_edit_button: function (access) {
            if (this.$buttons) {
                var button = this.$buttons.find(".o_form_button_edit");
                if (button) {
                    // button.prop("disabled", !access);
                    if (!access){
                        button.addClass('o_hidden');
                    }
                    else {
                        button.removeClass('o_hidden')
                    }
                }
            }
        },
        hide_button: function (state) {
            var accesses = this._rpc({
                model: this.modelName,
                method: "check_access_rule_all",
                args: [[state.data.id], ["write"]],
            });
            this.show_hide_edit_button(accesses.write);

            if (this.$buttons && this.mode === 'readonly') {
                var self = this;
                var attrs = this.renderer.arch.attrs;
                var action_edit = ['edit','create'];
                _.each(action_edit, function (action) {
                    var expr = attrs['qth_' + action];
                    var res = expr ? self._evalExpression(expr) : self.activeActions[action];
                    if (!res){
                        self.$buttons.find('.btn.btn-primary.o_form_button_' + action).addClass('o_hidden');
                    }
                    else {
                        self.$buttons.find('.btn.btn-primary.o_form_button_' + action).removeClass('o_hidden')
                    }
                    // self.$buttons.find('.btn.btn-primary.o_form_button_' + action).toggleClass('o_hidden', !res);
                });
            }
            return true;
        },

        _evalExpression: function (expr) {
            //https://openerp-web-v7.readthedocs.io/en/stable/#convert-js
            var tokens = py.tokenize(expr);
            var tree = py.parse(tokens);
            var evalcontext = this.renderer.state.evalContext;
            var expr_eval = py.evaluate(tree, evalcontext);
            return py.PY_isTrue(expr_eval);
        }
    });
});
