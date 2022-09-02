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
        CATEGORY_SELECTION, string="工事オーダー", default="no", )

