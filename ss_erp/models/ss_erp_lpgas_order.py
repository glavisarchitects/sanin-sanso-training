# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import dateutil.relativedelta
import calendar
import logging

_logger = logging.getLogger(__name__)


class LPGasOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.lpgas.order'
    _description = 'LPガス棚卸伝票'
    _rec_name = 'name'

    name = fields.Char('LPガス棚卸参照')
    organization_id = fields.Many2one('ss_erp.organization', string="組織名")
    inventory_type = fields.Selection([('cylinder', 'シリンダー'), ('minibulk', 'ミニバルク')], string='棚卸種別')
    accounting_date = fields.Date(string='会計日')
    aggregation_period = fields.Date(string='棚卸対象期間')
    month_aggregation_period = fields.Integer(string='month of aggregation period',
                                              compute='compute_month_aggregation_period')
    state = fields.Selection(
        [('draft', 'ドラフト'), ('confirm', '集計完了'), ('waiting', '承認待ち'), ('approval', '承認依頼中'), ('approved', '承認済み'),
         ('done', '検証済'), ('cancel', '取消済')], default='draft', string='ステータス')

    lpgas_order_line_ids = fields.One2many('ss_erp.lpgas.order.line', 'lpgas_order_id', string='集計結果')


    #
    # @api.onchange('accounting_date')
    # def _onchange_partner_id(self):
    #     if self.accounting_date:
    #         self.aggregation_period = fields.Date(self.accounting_date)

    @api.depends('aggregation_period')
    def compute_month_aggregation_period(self):
        """ compute """
        for rec in self:
            rec.month_aggregation_period = int(rec.aggregation_period.month)

    #
    def aggregate_lpgas(self):
        branch_warehouse = self.organization_id.warehouse_id
        if not branch_warehouse:
            raise UserError(_("Your branch have not warehouse please re config again!"))
        warehouse_view_location = branch_warehouse.view_location_id
        warehouse_gas_customer_location = self.env['stock.location'].search(
            [('id', 'child_of', warehouse_view_location.id), ('usage', '=', 'customer')])

        lp_gas_order_line = []
        for loc in warehouse_gas_customer_location:
            if loc.x_inventory_type not in ['cylinder', 'minibulk']:
                continue
            sml_customer_used = self.env['stock.move.line'].search([('location_id', '=', loc.id), ])
            used_amount = sum(sml.qty_done for sml in sml_customer_used)
            remaining_amount = loc.x_total_installation_quantity - used_amount

            sml_provided_to_customer = self.env['stock.move.line'].search([('location_dest_id', '=', loc.id), ])
            provided_amount = sum(sml.qty_done for sml in sml_provided_to_customer)
            actual_end_this_month = provided_amount + remaining_amount

            # Get amount end of last month
            amount_end_last_month = 0
            period_last_month = self.aggregation_period + dateutil.relativedelta.relativedelta(months=-1)
            last_month_lpgas = self.search([('month_aggregation_period', '=', period_last_month.month)], limit=1)
            if last_month_lpgas:
                last_month_lpgas_result = last_month_lpgas.lpgas_order_line_ids.filtered(
                    lambda i: i.location_id == loc.id)
                if last_month_lpgas_result:
                    amount_end_last_month = last_month_lpgas_result.this_month_inventory

            theory_end_this_month = amount_end_last_month + provided_amount - remaining_amount
            difference_qty = actual_end_this_month - theory_end_this_month
            vals = {
                'organization_id': self.organization_id.id,
                'location_id': loc.id,
                'meter_reading_date': self.aggregation_period.replace(day=18),
                'tank_capacity': loc.x_total_installation_quantity,
                'month_amount_of_use': used_amount,
                'this_month_filling': provided_amount,
                'meter_reading_inventory': remaining_amount,
                'this_month_inventory': actual_end_this_month,
                'theoretical_inventory': theory_end_this_month,
                'difference_qty': difference_qty,
            }
            lp_gas_order_line.append((0, 0, vals))
            # print('lp_gas_order_line', lp_gas_order_line)
        self.lpgas_order_line_ids = lp_gas_order_line
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ss_erp.lpgas.order.line',
            'views': [[self.env.ref('ss_erp.ss_erp_lpgas_order_line_view_tree').id, 'tree']],
            'domain': [('id', '=', self.id)],
            'target': 'main',
        }

    #   when create and write make aggregation_period date default is end of this month
    @api.model
    def create(self, vals):
        if vals.get('aggregation_period'):
            day = calendar.monthrange(int(vals['aggregation_period'][0:3]), int(vals['aggregation_period'][5:7]))[1]
            vals['aggregation_period'] = vals['aggregation_period'][:-2] + str(day)
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('lpgas.order.name') or _('New')
        result = super(LPGasOrder, self).create(vals)
        return result

    # #
    def write(self, vals):
        if vals.get('aggregation_period'):
            day = calendar.monthrange(int(vals['aggregation_period'][0:3]), int(vals['aggregation_period'][5:7]))[1]
            vals['aggregation_period'] = vals['aggregation_period'][:-2] + str(day)
        result = super(LPGasOrder, self).write(vals)
        return result

    @api.constrains("accounting_date", "aggregation_period")
    def _check_accounting_date_aggregation_period(self):
        for r in self:
            if r.accounting_date < r.aggregation_period:
                raise ValidationError(_("会計日は棚卸対象期間より過去の日付は設定できません。"))

class LPGasOrderLine(models.Model):
    _name = 'ss_erp.lpgas.order.line'
    _description = '集計結果'
    _rec_name = 'name'

    name = fields.Char(default='集計結果')
    lpgas_order_id = fields.Many2one('ss_erp.lpgas.order')
    organization_id = fields.Many2one('ss_erp.organization', default=lambda self: self.lpgas_order_id.organization_id,
                                      string="組織名")
    location_id = fields.Many2one('stock.location', 'ロケーション')
    tank_capacity = fields.Float('タンク容量')
    # product_id = fields.Many2one('product.product', string='プロダクト', )
    meter_reading_date = fields.Date(string='検針日', )
    month_amount_of_use = fields.Float('当月使用量')
    meter_reading_inventory = fields.Float('検針時在庫')
    # charge_after_meter_reading = fields.Float('検針後チャージ')

    filling_after_meter_reading = fields.Float('検針後設置数量')
    previous_last_inventory = fields.Float('先月末在庫')
    this_month_filling = fields.Float('当月充填量')
    this_month_inventory = fields.Float('月末在庫')
    # uom_id = fields.Many2one('uom.uom', string='単位')
    # unified_quantity_unit = fields.Many2one('uom.uom', string='統一数量単位')
    theoretical_inventory = fields.Float(string='理論的な月末在庫')
    difference_qty = fields.Float(string='棚卸差異')

