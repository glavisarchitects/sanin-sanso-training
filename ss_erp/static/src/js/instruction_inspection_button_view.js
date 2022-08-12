odoo.define('ss_erp.InstructionInspectionView', function (require) {
    "use strict";

    var InstructionInspectionController = require('ss_erp.InstructionInspectionController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var InstructionInspectionView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: InstructionInspectionController
        })
    });

    viewRegistry.add('instruction_inspection_button', InstructionInspectionView);

});
