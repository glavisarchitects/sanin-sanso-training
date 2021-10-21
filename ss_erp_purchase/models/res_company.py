# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.translate import html_translate

class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_default_notes_construction_contract(self):
        result = _("""
            <div>
                <div>According to the construction outline and construction method "attached design document".</div>
                <div>Construction conditions / scope According to "Attachment design document" and "Construction plan".</div>
                <div>Estimated price and estimated period for subcontracting work.</div>
            </div>""")

        return result

    def _get_default_estimated_subcontracting_work(self):
        result = _("""
            <div>
                <div>Construction work less than 5 million yen for 1 day or more.</div>
                <div>Construction work of 5 million yen or more and less than 50 million yen for 10 days or more.</div>
                <div>Construction work of 50 million yen or more 15 days or more during.</div>
            </div>""")

        return result

    x_construction_contract_notice = fields.Html("Notes on construction contract", default=_get_default_notes_construction_contract, copy=False, translate=html_translate, sanitize=False)
    x_construction_subcontract = fields.Html("Estimated price and estimated period for subcontracting work", default=_get_default_estimated_subcontracting_work, copy=False, translate=html_translate, sanitize=False)
