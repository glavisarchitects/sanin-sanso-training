from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMediumClassification(models.Model):
    _name = 'ss_erp.product.medium.classification'
    _description = 'プロダクト中分類'
    _rec_name = 'display_name'

    major_classification_code = fields.Many2one('ss_erp.product.major.classification', '大分類コード')
    name = fields.Char('中分類名称')
    medium_classification_code = fields.Char('中分類コード')
    remarks = fields.Char('備考')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('name', 'major_classification_code.display_name', 'medium_classification_code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s/[%s]%s" % (
                                rec.major_classification_code.display_name, rec.medium_classification_code, rec.name)
