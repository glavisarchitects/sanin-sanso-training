odoo.define('ss_erp_stock.datepicker', function (require) {
"use strict";
    var field_registry = require('web.field_registry');
    var DatePicker = require('web.datepicker');
    var time = require('web.time');
    var fields = require('web.basic_fields');
    var field_utils = require('web.field_utils');
    var translation = require('web.translation');

    var _t = translation._t;

    var DatePickerOptions = DatePicker.DateWidget.include({

        init: function (parent, options) {
            this._super(parent, options);
            var lang = _t.database.parameters.name
            if (this.options.showMonthsPeriod === true && lang == 'Japanese / 日本語') {
                this.options.format = (time.getLangDateFormat(), "YYYY年MM月度");
            }
        },
    });
    return DatePickerOptions;
});