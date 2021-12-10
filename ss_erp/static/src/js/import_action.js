odoo.define("ss_erp.import", function (require) {
    "use strict";
    
    var BaseImport = require("base_import.import")
    var core = require("web.core");

    var QWeb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;
    var session = require('web.session');
    var StateMachine = window.StateMachine;
    
    var DataImportCustom = BaseImport.DataImport.include({

        init: function () {
            this._super.apply(this, arguments);
            this.transformed = false;
        },

        import_options: function () {
            var options = this._super.apply(this, arguments);
            if (this.transformed) {
                options['custom_transform'] = true;
            } else {
                options['custom_transform'] = false;
            }
            return options;
        },

        _getTransformType: function () {
            if (this.res_model === "ss_erp.ifdb.autogas.file.data.rec") {
                return "autogas";
            } else if (this.res_model === "ss_erp.ifdb.powernet.sales.detail") {
                return "powernet";
            } else if (this.res_model === "ss_erp.ifdb.youki.kanri.detail") {
                return "youki_kanri";
            }
        },

        onTransform: function () {
            var transform_type = this._getTransformType();
            this._rpc({
                model: "base_import.import",
                method: `transform_${transform_type}_file`,
                args: [this.id, this.import_options(), this.parent_context],
            }).then(function () {
                $(`.oe_${transform_type}_import_transform`).prop("disabled", true);
                $("input#oe_import_row_start").val(1);
                $("input#oe_import_row_start").prop("disabled", true);
                $("input#oe_import_has_header").prop("checked", true);
                $("input#oe_import_has_header").prop("disabled", true);
                $("input#oe_import_has_header").change();
            });
        },

        renderButtons: function () {
            this._super.apply(this, arguments);
            this.$buttons.filter(".oe_powernet_import_transform").on("click", this.onTransform.bind(this));
            this.$buttons.filter(".oe_autogas_import_transform").on("click", this.onTransform.bind(this));
            this.$buttons.filter(".oe_youki_kanri_import_transform").on("click", this.onTransform.bind(this));
            this.$buttons.filter('.o_import_transform').on('click', function () {
                this.transformed = true;
                this['settings_changed']();
            }.bind(this));
        },

        onpreviewing: function () {
            this._super.apply(this, arguments);
            if (this.res_model === "ss_erp.ifdb.autogas.file.data.rec"
                && this.parent_context.default_import_file_header_model
                && this.parent_context.default_import_file_header_id
                ) {
                this.$buttons.filter(".oe_autogas_import_transform").removeClass("d-none");
            }
            if (this.res_model === "ss_erp.ifdb.powernet.sales.detail"
                && this.parent_context.default_import_file_header_model
                && this.parent_context.default_import_file_header_id
                ) {
                this.$buttons.filter(".oe_powernet_import_transform").removeClass("d-none");
            }
            if (this.res_model === "ss_erp.ifdb.youki.kanri.detail"
                && this.parent_context.default_import_file_header_model
                && this.parent_context.default_import_file_header_id
                ) {
                this.$buttons.filter(".oe_youki_kanri_import_transform").removeClass("d-none");
            }
        },

        onfile_loaded: function () {
            this._super.apply(this, arguments);
            this.transformed = false;
        },

        onpreview_success: function () {
            this._super.apply(this, arguments);
            console.log('import');
            if (this.transformed) {
                this.$buttons.filter('.o_import_transform').addClass('d-none');
            } else {
                this.$buttons.filter('.o_import_transform').removeClass('d-none');
            }
        },

    });

    core.action_registry.add("import_custom", DataImportCustom);
    
    return {
        DataImportCustom: DataImportCustom,
    };

});
