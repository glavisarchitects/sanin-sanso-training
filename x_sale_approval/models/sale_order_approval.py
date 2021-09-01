from odoo import fields, models, api


class SaleOrderApproval(models.Model):
    _name = 'sale.order.approval'
    _description = 'Sale Order Approval For Quotation'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string='sale_order_id', required=False)

    crm_team_id = fields.Many2one("crm.team", string="申請先", required=True)
    x_deadline = fields.Date(string='承認希望日', required=False, default=fields.Date.today, help='Deadline')
    x_comment = fields.Char(string='備考', required=False, help='comment')
    x_reason = fields.Char(string='理由', required=False, help='reason')
    x_state = fields.Selection(string='判断', selection=[('approved', 'Approved'), ('reject', 'Reject'), ('cancel', 'Cancel'), ], required=False, help='state')

    # add new column not in design
    x_create = fields.Date(string='Create', required=False, default=fields.Date.today, help='Create Date')
