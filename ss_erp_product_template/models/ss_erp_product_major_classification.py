from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductMajorClassification(models.Model):
    _name = 'ss_erp.product.major.classification'
    _description = 'プロダクト大分類'
    _rec_name = 'display_name'

    major_classification_code = fields.Char('大分類コード')
    name = fields.Char('大分類名称', )
    remarks = fields.Char('備考')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('major_classification_code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "[%s]%s" % (rec.major_classification_code, rec.name)
