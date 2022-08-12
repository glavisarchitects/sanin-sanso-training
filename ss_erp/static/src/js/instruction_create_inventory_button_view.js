odoo.define('ss_erp.InstructionCreateInventoryView', function (require) {
    "use strict";

    var InstructionCreateInventoryController = require('ss_erp.InstructionCreateInventoryController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var InstructionCreateInventoryView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: InstructionCreateInventoryController
        })
    });

    viewRegistry.add('instruction_create_inventory_button', InstructionCreateInventoryView);

});
