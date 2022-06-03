from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMediumClassification(models.Model):
    _name = 'ss_erp.product.medium.classification'
    _description = 'Product Medium Classification'

    major_classification_code = fields.Many2one('ss_erp.product.major.classification','大分類コード')
    name = fields.Char('大分類名称')
    medium_classification_code = fields.Char('中分類コード')
    name_middle_classification = fields.Char('中分類名称')
    remarks = fields.Char('備考')
