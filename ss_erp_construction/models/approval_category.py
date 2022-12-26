# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

CATEGORY_SELECTION = [
    ('required', '必須'),
    ('optional', 'オプション'),
    ('no', 'なし')]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_construction_order_id = fields.Selection(
        CATEGORY_SELECTION, string="工事オーダ", default="no", )
    has_construction_order_id2 = fields.Selection(
        CATEGORY_SELECTION, string="工事見積書", default="no", )
    has_construction_template_id = fields.Selection(
        CATEGORY_SELECTION, string="工事テンプレート", default="no", )

