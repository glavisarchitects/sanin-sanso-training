from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductDetailClassification(models.Model):
    _name = 'ss_erp.product.detail.classification'
    _description = 'プロダクト詳細分類'
    _rec_name = 'display_name'

    minor_classification_code = fields.Many2one('ss_erp.product.minor.classification', '小分類コード')
    name = fields.Char('詳細分類名称')
    detail_classification_code = fields.Char('詳細分類コード')
    remarks = fields.Char('備考')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('detail_classification_code', 'minor_classification_code.display_name', 'name')
    def _compute_display_name(self):
        self.display_name = "%s/[%s]%s" % (
            self.minor_classification_code.display_name, self.detail_classification_code, self.name)
