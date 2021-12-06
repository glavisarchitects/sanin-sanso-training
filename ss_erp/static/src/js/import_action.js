odoo.define("ss_erp.import", function (require) {
    "use strict";
    
    var BaseImport = require("base_import.import")
    var core = require("web.core");
    var session = require('web.session');
    
    var DataImportCustom = BaseImport.DataImport.include({
        init: function () {
            this._super.apply(this, arguments);
            this.transformed = false;
        },
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
        renderButtons: function () {
            this._super.apply(this, arguments);
            this.$buttons.filter('.oe_powernet_import_transform').on('click', this.ontransform.bind(this));
            this.$buttons.filter(".oe_autogas_import_transform").on("click", function () {
                this._rpc({
                    model: "base_import.import",
                    method: "transform_autogas_file",
                    args: [this.id, this.import_options()],
                }).then(function () {
                    $(".oe_autogas_import_transform").prop("disabled", true);
                    $("input#oe_import_row_start").val(2);
                    $("input#oe_import_row_start").prop("disabled", true);
                    $("input#oe_import_has_header").prop("checked", true);
                    $("input#oe_import_has_header").prop("disabled", true);
                    $("input#oe_import_has_header").change();
                });
                this.transformed = true;
            }.bind(this));
        },
        onpreviewing: function () {
            this._super.apply(this, arguments);
            if (this.res_model === "ss_erp.ifdb.autogas.file.data.rec") {
                this.$buttons.filter(".oe_autogas_import_transform").removeClass("d-none");
            }
        },
    });
    core.action_registry.add("import_custom", DataImportCustom);
    
    return {
        DataImportCustom: DataImportCustom,
    };
});
