from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMajorClassification(models.Model):
    _name = 'ss_erp.product.major.classification'
    _description = 'ProductMajorClassification'

    major_classification_code = fields.Char('大分類コード',required=True)
    name = fields.Char('大分類名称',required=True)
    remarks = fields.Char('備考')
