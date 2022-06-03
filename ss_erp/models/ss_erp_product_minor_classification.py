from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMinorClassification(models.Model):
    _name = 'ss_erp.product.minor.classification'
    _description = 'Product Minor Classification'

    major_classification_code = fields.Many2one('ss_erp.product.major.classification','中分類コード',required=True)
    name = fields.Char('大分類名称',store=False)
    minor_classification_code = fields.Char('小分類名称',require=True)
    name_subcategory = fields.Char('小分類名称',required=True)
    remarks = fields.Char('備考')