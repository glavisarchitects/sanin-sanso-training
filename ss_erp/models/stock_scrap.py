from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    x_organization_id = fields.Many2one(
        'ss_erp.organization', string='担当組織',default=lambda self: self.env.user.organization_id)
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string='管轄部門')

    scrap_type = fields.Selection(
        string='廃棄種別',
        selection=[('retained', '長期滞留品の廃棄'),
                   ('expired', '消費期限切れ品の廃棄'),
                   ('damaged', '破損品の廃棄'),
                   ('ingredient_defect', '成分不良品の廃棄'),
                   ('damage_compensation', '配送中の事故による破損補償'),
                   ('products_scrap', '仕掛品・製造品の廃棄'),
                   ],
        required=False, )

