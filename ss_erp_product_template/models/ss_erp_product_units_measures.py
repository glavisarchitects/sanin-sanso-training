from odoo import models, api, fields, _
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from odoo.fields import Datetime, Date


class ProductUnitMeasures(models.Model):
    _name = 'ss_erp.product.units.measure'
    _description = 'プロダクト単位測定'

    product_template_id = fields.Many2one('product.template','プロダクトテンプレートID')
    alternative_uom_id = fields.Many2one('uom.uom','代替単位')
    converted_value = fields.Float('換算値')
    remarks = fields.Char('備考')
    name = fields.Char('製品単位の測定名前')


