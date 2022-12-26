odoo.define('ss_erp.hide_create_btn', function (require) {
"use strict";

    var ListController = require('web.ListController');
    var viewRegistry = require('web.view_registry');
    var ListView = require('web.ListView');

    var ImportDetailListController = ListController.extend({
        updateButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('button.o_list_button_add').hide();

            }
        },

    });

    var DetailListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ImportDetailListController,
        }),
    });
    viewRegistry.add('import_detail_tree', DetailListView);

});