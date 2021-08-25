from odoo import models, fields, _, api


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order"]
    _description = "sanin-sanso sale"

    # TODO: all fields set char for mockup
    # TODO: ERD model

    # x_sales_organization = fields.One2many(string='販売組織', required=False)
    x_sales_organization = fields.Char(string='販売組織', required=False)

    # x_shipping_information = fields.Char(string='配送情報', required=False)

    # x_campaign = fields.Char(string='キャンペーン', required=False)

    #x_expected_delivery_date = fields.Char(string='納期予定日', default=fields.Date.today, required=True)

    x_application_destination = fields.Char(string='申請先', required=False)

    x_desired_approval_date = fields.Char(string='承認希望日', default=fields.Date.today, required=True)

    x_remark = fields.Selection([
        ('x_remark_1', 'x_remark 1'),
        ('x_remark_2', 'x_remark 2')],
        string='備考', default='x_remark_1')

    x_application = fields.Char(string='申請', required=False)

    x_judgment = fields.Char(string='判断', required=False)

    x_reason = fields.Char(string='理由', required=False)

    x_decision = fields.Char(string='決定', required=False)

    def x_request_rfq(self):
        print("##########################################", self.x_reason)