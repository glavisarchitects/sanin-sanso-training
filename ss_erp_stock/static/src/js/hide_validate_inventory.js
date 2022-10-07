odoo.define('ss_erp_stock.hide_validate_btn', function (require) {
"use strict";
    
    var ListController = require('web.ListController');
    var viewRegistry = require('web.view_registry');
    var ListView = require('web.ListView');

    var InventoryValidationController = ListController.extend({
        updateButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('button.o_button_validate_inventory').hide();
            }
        },

    });

    var InventoryValidationView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: InventoryValidationController,
        }),
    });
    viewRegistry.add('custom_validate_inventory_btn_hide', InventoryValidationView);

});