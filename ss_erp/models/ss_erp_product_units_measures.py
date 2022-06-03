from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductUnitMeasures(models.Model):
    _name = 'ss_erp.product.units.measure'
    _description = 'Product Unit Measures'

    product_id = fields.Many2one('product.product','プロダクトID')
    alternative_uom_id = fields.Char('代替単位')
    converted_value = fields.Float('換算値')
    remarks = fields.Char('備考')
