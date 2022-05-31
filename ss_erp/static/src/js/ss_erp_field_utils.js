odoo.define('ss_erp.field_utils.date', function (require) {
"use strict";
// override Datetime function
var session = require('web.session');
var field_utils = require('web.field_utils');
var time = require('web.time');
function MyCustomformatDate(value, field, options) {

//    function formatDate(value, field, options) {
        if (value === false || isNaN(value)) {
            return "";
        }
        if (field && field.type === 'datetime') {
            if (!options || !('timezone' in options) || options.timezone) {
                value = value.clone().add(session.getTZOffset(value), 'minutes');
            }
        }
        var date_format = time.getLangDateFormat();
        if(options.hasOwnProperty('datepicker')){
            if (options.datepicker['showMonthsPeriod'] === true) {
            date_format = (time.getLangDateFormat(), "YYYY年MM月度");
        }
        }
        return value.format(date_format);
//    }
}

field_utils.format.date = MyCustomformatDate;
});