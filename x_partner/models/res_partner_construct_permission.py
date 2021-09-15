from odoo import fields, models


class PartnerConstructionPermit(models.Model):
    _name = "x.x_partner.partner_construction_permit"
    _description = "Partner Construction Permit"
    
    name = fields.Char(string="許可番号", required=True)
    construction_permit_type_id = fields.Char(string="許可の種類", required=True)
    authorize_classification = fields.Char(string="大臣･知事区分", required=True)
    type_classification = fields.Char(string="特定･一般区分", required=True)
    permission_date = fields.Date(string="許可年月日", default=fields.Date.today)
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Contact", domain="[('company_type', '=', 'company')]",
        readonly=True, copy=False, ondelete="cascade", required=True
    )
