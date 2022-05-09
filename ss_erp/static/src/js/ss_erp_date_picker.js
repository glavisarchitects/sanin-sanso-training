odoo.define('ss_erp.datepicker', function (require) {
"use strict";
    var field_registry = require('web.field_registry');
    var DatePicker = require('web.datepicker');
    var time = require('web.time');
    var fields = require('web.basic_fields');

    var DatePickerOptions = DatePicker.DateWidget.include({

        init: function (parent, options) {
            this._super(parent, options);
            if (this.options.showMonthsPeriod) {
                this.options.format = 'YYYY年MM月 度';
//                console.log('xxx', time.getLangDateFormat())
            }

        },
    });

//    field_registry.add('datepicker_widget', DatePickerOptions);
//    return DatePickerOptions;

});