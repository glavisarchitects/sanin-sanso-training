# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import logging
import pytz

_logger = logging.getLogger(__name__)


class LPGasOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.lpgas.order'
    _description = 'LPガス棚卸伝票'
    _rec_name = 'name'

    name = fields.Char('LPガス棚卸参照')
    user_organization_ids = fields.Many2many('ss_erp.organization',
                                             default=lambda self: self.env.user.organization_ids.ids)
    organization_id = fields.Many2one('ss_erp.organization', string="組織名", domain="[('warehouse_id', '!=', False)]")
    inventory_type = fields.Selection([('cylinder', 'シリンダー'), ('minibulk', 'ミニバルク')], string='棚卸種別')
    accounting_date = fields.Date(string='会計日')
    aggregation_period = fields.Date(string='棚卸対象期間', copy=False)
    month_aggregation_period = fields.Integer(string='month of aggregation period', store=True, copy=False,
                                              compute='compute_month_aggregation_period')
    state = fields.Selection(
        [('draft', 'ドラフト'), ('confirm', '集計完了'), ('waiting', '承認待ち'), ('approval', '承認依頼中'),
         ('approved', '承認済み'),
         ('done', '検証済'), ('cancel', '取消済')], default='draft', string='ステータス')

    lpgas_order_line_ids = fields.One2many('ss_erp.lpgas.order.line', 'lpgas_order_id', ondelete="cascade",
                                           string='集計結果')

    def make_inventory_adjustment(self):
        lpgas_product_tmp_id = self.env['ir.config_parameter'].sudo().get_param('lpgus.order.propane_gas_id')
        if lpgas_product_tmp_id == '':
            raise UserError(_("プロダクトコードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。"))
        lpgas_product_id = self.env['product.product'].search([('product_tmpl_id', '=', int(lpgas_product_tmp_id))],
                                                              limit=1)
        branch_loss_location = self.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('id', 'child_of', self.organization_id.warehouse_id.view_location_id.id), ],
            limit=1)
        if not branch_loss_location:
            raise UserError(_("ロケーションロスを設定してください。"))
        for line in self.lpgas_order_line_ids:
            if line.difference_qty == 0:
                continue
            location_id = line.location_id.id if line.difference_qty < 0 else branch_loss_location.id
            location_dest_id = branch_loss_location.id if line.difference_qty < 0 else line.location_id.id

            sm_value = {
                'name': _('INV:LP GAS ') + (str(self.inventory_type) or ''),
                'x_organization_id': self.organization_id.id,
                'product_id': lpgas_product_id.id,
                'product_uom': lpgas_product_id.uom_id.id,
                'product_uom_qty': abs(line.difference_qty),
                'date': datetime.now(),
                'lpgas_adjustment': True,
                'company_id': self.env.user.company_id.id,
                'state': 'done',
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'move_line_ids': [(0, 0, {
                    'product_id': lpgas_product_id.id,
                    # 'lot_id': self.prod_lot_id.id,
                    'product_uom_qty': 0,  # bypass reservation here
                    'product_uom_id': lpgas_product_id.uom_id.id,
                    'qty_done': abs(line.difference_qty),
                    'state': 'done',
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                })]
            }

            self.env['stock.move'].create(sm_value)

    @api.depends('aggregation_period', 'lpgas_order_line_ids', 'state')
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
        lpgas_product_tmp_id = self.env['ir.config_parameter'].sudo().get_param('lpgus.order.propane_gas_id')
        if lpgas_product_tmp_id == '':
            raise UserError(_("プロダクトコードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。"))

        if int(lpgas_product_tmp_id) not in self.env['product.template'].search([]).ids:
            raise UserError(_("設定しているプロダクトIDは存在しません。"))

        lpgas_product_id = self.env['product.product'].search([('product_tmpl_id', '=', int(lpgas_product_tmp_id))],
                                                              limit=1).id

        branch_warehouse = self.organization_id.warehouse_id
        warehouse_location = branch_warehouse.lot_stock_id
        period_last_date = self.aggregation_period + relativedelta(months=-1)
        period_last_month = period_last_date.month
        # update condition new design 18/10/22
        # if self.inventory_type == 'cylinder':
        #     domain_location = [('id', 'child_of', warehouse_location.id),
        #                        ('x_inventory_type', '=', self.inventory_type)]
        # else:
        domain_location = [('id', 'child_of', warehouse_location.id), ('x_inventory_type', '=', self.inventory_type)]
        customer_location = self.env['stock.location'].search(domain_location).ids

        customer_location = f"({','.join(map(str, customer_location))})"
        start_period_measure = datetime.combine(period_last_date.replace(day=19), datetime.min.time())
        end_period_measure = datetime.combine(self.aggregation_period.replace(day=18), datetime.max.time())
        day_after_end_period_measure = datetime.combine(self.aggregation_period.replace(day=19), datetime.min.time())

        start_period_datetime = datetime.combine(self.aggregation_period.replace(day=1), datetime.min.time())
        end_period_datetime = datetime.combine(self.aggregation_period, datetime.max.time())

        # Current month measurement date
        current_month_measure_date = self.aggregation_period.replace(day=18)
        # Number of inventory days in a month
        numbers_day_inventory_in_month = current_month_measure_date - period_last_date.replace(day=18)

        # get the number of hours difference between local time and utc time
        tz = self.env.user.tz
        utcnow = pytz.timezone('utc').localize(datetime.utcnow())  # generic time
        local_user_time_now = utcnow.astimezone(pytz.timezone(tz)).replace(tzinfo=None)
        offset = relativedelta(local_user_time_now, datetime.utcnow())
        hours_diff = int(offset.hours)
        minutes_diff = int(offset.minutes)
        seconds_diff = int(offset.seconds)

        if self.inventory_type == 'cylinder':
            if customer_location == '()':
                raise UserError(_("棚卸対象の組織にシリンダーの顧客ロケーションが適切に設定されていません。"))
            _select_data = f""" 
                WITH tiq as (
                SELECT id, x_total_installation_quantity install_quantity from stock_location where id IN {customer_location}
                ),
                cmu as (
                    SELECT sml.location_id, sum(sml.qty_done) cm_use from stock_move_line sml  -- 2-3-2 Current Month Use
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    LEFT JOIN sale_order so ON so.id = sp.sale_id
                    WHERE sml.state = 'done'
                    And sml.product_id = '{lpgas_product_id}'
                    And sml.location_id IN {customer_location}
                    and (sml.date + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                                            interval '1 second' * '{seconds_diff}') BETWEEN '{start_period_measure}' and '{end_period_measure}'
                    GROUP BY sml.location_id
                ),
                ndm as (
                    SELECT DISTINCT ON (tb.location_id) location_id, tb.num_day_measure
                    FROM
                    (
                    SELECT sml.location_dest_id location_id, ('{current_month_measure_date}'::date - sml.date::date) num_day_measure FROM stock_move_line sml -- 2-3-4 Số ngày đo
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    WHERE sml.location_dest_id IN {customer_location}
                    AND sml.product_id = '{lpgas_product_id}'
                    AND (sml.date + interval '1 hour' * '8' + interval '1 minute' * '59' +
                                            interval '1 second' * '59') <=  '{current_month_measure_date}'
                    AND sml.state = 'done') tb order by tb.location_id, tb.num_day_measure asc
                ),
                fam as (
                SELECT sml.location_dest_id location_id, (Case When sum(sml.qty_done) is NULL then 0 ELSE sum(sml.qty_done) END) fill_after_measure FROM stock_move_line sml  --2-4-1 Lượng bơm thêm sau khi đo
                Left join stock_picking sp ON sp.id = sml.picking_id
                where sml.state = 'done'
                AND (sml.date + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                                        interval '1 second' * '{seconds_diff}') BETWEEN '{day_after_end_period_measure}' and '{end_period_datetime}'
                And sml.product_id = '{lpgas_product_id}'
                And sml.location_dest_id IN {customer_location}
                GROUP BY sml.location_dest_id
                ), 
                ftm as (
                SELECT sml.location_dest_id location_id, sum(sml.qty_done) fill_this_month FROM stock_move_line sml -- 2-5-1 this_month_filling
                Left join stock_picking sp ON sp.id = sml.picking_id
                where sml.state = 'done'
                AND (sml.date + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                    interval '1 second' * '{seconds_diff}') BETWEEN '{start_period_datetime}' and '{end_period_datetime}'
                And sml.product_id = '{lpgas_product_id}'
                And sml.location_dest_id IN {customer_location}
                GROUP BY sml.location_dest_id),
                lmi as 
                (SELECT lp.organization_id, sl.id location_id, lpl.this_month_inventory lm_inventory from stock_location sl -- 2-2
                LEFT JOIN ss_erp_lpgas_order_line lpl ON lpl.location_id = sl.id
                LEFT JOIN ss_erp_lpgas_order lp ON lpl.lpgas_order_id = lp.id
                WHERE lp.month_aggregation_period = '{period_last_month}' AND
                sl.x_inventory_type = 'cylinder' AND
                lp.state = 'done' AND
                lp.organization_id = '{self.organization_id.id}' 
                AND sl.id IN {customer_location})
                SELECT 
                    '{self.organization_id.id}' organization_id, 
                    tiq.id location_id, 
                    tiq.install_quantity tank_capacity, 
                    '{current_month_measure_date}' meter_reading_date, 
                    cmu.cm_use month_amount_of_use,
                    (tiq.install_quantity - (Case When (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) is NULL then 0 ELSE (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) END)) meter_reading_inventory, -- 2-3-5
                    fam.fill_after_measure filling_after_meter_reading,
                    lmi.lm_inventory previous_last_inventory,
                    ftm.fill_this_month this_month_filling,
                    (tiq.install_quantity - (Case When (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) is NULL then 0 ELSE (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) END) + (Case When fam.fill_after_measure is NULL then 0 ELSE fam.fill_after_measure END)) this_month_inventory, -- 2-4-2
                    ((Case When lmi.lm_inventory is NULL then 0 ELSE lmi.lm_inventory END) + (Case When ftm.fill_this_month is NULL then 0 ELSE ftm.fill_this_month END) - (Case When cmu.cm_use is NULL then 0 ELSE cmu.cm_use END)) theoretical_inventory, -- 2-5-2
                    (tiq.install_quantity - (Case When (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) is NULL then 0 ELSE (cmu.cm_use/('{numbers_day_inventory_in_month.days}')*ndm.num_day_measure) END) + (Case When fam.fill_after_measure is NULL then 0 ELSE fam.fill_after_measure END)- 
                    ((Case When lmi.lm_inventory is NULL then 0 ELSE lmi.lm_inventory END) + (Case When ftm.fill_this_month is NULL then 0 ELSE ftm.fill_this_month END) - (Case When cmu.cm_use is NULL then 0 ELSE cmu.cm_use END))) difference_qty -- 2-5-2
                FROM 
                -- 
                -- 2-3-1 Total set in location
                tiq   

                LEFT JOIN

                cmu ON tiq.id =  cmu.location_id

                LEFT JOIN

                ndm ON ndm.location_id = tiq.id

                LEFT JOIN

                fam ON fam.location_id = tiq.id

                LEFT JOIN

                ftm ON ftm.location_id = tiq.id

                LEFT JOIN

                lmi ON lmi.location_id = tiq.id				
                ;
            """
        else:
            if customer_location == '()':
                raise UserError(_("棚卸対象の組織にミニバルクの顧客ロケーションが適切に設定されていません。"))
            _select_data = f"""

                    WITH do_mea as (
                        SELECT 
                        DISTINCT ON (tb1.location_id) location_id, tb1.measure_date
                        FROM                    
                        (SELECT sml.location_id, (so.date_order + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                                            interval '1 second' * '{seconds_diff}') measure_date FROM stock_move_line sml  -- 3-3-1 get measure date from SO date order
                        LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                        LEFT JOIN sale_order so ON so.id = sp.sale_id
                        WHERE sml.state = 'done'
                        AND so.state = 'sale'
                        AND sp.state = 'done' --update condition 3-3-1
                        AND sml.product_id = '{lpgas_product_id}'
                        AND sml.location_id IN {customer_location}
                        AND (so.date_order + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                                            interval '1 second' * '{seconds_diff}') BETWEEN '{start_period_datetime}' and '{end_period_datetime}')
                        tb1 ORDER BY tb1.location_id, tb1.measure_date DESC 
                    ),
                    lmi AS (
                        SELECT sl.id location_id,lpl.this_month_inventory lm_inventory, lpl.meter_reading_date lm_meter_reading_date from stock_location sl -- 3-2 At the warehouse last month
                        LEFT JOIN ss_erp_lpgas_order_line lpl ON lpl.location_id = sl.id
                        LEFT JOIN ss_erp_lpgas_order lp ON lpl.lpgas_order_id = lp.id
                        WHERE lp.month_aggregation_period = '8' AND
                        sl.x_inventory_type = 'minibulk' AND
                        lp.inventory_type = 'minibulk' AND
                        lp.state = 'done' AND
                        lp.organization_id = '{self.organization_id.id}' 
                        AND sl.id IN {customer_location}
                    ),
                    cmu AS (
                    SELECT sml.location_id, sum(sml.qty_done) cm_use FROM stock_move_line sml  -- 3-3-3  Usage amount this month
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    LEFT JOIN do_mea ON sml.location_id = do_mea.location_id
                    LEFT JOIN lmi ON sml.location_id = lmi.location_id
                    WHERE sml.state = 'done'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_id IN {customer_location}
                    AND (sml.date + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                    interval '1 second' * '{seconds_diff}') BETWEEN lmi.lm_meter_reading_date AND do_mea.measure_date
                    GROUP BY sml.location_id),
                    dd_tran AS (
                    SELECT 
                    DISTINCT ON (tb2.location_id) location_id, tb2.date_done
                    FROM
                    (SELECT sml.location_dest_id location_id, (sp.date_done + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                    interval '1 second' * '{seconds_diff}') date_done FROM stock_move_line sml  -- 3-3-5 a date_done transfer 
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    LEFT JOIN do_mea ON sml.location_dest_id = do_mea.location_id
                    WHERE sml.state = 'done'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_dest_id IN {customer_location}
                    AND sp.date_done <= do_mea.measure_date
                    ) tb2 ORDER BY tb2.location_id, tb2.date_done DESC),
                    mri_not_tran AS (
                    SELECT location_id, quantity FROM stock_quant  -- 3-3-6 case 3-3-5-a is NULL
                    WHERE product_id = '{lpgas_product_id}'
                    AND location_id IN {customer_location}),
                    fam AS 
                    (
                    SELECT sml.location_dest_id location_id,sum(sml.qty_done) fill_after_measure FROM stock_move_line sml  --3-4-1 Extra filling amount after measuring
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    LEFT JOIN do_mea ON do_mea.location_id = sml.location_dest_id
                    WHERE sml.state = 'done'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_dest_id IN {customer_location}
                    AND (sml.date + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                    interval '1 second' * '{seconds_diff}') > do_mea.measure_date 
                    AND (sml.date + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                    interval '1 second' * '{seconds_diff}') < '{end_period_datetime}'
                    GROUP BY sml.location_dest_id),										
                    ftm AS (
                    SELECT sml.location_dest_id location_id, sum(sml.qty_done) fill_this_month FROM stock_move_line sml -- 3-5-1 fill amount in this month
                    LEFT JOIN stock_picking sp ON sp.id = sml.picking_id
                    WHERE sml.state = 'done'
                    AND (sml.date + interval '1 hour' * '{hours_diff}' + interval '1 minute' * '{minutes_diff}' +
                                        interval '1 second' * '{seconds_diff}') BETWEEN '{start_period_datetime}' and '{end_period_datetime}'
                    AND sml.product_id = '{lpgas_product_id}'
                    AND sml.location_dest_id IN {customer_location}
                    GROUP BY sml.location_dest_id)
                    SELECT 
                            '{self.id}' lpgas_order_id, 
                            '{self.organization_id.id}' organization_id, 
                            tiq.id location_id, 
                            tiq.install_quantity tank_capacity, 
                            do_mea.measure_date meter_reading_date, 
                            cmu.cm_use month_amount_of_use, -- 3-3-3

                            (CASE WHEN dd_tran.date_done is NUll THEN mri_not_tran.quantity ELSE (tiq.install_quantity - 
                            (cmu.cm_use/(do_mea.measure_date::date - lmi.lm_meter_reading_date::date)*
                            (do_mea.measure_date::date - dd_tran.date_done::date))) END) meter_reading_inventory, -- 3-3-6

                            fam.fill_after_measure filling_after_meter_reading, -- 3-4-1
                            lmi.lm_inventory previous_last_inventory,
                            ftm.fill_this_month this_month_filling,

                            ((CASE WHEN dd_tran.date_done is NUll THEN mri_not_tran.quantity ELSE (tiq.install_quantity - 
                            (cmu.cm_use/(do_mea.measure_date::date - lmi.lm_meter_reading_date::date)*
                            (do_mea.measure_date::date - dd_tran.date_done::date))) END) + 
                            (Case When fam.fill_after_measure is NULL then 0 ELSE fam.fill_after_measure END)) this_month_inventory, -- 3-4-2 = 3-3-6 + 3-4-1

                            ((Case When lmi.lm_inventory is NULL then 0 ELSE lmi.lm_inventory END) + 
                            (Case When ftm.fill_this_month is NULL then 0 ELSE ftm.fill_this_month END) - 
                            (Case When cmu.cm_use is NULL then 0 ELSE cmu.cm_use END)) theoretical_inventory, -- 3-5-2 = 3-2 + 3-5-1 + 3-3-3 

                            (((CASE WHEN dd_tran.date_done is NUll THEN mri_not_tran.quantity ELSE (tiq.install_quantity - 
                            (cmu.cm_use/(do_mea.measure_date::date - lmi.lm_meter_reading_date::date)*
                            (do_mea.measure_date::date - dd_tran.date_done::date))) END) + 
                            (Case When fam.fill_after_measure is NULL then 0 ELSE fam.fill_after_measure END)) -
                            ((Case When lmi.lm_inventory is NULL then 0 ELSE lmi.lm_inventory END) + 
                            (Case When ftm.fill_this_month is NULL then 0 ELSE ftm.fill_this_month END) - 
                            (Case When cmu.cm_use is NULL then 0 ELSE cmu.cm_use END)) ) difference_qty -- 3-6-1 = 3-4-2 - 3-5-2
                    FROM                     

                    (SELECT id, x_total_installation_quantity install_quantity FROM 
                    stock_location WHERE id IN {customer_location}) tiq  -- 3-3-2 Total amount set in location 

                    LEFT JOIN
                    -- 
                    do_mea ON do_mea.location_id = tiq.id 

                    LEFT JOIN
                    --
                    lmi ON lmi.location_id = tiq.id

                    LEFT JOIN

                    -- 
                    cmu ON cmu.location_id = tiq.id

                    LEFT JOIN
                    -- 
                    dd_tran ON dd_tran.location_id = tiq.id

                    LEFT JOIN
                    -- 
                    mri_not_tran ON mri_not_tran.location_id = tiq.id

                    LEFT JOIN
                    --
                    fam ON fam.location_id = tiq.id

                    LEFT JOIN
                    ftm ON ftm.location_id = tiq.id
                    ;

                    """

        self._cr.execute(_select_data)
        data_lqgas_result = self._cr.dictfetchall()
        create_data = []
        for da in data_lqgas_result:
            create_data.append((0, 0, da))

        # self.env["ss_erp.lpgas.order.line"].search([('lpgas_order_id', '=', self.id)]).sudo().unlink()
        self.lpgas_order_line_ids = False
        self.lpgas_order_line_ids = create_data
        # self.state = 'confirm'
        return self.show_lpgas_report()

    #
    @api.constrains('aggregation_period', 'inventory_type', 'organization_id')
    def _check_constrain_period(self):
        # check is this period is exist
        if self.aggregation_period and self.inventory_type and self.organization_id:
            exist_lpgas_on_period = self.search([('month_aggregation_period', '=', self.aggregation_period.month),
                                                 ('inventory_type', '=', self.inventory_type),
                                                 ('organization_id', '=', self.organization_id.id)])
            if exist_lpgas_on_period and exist_lpgas_on_period != self:
                raise UserError(_("指定した棚卸期間のLPガス棚卸しは既に行われています。"))

    def show_lpgas_report(self):
        return {
            'name': _('集計結果'),
            'type': 'ir.actions.act_window',
            'res_model': 'ss_erp.lpgas.order.line',
            'views': [[self.env.ref('ss_erp_stock.ss_erp_lpgas_order_line_view_tree').id, 'tree']],
            'domain': [('lpgas_order_id', '=', self.id)],
            # 'target': 'new',
        }

    def approval_request(self):
        if self.state == 'confirm':
            self.write({'state': 'waiting'})

    def verify_lpgas_slip(self):
        if self.state == 'approved':
            self.make_inventory_adjustment()
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
            if r.accounting_date and r.aggregation_period:
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
    difference_qty = fields.Float(string='棚卸差異', compute='_compute_difference_qty')

    def write(self, vals):
        self.lpgas_order_id.state = 'confirm'
        res = super(LPGasOrderLine, self).write(vals)
        return res

    @api.depends('theoretical_inventory', 'this_month_inventory')
    def _compute_difference_qty(self):
        for line in self:
            line.difference_qty = line.this_month_inventory - line.theoretical_inventory
