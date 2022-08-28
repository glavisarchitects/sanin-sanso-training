odoo.define('ss_erp.InstructionInspectionController', function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');

    var _t = core._t;
    var qweb = core.qweb;

    var InstructionInspectionController = ListController.extend({
        events: _.extend({
            'click .o_button_instruction_inspection': '_onInstructionInspection'
        }, ListController.prototype.events),

        init: function (parent, model, renderer, params) {
            var context = renderer.state.getContext();
            this.inventory_id = context.active_id;
            return this._super.apply(this, arguments);
        },

        _updateSelectionBox: function () {
            this._super.apply(this, arguments);
            var self = this;
            if (self.selectedRecords.length) {
                var ids = this.getSelectedIds()
                self._rpc({
                    model: 'ss_erp.instruction.order',
                    method: 'search_read',
                    domain: [['id', 'in', ids],
                        ['state', '=', 'approved']
                    ],
                    fields: ['id'],
                }).then(function (res) {
                    if (res.length && res.length == self.selectedRecords.length) {
                        var $inspectionButton = $(qweb.render('InstructionInspection.Buttons'));
                        if (!self.$buttons.find('.o_button_instruction_inspection').length) {
                            self.$buttons.prepend($inspectionButton);
                        }
                    } else {
                        self.$buttons.find('.o_button_instruction_inspection').remove()
                    }
                });
            } else {
                self.$buttons.find('.o_button_instruction_inspection').remove()
            }
        },

        _onInstructionInspection: function () {
            var self = this;
            var prom = Promise.resolve();
            var recordID = this.renderer.getEditableRecordID();
            if (recordID) {
                // If user's editing a record, we wait to save it before to try to
                // validate the inventory.
                prom = this.saveRecord(recordID);
            }

            prom.then(function () {
                self._rpc({
                    model: 'ss_erp.instruction.order',
                    method: 'action_inspection',
                    args: [self.getSelectedIds()]
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
                            _t("The Instruction has been verify"));
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

    return InstructionInspectionController;

});
