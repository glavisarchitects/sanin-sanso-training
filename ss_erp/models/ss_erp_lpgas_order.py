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
    user_organization_ids = fields.Many2many('ss_erp.organization', default=lambda self: self.env.user.organization_ids.ids)
    organization_id = fields.Many2one('ss_erp.organization', string="組織名", domain="[('id','in', user_organization_ids)]")
    inventory_type = fields.Selection([('cylinder', 'シリンダー'), ('minibulk', 'ミニバルク')], string='棚卸種別')
    accounting_date = fields.Date(string='会計日')
    aggregation_period = fields.Date(string='棚卸対象期間')
    month_aggregation_period = fields.Integer(string='month of aggregation period', store=True,
                                              compute='compute_month_aggregation_period')
    state = fields.Selection(
        [('draft', 'ドラフト'), ('confirm', '集計完了'), ('waiting', '承認待ち'), ('approval', '承認依頼中'), ('approved', '承認済み'),
         ('done', '検証済'), ('cancel', '取消済')], default='draft', string='ステータス')

    lpgas_order_line_ids = fields.One2many('ss_erp.lpgas.order.line', 'lpgas_order_id', ondelete="cascade", string='集計結果')

    @api.depends('aggregation_period')
    def compute_month_aggregation_period(self):
        """ compute """
        for rec in self:
            if rec.aggregation_period:
                rec.month_aggregation_period = int(rec.aggregation_period.month)
            else:
                rec.month_aggregation_period = False

    def _compute_user_organization_ids(self):
        for rec in self:
            rec.user_organization_ids = rec.env.user.organization_ids

    #
    def calculate_aggregate_lpgas(self):

        # calculate cylinder
        lpgas_product_id = self.env['ir.config_parameter'].sudo().get_param('lpgus.order.propane_gas_id')
        if not lpgas_product_id:
            raise UserError(_("プロダクトコードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。"))

        branch_warehouse = self.organization_id.warehouse_id
        warehouse_location = branch_warehouse.lot_stock_id
        period_last_date = self.aggregation_period + dateutil.relativedelta.relativedelta(months=-1)
        period_last_month = period_last_date.month
        customer_location = self.env['stock.location'].search(
            [('id', 'child_of', warehouse_location.id), ('usage', '=', 'customer'), ('x_inventory_type', '=', self.inventory_type)]).ids

        customer_location = f"({','.join(map(str, customer_location))})"
        start_period_measure = datetime.combine(period_last_date.replace(day=19), datetime.min.time())
        end_period_measure = datetime.combine(self.aggregation_period.replace(day=18), datetime.max.time())

        start_period_datetime = datetime.combine(self.aggregation_period.replace(day=1), datetime.min.time())
        end_period_datetime = datetime.combine(self.aggregation_period, datetime.max.time())

        # Current month measurement date
        current_month_measure_date = self.aggregation_period.replace(day=18)
        # Number of inventory days in a month
        numbers_day_inventory_in_month = current_month_measure_date - period_last_date.replace(day=18)

        if self.inventory_type == 'cylinder':
            if customer_location == '()':
                raise UserError(_("棚卸対象の組織にシリンダーの顧客ロケーションが適切に設定されていません。"))
            _select_data = f""" 
                SELECT 
                    '{self.organization_id.id}' organization_id, 
                    tiq.id location_id, 
                    tiq.install_quantity tank_capacity, 
                    '{current_month_measure_date}' meter_reading_date, 
                    cmu.cm_use month_amount_of_use,
                    (tiq.install_quantity - (Case When (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) is NULL then 0 ELSE (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) END)) meter_reading_inventory, -- 2-3-5
                    fam.fill_after_measure filling_after_meter_reading,
                    lmi.lm_inventory previous_last_inventory,
                    (tiq.install_quantity - (Case When (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) is NULL then 0 ELSE (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) END) + fam.fill_after_measure) this_month_inventory, -- 2-4-2
                    (lmi.lm_inventory + ftm.fill_this_month - cmu.cm_use) theoretical_inventory, -- 2-5-2
                    ((tiq.install_quantity - (Case When (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) is NULL then 0 ELSE (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) END) + fam.fill_after_measure)- 
                    (lmi.lm_inventory + ftm.fill_this_month - cmu.cm_use)) difference_qty -- 2-5-2
                FROM 
                -- 
                
                (SELECT id, x_total_installation_quantity install_quantity from stock_location where id IN {customer_location}) tiq  -- 2-3-1 Total set in location
                
                LEFT JOIN
                
                (SELECT sml.location_id, sum(sml.qty_done) cm_use from stock_move_line sml  -- 2-3-2 Current Month Use
                LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                LEFT JOIN sale_order so ON so.id = sp.sale_id
                WHERE sml.state = 'done'
                And sml.product_id = '{lpgas_product_id}'
                And sml.location_id IN {customer_location}
                and sml.date BETWEEN '{start_period_measure}' and '{end_period_measure}'
                GROUP BY sml.location_id) cmu ON tiq.id =  cmu.location_id
                
                LEFT JOIN
                
                (SELECT sml.location_dest_id location_id, ROUND(AVG(extract(day from AGE('{current_month_measure_date}', sml.date))::int)) num_day_measure FROM stock_move_line sml -- 2-3-4 Số ngày đo
                --LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                WHERE sml.date BETWEEN '{start_period_datetime}' and '{end_period_datetime}'
                AND sml.location_dest_id IN {customer_location}
                AND sml.product_id = '{lpgas_product_id}'
                AND sml.state = 'done' GROUP BY sml.location_dest_id) ndm ON ndm.location_id = tiq.id

                
                LEFT JOIN
                
                (SELECT sml.location_dest_id location_id, (Case When sum(sml.qty_done) is NULL then 0 ELSE sum(sml.qty_done) END) fill_after_measure FROM stock_move_line sml  --2-4-1 Lượng bơm thêm sau khi đo
                Left join stock_picking sp ON sp.id = sml.picking_id
                where sml.state = 'done'
                AND sml.date BETWEEN '{start_period_measure}' and '{end_period_datetime}'
                And sml.product_id = '{lpgas_product_id}'
                And sml.location_dest_id IN {customer_location}
                GROUP BY sml.location_dest_id
                ) fam ON fam.location_id = tiq.id
                
                LEFT JOIN
                
                (SELECT sml.location_dest_id location_id, (Case When sum(sml.qty_done) is NULL then 0 ELSE sum(sml.qty_done) END) fill_this_month FROM stock_move_line sml -- 2-5-1 Lượng bơm trong tháng
                Left join stock_picking sp ON sp.id = sml.picking_id
                where sml.state = 'done'
                AND sml.date BETWEEN '{start_period_datetime}' and '{end_period_datetime}'
                And sml.product_id = '{lpgas_product_id}'
                And sml.location_dest_id IN {customer_location}
                GROUP BY sml.location_dest_id) ftm ON ftm.location_id = tiq.id
                
                LEFT JOIN
                
                (SELECT lp.organization_id, sl.id location_id,(Case When lpl.this_month_inventory is NULL then 0 ELSE lpl.this_month_inventory END) lm_inventory from stock_location sl -- 2-2
                LEFT JOIN ss_erp_lpgas_order_line lpl ON lpl.location_id = sl.id
                LEFT JOIN ss_erp_lpgas_order lp ON lpl.lpgas_order_id = lp.id
                WHERE lp.month_aggregation_period = '{period_last_month}' AND
                sl.x_inventory_type = 'cylinder' AND
                lp.state = 'done' AND
                lp.organization_id = '{self.organization_id.id}' 
                AND sl.id IN {customer_location})lmi ON lmi.location_id = tiq.id				
                ;
            """
        else:
            if customer_location == '()':
                raise UserError(_("棚卸対象の組織にミニバルクの顧客ロケーションが適切に設定されていません。"))
            _select_data = f"""				
                    SELECT 
                            '{self.id}' lpgas_order_id, 
                            '{self.organization_id.id}' organization_id, 
                            tiq.id location_id, 
                            tiq.install_quantity tank_capacity, 
                            '{current_month_measure_date}' meter_reading_date, 
                            cmu.cm_use month_amount_of_use,
                            (CASE WHEN dd_tran.date_done is NUll THEN mri_not_tran.quantity ELSE (tiq.install_quantity - (cmu.cm_use/{numbers_day_inventory_in_month.days}*(extract(day from AGE(do_mea.date_order, dd_tran.date_done))::int))) END) meter_reading_inventory, -- 3-3-5
                            fam.fill_after_measure filling_after_meter_reading, -- 3-4-1
                            lmi.lm_inventory previous_last_inventory,
                            ((CASE WHEN dd_tran.date_done is NUll THEN mri_not_tran.quantity ELSE (tiq.install_quantity - (cmu.cm_use/{numbers_day_inventory_in_month.days}*(extract(day from AGE(do_mea.date_order, dd_tran.date_done))::int))) END) + fam.fill_after_measure) this_month_inventory, -- 3-4-2
                            (lmi.lm_inventory + ftm.fill_this_month - cmu.cm_use) theoretical_inventory, -- 3-5-2
                            (((CASE WHEN dd_tran.date_done is NUll THEN mri_not_tran.quantity ELSE (tiq.install_quantity - (cmu.cm_use/{numbers_day_inventory_in_month.days}*(extract(day from AGE(do_mea.date_order, dd_tran.date_done))::int))) END) + fam.fill_after_measure) - (lmi.lm_inventory + ftm.fill_this_month - cmu.cm_use)) difference_qty -- 2-5-2
                    FROM 
                    
                                
                    (SELECT id, x_total_installation_quantity install_quantity FROM stock_location WHERE id IN {customer_location}) tiq  -- 3-3-1 Total amount set in location
                    
                    LEFT JOIN
                    -- 
                    (SELECT sml.location_id, (Case When sum(sml.qty_done) is NULL then 0 ELSE sum(sml.qty_done) END) cm_use FROM stock_move_line sml  -- 3-3-2 Usage amount this month
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    WHERE sml.state = 'done'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_id IN {customer_location}
                    AND sml.date BETWEEN '{start_period_measure}' and '{end_period_measure}'
                    GROUP BY sml.location_id) cmu ON cmu.location_id = tiq.id 
                    
                    LEFT JOIN
                    -- 
                    (SELECT sml.location_id, so.date_order FROM stock_move_line sml  -- 3-3-4 a nearest date_order - measurement date
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    LEFT JOIN sale_order so ON so.id = sp.sale_id
                    WHERE sml.state = 'done'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_id IN {customer_location}
                    AND so.date_order BETWEEN '{start_period_datetime}' and '{end_period_datetime}'
                    ORDER BY so.date_order desc LIMIT 1
                    ) do_mea ON do_mea.location_id = tiq.id 
                    
                    LEFT JOIN
                    -- 
                    (SELECT sml.location_id, sp.date_done FROM stock_move_line sml  -- 3-3-4 b date_done transfer 
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    WHERE sml.state = 'done'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_id IN {customer_location}
                    LIMIT 1
                    ) dd_tran ON dd_tran.location_id = tiq.id and dd_tran.date_done <= do_mea.date_order
                    
                    LEFT JOIN
                    -- 
                    (SELECT location_id, quantity FROM stock_quant  -- 3-3-5 b case 3-3-4-b is NULL
                    WHERE product_id = '{lpgas_product_id}'
                    AND location_id IN {customer_location}
                    ) mri_not_tran ON mri_not_tran.location_id = tiq.id
                    
                    LEFT JOIN
                    
                    (
                    SELECT sl.id location_id,(Case When lpl.this_month_inventory is NULL then 0 ELSE lpl.this_month_inventory END) lm_inventory from stock_location sl -- 3-2 Tại kho tháng trước
                    LEFT JOIN ss_erp_lpgas_order_line lpl ON lpl.location_id = sl.id
                    LEFT JOIN ss_erp_lpgas_order lp ON lpl.lpgas_order_id = lp.id
                    WHERE lp.month_aggregation_period = '{period_last_month}' AND
                    sl.x_inventory_type = 'minibulk' AND
                    lp.state = 'done' AND
                    lp.organization_id = '{self.organization_id.id}' 
                    AND sl.id IN {customer_location}
                    )lmi ON lmi.location_id = cmu.location_id
                    
                    LEFT JOIN
                    
                    (SELECT sml.location_dest_id location_id, (Case When sum(sml.qty_done) is NULL then 0 ELSE sum(sml.qty_done) END) fill_after_measure FROM stock_move_line sml  --3-4-1 Extra filling amount after measuring
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    WHERE sml.state = 'done'
                    AND sml.date BETWEEN '{start_period_measure}' and '{end_period_datetime}'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_dest_id IN {customer_location}
                    GROUP BY sml.location_dest_id
                    ) fam ON fam.location_id = cmu.location_id
                    
                    LEFT JOIN
                    (
                    SELECT sml.location_dest_id location_id, (Case When sum(sml.qty_done) is NULL then 0 ELSE sum(sml.qty_done) END) fill_this_month FROM stock_move_line sml -- 3-5-1 fill amount in this month
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    WHERE sml.state = 'done'
                    AND sml.date BETWEEN '{start_period_datetime}' and '{end_period_datetime}'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_dest_id IN {customer_location}
                    GROUP BY sml.location_dest_id
                    ) ftm ON ftm.location_id = cmu.location_id
                    ;
                    """

        self._cr.execute(_select_data)
        data_lqgas_result = self._cr.dictfetchall()
        print('##############data_lqgas_result', data_lqgas_result)
        create_data = []
        for da in data_lqgas_result:
            create_data.append((0, 0, da))

        self.env["ss_erp.lpgas.order.line"].search([('lpgas_order_id', '=', self.id)]).sudo().unlink()
        self.lpgas_order_line_ids = create_data
        # self.state = 'confirm'
        return self.show_lpgas_report()

    #
    @api.constrains('aggregation_period', 'inventory_type', 'organization_id')
    def _check_constrain_period(self):
        # check is this period is exist
        if self.aggregation_period and self.inventory_type and self.organization_id:
            exist_lpgas_on_period = self.search([('month_aggregation_period', '=', self.aggregation_period.month), ('inventory_type', '=', self.inventory_type), ('organization_id', '=', self.organization_id.id)])
            if exist_lpgas_on_period and exist_lpgas_on_period != self:
                raise UserError(_("lpgas exists for this period, please recheck again"))

    def show_lpgas_report(self):
        return {
            'name': _('集計結果'),
            'type': 'ir.actions.act_window',
            'res_model': 'ss_erp.lpgas.order.line',
            'views': [[self.env.ref('ss_erp.ss_erp_lpgas_order_line_view_tree').id, 'tree']],
            'domain': [('lpgas_order_id', '=', self.id)],
            # 'target': 'new',
        }

    def approval_request(self):
        self.write({'state': 'waiting'})

    def verify_lpgas_slip(self):
        self.write({'state': 'done'})

    def cancel_lpgas_slip(self):
        self.write({'state': 'cancel'})

    #   when create and write make aggregation_period date default is end of this month
    @api.model
    def create(self, vals):
        if vals.get('aggregation_period'):
            day = calendar.monthrange(int(vals['aggregation_period'][0:3]), int(vals['aggregation_period'][5:7]))[1]
            vals['aggregation_period'] = vals['aggregation_period'][:-2] + str(day)
        vals['name'] = self.env['ir.sequence'].next_by_code('lpgas.order.name') or _('New')
        result = super(LPGasOrder, self).create(vals)
        return result

    #
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
    # _rec_name = 'name'

    # name = fields.Char(default='集計結果')
    lpgas_order_id = fields.Many2one('ss_erp.lpgas.order')
    state = fields.Selection(related='lpgas_order_id.state')
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

    def write(self, vals):
        self.lpgas_order_id.state = 'confirm'
        res = super(LPGasOrderLine, self).write(vals)
        return res