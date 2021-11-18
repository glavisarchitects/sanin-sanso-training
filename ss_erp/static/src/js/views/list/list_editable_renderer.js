odoo.define('ss_erp.EditableListRenderer', function (require) {
"use strict";

/**
 * Editable List renderer
 *
 * The list renderer is reasonably complex, so we split it in two files. This
 * file simply 'includes' the basic ListRenderer to add all the necessary
 * behaviors to enable editing records.
 *
 * Unlike Odoo v10 and before, this list renderer is independant from the form
 * view. It uses the same widgets, but the code is totally stand alone.
 */
var core = require('web.core');
var dom = require('web.dom');
var ListRenderer = require('web.ListRenderer');
var utils = require('web.utils');
const { WidgetAdapterMixin } = require('web.OwlCompatibility');

var _t = core._t;

ListRenderer.include({
   
    _computeDefaultWidths: function () {
        const isListEmpty = !this._hasVisibleRecords(this.state);
        const relativeWidths = [];
        this.columns.forEach(column => {
            const th = this._getColumnHeader(column);
            if (th.offsetParent === null) {
                relativeWidths.push(false);
            } else {
                const width = this._getColumnWidth(column);
                if (width.match(/[a-zA-Z]/)) { // absolute width with measure unit (e.g. 100px)
                    if (isListEmpty) {
                        th.style.width = width;
                    } else {
                        // If there are records, we force a min-width for fields with an absolute
                        // width to ensure a correct rendering in edition
                        th.style.minWidth = width;
                    }
                    relativeWidths.push(false);
                } else { // relative width expressed as a weight (e.g. 1.5)
                    relativeWidths.push(parseFloat(width, 10));
                }
            }
        });

        // Assignation of relative widths
        if (isListEmpty || this.state.model === 'ss_erp.partner.payment.term') {
            const totalWidth = this._getColumnsTotalWidth(relativeWidths);
            for (let i in this.columns) {
                if (relativeWidths[i]) {
                    const th = this._getColumnHeader(this.columns[i]);
                    th.style.width = (relativeWidths[i] / totalWidth * 100) + '%';
                }
            }
            // Manualy assigns trash icon header width since it's not in the columns
            const trashHeader = this.el.getElementsByClassName('o_list_record_remove_header')[0];
            if (trashHeader) {
                trashHeader.style.width = '32px';
                }
            }
        }
    });
});