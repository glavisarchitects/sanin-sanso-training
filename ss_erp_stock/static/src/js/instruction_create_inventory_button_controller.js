odoo.define('ss_erp_stock.InstructionCreateInventoryController', function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');
    var _t = core._t;
    var qweb = core.qweb;

    var InventoryValidationController = ListController.extend({
        events: _.extend({
            'click .o_button_instruction_create_inventory': '_onCreateInventory'
        }, ListController.prototype.events),
        /**
         * @override
         */
        init: function (parent, model, renderer, params) {
            var context = renderer.state.getContext();
            this.inventory_id = context.active_id;
            return this._super.apply(this, arguments);
        },

        // -------------------------------------------------------------------------
        // Public
        // -------------------------------------------------------------------------

        /**
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments);
            var $validationButton = $(qweb.render('InstructionDetails.Buttons'));
            this.$buttons.prepend($validationButton);
        },

        // -------------------------------------------------------------------------
        // Handlers
        // -------------------------------------------------------------------------

        /**
         * Handler called when user click on validation button in inventory lines
         * view. Makes an rpc to try to validate the inventory, then will go back on
         * the inventory view form if it was validated.
         * This method could also open a wizard in case something was missing.
         *
         * @private
         */
        _onCreateInventory: function () {

            var self = this;
            var prom = Promise.resolve();
            var recordID = this.renderer.getEditableRecordID();
            var state = this.model.get(this.handle, {raw: true});
            var domain_record = []
            if (this.isDomainSelected) {
                domain_record = state.getDomain()
            }

            if (recordID) {
                // If user's editing a record, we wait to save it before to try to
                // validate the inventory.
                prom = this.saveRecord(recordID);
            }

            prom.then(function () {

                var res_ids = self.getSelectedIds();
                self._rpc({
                    model: 'ss_erp.instruction.order',
                    method: 'action_create_inventory',
                    args: [self.inventory_id, res_ids, domain_record]
                }).then(function (res) {
                    var exitCallback = function (infos) {
                        // In case we discarded a wizard, we do nothing to stay on
                        // the same view...
                        if (infos && infos.special) {
                            return;
                        }
                        // ... but in any other cases, we go back on the inventory form.
                        self.do_notify(
                            false,
                            _t("???????????????????????????????????????"));
                        self.trigger_up('history_back');
                    };

                    if (_.isObject(res)) {
                        self.do_action(res, { on_close: exitCallback });
                    } else {
                        return exitCallback();
                    }
                });
            });
        },
    });

    return InventoryValidationController;

});
