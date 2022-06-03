from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductDetailClassification(models.Model):
    _name = 'ss_erp.product.detail.classification'
    _description = 'Product Detail Classification'


    minor_classification_code = fields.Many2one('ss_erp.product.minor.classification','大分類コード')
    name = fields.Char('小分類名称')
    detail_classification_code = fields.Char('詳細分類コード')
    name_middle_classification = fields.Char('詳細分類名称')
    remarks = fields.Char('備考')
