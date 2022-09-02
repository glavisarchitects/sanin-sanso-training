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
                options['header_id'] = this.parent_context['default_import_file_header_id'];
            } else {
                options['custom_transform'] = false;
                options['header_id'] = this.parent_context['default_import_file_header_id'];
            }
            return options;
        },

        _getTransformType: function () {
            switch (this.res_model) {
                case "ss_erp.ifdb.autogas.file.data.rec":
                    return "autogas";
                case "ss_erp.ifdb.powernet.sales.detail":
                    return "powernet";
                case "ss_erp.ifdb.youki.kanri.detail":
                    return "youki_kanri";
                case "ss_erp.ifdb.youkikensa.billing.file.detail":
                    return "youki_kensa";
                case "ss_erp.ifdb.propane.sales.detail":
                    return "propane";
                case "ss_erp.account.transfer.result.line":
                    return "account_transfer";
                case "ss_erp.account.receipt.notification.line":
                    return "account_receipt";
            }
        },

        onTransform: function () {
            console.log('run here')
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
            this.$buttons.filter(".oe_youki_kensa_import_transform").on("click", this.onTransform.bind(this));
            this.$buttons.filter(".oe_propane_import_transform").on("click", this.onTransform.bind(this));
            this.$buttons.filter(".o_account_transfer_import_transform").on("click", this.onTransform.bind(this));
            this.$buttons.filter(".o_account_receipt_import_transform").on("click", this.onTransform.bind(this));
            this.$buttons.filter('.o_import_transform').on('click', function () {
                this.transformed = true;
                this['settings_changed']();
            }.bind(this));

            this.$buttons.filter('.o_import_validate').on('click', function(){
                var self = this;
                this._rpc({
                    model: 'base_import.import',
                    method: 'parse_preview',
                    args: [this.id, this.import_options()],
                    }).then(function (data) {
                    const header_data = data.headers;
                    const preview_data = data.preview;
//                    self.val = _.map(prices, v => [v[9]])
//                    var iterator = self.val.values();

                    var price_unit_col = -1
                    for (let index = 0, len = header_data.length; index < len; ++index) {
                         if(header_data[index] === "price_unit" || header_data[index] === "単価"){
                            price_unit_col = index
                         }
                    }
                    if(price_unit_col != -1){
                        for (let row_data = 0, len = preview_data.length; row_data < len; ++row_data) {
                            if(preview_data[row_data][price_unit_col] === ""){
                                    var message = _t("単価がブランクのレコードはあります。ご確認ください。");
                                    self.do_warn(_t("Warning"), message,false);
                                    return Promise.resolve();
                            }
                        }
                    }
                });
            }.bind(this));
        },

        onpreviewing: function () {
            this._super.apply(this, arguments);
            if (
                    this.parent_context.default_import_file_header_id
                &&  this.parent_context.default_import_file_header_model
                ) {
                    switch (this.res_model) {
                        case "ss_erp.ifdb.autogas.file.data.rec":
                            this.$buttons.filter(".oe_autogas_import_transform").removeClass("d-none");
                            break;
                        case "ss_erp.ifdb.powernet.sales.detail":
                            this.$buttons.filter(".oe_powernet_import_transform").removeClass("d-none");
                            break;
                        case "ss_erp.ifdb.youki.kanri.detail":
                            this.$buttons.filter(".oe_youki_kanri_import_transform").removeClass("d-none");
                            break;
                        case "ss_erp.ifdb.youkikensa.billing.file.detail":
                            this.$buttons.filter(".oe_youki_kensa_import_transform").removeClass("d-none");
                            break;
                        case "ss_erp.ifdb.propane.sales.detail":
                            this.$buttons.filter(".oe_propane_import_transform").removeClass("d-none");

                    }
                }
            if (this.parent_context.default_account_transfer_result_header_id){
                this.$buttons.filter(".o_account_transfer_import_transform").removeClass("d-none");
            }
            if (this.parent_context.default_account_receipt_result_header_id){
                this.$buttons.filter(".o_account_receipt_import_transform").removeClass("d-none");
            }
            if (this.transformed) {
                this.$buttons.filter('.o_import_transform').addClass('d-none');
            } else {
                this.$buttons.filter('.o_import_transform').removeClass('d-none');
            }
        },

        onfile_loaded: function () {
            this._super.apply(this, arguments);
            this.transformed = false;
        },


    });

    core.action_registry.add("import_custom", DataImportCustom);
    
    return {
        DataImportCustom: DataImportCustom,
    };

});
