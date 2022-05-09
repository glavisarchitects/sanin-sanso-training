# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import calendar
import logging

_logger = logging.getLogger(__name__)


class LPGasOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.lpgas.order'
    _description = 'LPガス棚卸伝票'
    _rec_name = 'organization_id'

    organization_id = fields.Many2one('ss_erp.organization', string="組織名")
    inventory_type = fields.Selection([('cylinder_containers', 'シリンダー容器'), ('mini_bulk', 'ミニバルク')], string='棚卸タイプ')
    accounting_date = fields.Datetime(string='会計日')
    inventory_period = fields.Date(string='棚卸対象期間')
    state = fields.Selection(
        [('draft', 'ドラフト'), ('confirm', '集計完了'), ('waiting', '承認待ち'), ('approval', '承認依頼中'), ('approved', '承認済み'),
         ('done', '検証済'), ('cancel', '取消済')], default='draft', string='ステータス')

    # lpgas_order_line_ids = fields.One2many('ss_erp.lpgas.order.line', 'lpgas_order_id', string='集計結果')

    #
    # @api.onchange('accounting_date')
    # def _onchange_partner_id(self):
    #     if self.accounting_date:
    #         self.inventory_period = fields.Date(self.accounting_date)

    #
    def aggregate_lpgas(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ss_erp.lpgas.order.line',
            'views': [[self.env.ref('ss_erp.ss_erp_lpgas_order_line_view_tree').id, 'tree']],
            # 'res_id': self.mrp_production_ids.id,
            'target': 'main',
        }

    @api.model
    def create(self, vals):
        if vals.get('inventory_period'):
            day = calendar.monthrange(int(vals['inventory_period'][0:3]), int(vals['inventory_period'][5:7]))[1]
            vals['inventory_period'] = vals['inventory_period'][:-2] + str(day)
        result = super(LPGasOrder, self).create(vals)
        return result

    # #
    def write(self, vals):
        if vals.get('inventory_period'):
            day = calendar.monthrange(int(vals['inventory_period'][0:3]), int(vals['inventory_period'][5:7]))[1]
            vals['inventory_period'] = vals['inventory_period'][:-2] + str(day)
        result = super(LPGasOrder, self).write(vals)
        return result


class LPGasOrderLine(models.Model):
    _name = 'ss_erp.lpgas.order.line'
    _description = '集計結果'

    # lpgas_order_id = fields.Many2one('ss_erp.lpgas.order')
    organization_id = fields.Many2one('ss_erp.organization', default=lambda self: self.lpgas_order_id.organization_id,
                                      string="組織名")
    location_id = fields.Many2one('stock.location', 'ロケーション')
    tank_capacity = fields.Float('タンク容量')
    product_id = fields.Many2one('product.product', string='プロダクト', )
    meter_reading_date = fields.Date(string='検針日', )
    monthly_usage = fields.Float('当月使用量')
    stock_at_the_time_measure = fields.Float('検針時在庫')
    charge_after_meter_reading = fields.Float('検針後チャージ')
    inventory_at_the_eolm = fields.Float('先月末在庫')
    filling_amount_this_month = fields.Float('当月充填量')
    month_end_inventory = fields.Float('月末在庫')
    uom_id = fields.Many2one('uom.uom', string='単位')
    unified_quantity_unit = fields.Many2one('uom.uom', string='統一数量単位')
    theoretical_eom_inventory = fields.Float(string='理論的な月末在庫')
    inventory__theory_difference = fields.Float(string='棚卸差異')
