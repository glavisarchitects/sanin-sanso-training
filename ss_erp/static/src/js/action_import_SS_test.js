odoo.define('ss_erp.import', function (require) {
"use strict";

var BaseImport = require('base_import.import');
var core = require('web.core');

var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;
var session = require('web.session');
var StateMachine = window.StateMachine;

var DataImportPowerNetSales = BaseImport.DataImport.include({
    import_options: function () {
        var options = this._super();
        options['import_custom'] = false;
        return options;
    },
    ontransform: function (event, from, to, arg) {
        console.log('TTTTTTTTT',this.import_options());
        var options = this.import_options();
        options['import_custom'] = true;
        var self = this;
        this._rpc({
            model: 'base_import.import',
            method: 'parse_preview',
            args: [this.id, options],
            kwargs: {context: session.user_context},
            }).then(function(result) {
                return self.onpreview_success(event, from, to, result);
        });
    },
    _batchedImport: function (opts, args, kwargs, rec) {
        opts['import_custom'] = true;
        return this._super(opts, args, kwargs, rec);
    },
    renderButtons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("ImportView.buttons", this));
        this.$buttons.filter('.o_import_validate').on('click', this.validate.bind(this));
        //custom import
        this.$buttons.filter('.oe_powernet_import_transform').on('click', this.ontransform.bind(this));

        this.$buttons.filter('.o_import_import').on('click', this.import.bind(this));
        this.$buttons.filter('.oe_import_file').on('click', function () {
            self.$('.o_content .oe_import_file').click();
        });
        this.$buttons.filter('.o_import_cancel').on('click', function(e) {
            e.preventDefault();
            self.exit();
        });
    },
});
core.action_registry.add('import_powernet_sales', DataImportPowerNetSales);

return {
    DataImportPowerNetSales: DataImportPowerNetSales,
};
});