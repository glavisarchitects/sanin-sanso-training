from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMinorClassification(models.Model):
    _name = 'ss_erp.product.minor.classification'
    _description = 'プロダクトマイナー分類'
    _rec_name = 'display_name'

    medium_classification_code = fields.Many2one('ss_erp.product.medium.classification', '中分類コード', required=True)
    minor_classification_code = fields.Char('小分類コード', require=True)
    name = fields.Char('小分類名称')
    remarks = fields.Char('備考')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('minor_classification_code', 'medium_classification_code.display_name', 'name')
    def _compute_display_name(self):
        self.display_name = "%s/[%s]%s" % (
            self.medium_classification_code.display_name, self.minor_classification_code, self.name)
