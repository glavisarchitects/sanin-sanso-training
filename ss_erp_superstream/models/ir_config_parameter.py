# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     if res.key == 'A007_product_ctg_merchandise' and res.value:
    #         all_linkage_journal_recs = res.env['ss_erp.superstream.linkage.journal'].sudo().search([])
    #         all_linkage_journal_recs._compute_categ_product_id_char(vals['value'])
    #
    #     if res.key == 'A007_sanhot_point_product_id' and res.value:
    #         all_linkage_journal_recs = res.env['ss_erp.superstream.linkage.journal'].sudo().search([])
    #         all_linkage_journal_recs._compute_sanhot_product_id_char(vals['value'])
    #     return res
    #
    # def write(self, vals):
    #     for rec in self:
    #         if rec.key == 'A007_product_ctg_merchandise' and vals.get('value'):
    #             all_linkage_journal_recs = rec.env['ss_erp.superstream.linkage.journal'].sudo().search([])
    #             all_linkage_journal_recs._compute_categ_product_id_char(vals['value'])
    #
    #         if rec.key == 'A007_sanhot_point_product_id' and vals.get('value'):
    #             all_linkage_journal_recs = rec.env['ss_erp.superstream.linkage.journal'].sudo().search([])
    #             all_linkage_journal_recs._compute_sanhot_product_id_char(vals['value'])
    #     return super(IrConfigParameter, self).write(vals)
