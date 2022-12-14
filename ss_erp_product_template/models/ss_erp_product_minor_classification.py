from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMinorClassification(models.Model):
    _name = 'ss_erp.product.minor.classification'
    _description = 'プロダクト小分類'
    _rec_name = 'display_name'

    medium_classification_code = fields.Many2one('ss_erp.product.medium.classification', '中分類コード',)
    minor_classification_code = fields.Char('小分類コード',)
    name = fields.Char('小分類名称')
    remarks = fields.Char('備考')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('minor_classification_code', 'medium_classification_code.display_name', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s/[%s]%s" % (
                rec.medium_classification_code.display_name, rec.minor_classification_code, rec.name)
