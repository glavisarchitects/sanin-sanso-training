from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMinorClassification(models.Model):
    _name = 'ss_erp.product.minor.classification'
    _description = 'プロダクトマイナー分類'
    _rec_name = 'display_name'

    major_classification_code = fields.Many2one('ss_erp.product.major.classification','中分類コード',required=True)
    name_middle_classification = fields.Char('中分類名称',store=False)
    minor_classification_code = fields.Char('小分類名称',require=True)
    name = fields.Char('小分類名称')
    remarks = fields.Char('備考')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('minor_classification_code', 'display_name')
    def _compute_display_name(self):
        self.display_name = self.minor_classification_code