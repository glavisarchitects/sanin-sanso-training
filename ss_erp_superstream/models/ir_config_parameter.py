# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    def write(self, vals):
        for rec in self:
            if rec.key == 'A007_product_ctg_merchandise' and vals.get('value'):
                all_linkage_journal_recs = rec.env['ss_erp.superstream.linkage.journal'].search([])
                all_linkage_journal_recs._compute_categ_product_id_char(vals['value'])

            if rec.key == 'A007_sanhot_point_product_id' and vals.get('value'):
                all_linkage_journal_recs = rec.env['ss_erp.superstream.linkage.journal'].search([])
                all_linkage_journal_recs._compute_sanhot_product_id_char(vals['value'])
        return super(IrConfigParameter, self).write(vals)
