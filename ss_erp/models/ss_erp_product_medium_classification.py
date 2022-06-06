from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMediumClassification(models.Model):
    _name = 'ss_erp.product.medium.classification'
    _description = 'プロダクト中位分類'
    _rec_name = 'display_name'

    major_classification_code = fields.Many2one('ss_erp.product.major.classification','大分類コード')
    name_major_classification = fields.Char('大分類名称')
    medium_classification_code = fields.Char('中分類コード')
    name = fields.Char('中分類名称')
    remarks = fields.Char('備考')
    display_name = fields.Char(compute='_compute_display_name', store=True)



    @api.depends('name', 'display_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
