# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.osv import expression


class InstructionOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'ss_erp.instruction.order'
    _description = '指示伝票'

    name = fields.Char(default='新規', string='棚卸参照', )
    sequence = fields.Integer(string='シーケンス')
    accounting_date = fields.Datetime("会計日", default=lambda self: fields.Datetime.now())
    company_id = fields.Many2one('res.company', string='会社', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    date = fields.Datetime(string='在庫調整日')
    exhausted = fields.Boolean(string='在庫のないプロダクトを含める')
    prefill_counted_quantity = fields.Selection([
        ('counted', '手持在庫をデフォルト提案'),
        ('zero', 'ゼロをデフォルト提案'),
    ], string='棚卸数量')
    start_empty = fields.Boolean(string='空の在庫')
    state = fields.Selection([
        ('draft', 'ドラフト'),
        ('cancel', '取消済'),
        ('confirm', '進行中'),
        ('waiting', '承認待ち'),
        ('approval', '承認依頼中'),
        ('approved', '承認済み'),
        ('done', '検証済'),
    ], string='ステータス', default='draft')
    line_ids = fields.One2many('ss_erp.instruction.order.line', 'order_id', ondelete='cascade')
    location_ids = fields.Many2many(
        'stock.location', string='ロケーション',
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)]},
        domain="[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]")
    product_ids = fields.Many2many(
        'product.product', string='プロダクト', check_company=True,
        domain="[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        readonly=True,
        states={'draft': [('readonly', False)]}, )
    organization_id = fields.Many2one('ss_erp.organization', string='組織名')
    responsible_dept_id = fields.Many2one('ss_erp.responsible.department', string='管轄部門')
    responsible_user_id = fields.Many2one('res.users', string='担当者')
    # type_id = fields.Many2one('product.template', string='棚卸種別')
    stock_inventory_id = fields.One2many('stock.inventory', 'instruction_order_id', string='棚卸伝票番号', ondelete='cascade')

    stock_inventory_id_count = fields.Integer(compute='_compute_count_stock_inventory_id')

    def _compute_count_stock_inventory_id(self):
        for rec in self:
            rec.stock_inventory_id_count = len(self.env['stock.inventory'].search([('instruction_order_id', '=', rec.id)]))

    def action_view_inventory_adjustment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_inventory_form")
        action['domain'] = [('instruction_order_id', '=', self.id)]
        return action

    @api.constrains("organization_id")
    def _check_default_warehouse(self):
        for record in self:
            if not record.organization_id.warehouse_id:
                raise ValidationError(_("対象の支店にデフォルト倉庫が設定されていません。組織マスタの設定を確認してください。"))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'ss_erp.instruction.order.name') or _('New')
        result = super(InstructionOrder, self).create(vals)
        return result

    @api.constrains('accounting_date')
    def _check_accounting_date(self):
        for record in self:
            if not record.accounting_date:
                raise ValidationError(_(
                    "会計日を選択してください。"))
            if record.accounting_date.date() < fields.Date.today():
                raise ValidationError(
                    _(
                        "会計日は現在より過去の日付は設定できません。"))
            elif record.accounting_date and record.date and \
                    record.accounting_date.date() < record.date.date():
                raise ValidationError(
                    _("会計日は棚卸予定日以降の日付を選択してください。")
                )

    @api.constrains('organization_id')
    def _check_organization_id(self):
        for record in self:
            if not record.organization_id:
                raise ValidationError(
                    _("組織名を選択してください。")
                )

    @api.constrains('date')
    def _check_date(self):
        for record in self:
            if not record.date:
                raise ValidationError(
                    _("棚卸予定日を選択してください。"))

    def display_action(self):
        self.ensure_one()
        if not self.stock_inventory_id:
            self._action_start()
        self._check_company()
        return self.display_view()

    def search_action(self):
        self.ensure_one()
        if not self.stock_inventory_id:
            self._action_start()
        self._check_company()
        return self.search_view()

    def display_view(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('棚卸計画詳細'),
            'res_model': 'ss_erp.instruction.order.line',
        }
        context = {
            'default_is_editable': True,
            'default_order_id': self.id,
        }
        # Define domains and context
        domain = [
            ('order_id', '=', self.id),
        ]
        view_id = self.env.ref('ss_erp_stock.ss_erp_instruction_order_line_tree').id
        stock_inventory_id_list = list(set(self.stock_inventory_id.mapped('state')))
        if self.stock_inventory_id and 'draft' not in stock_inventory_id_list:
            view_id = self.env.ref('ss_erp_stock.ss_erp_instruction_order_line_tree_non_edit').id
        action['view_id'] = view_id
        action['context'] = context
        action['domain'] = domain
        return action

    def search_view(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('棚卸計画詳細'),
            'res_model': 'ss_erp.instruction.order.line',
        }
        context = {
            'default_is_editable': True,
            'default_order_id': self.id,
        }
        # Define domains and context
        domain = [
            ('order_id', '=', self.id),
            ('organization_id', '=', self.organization_id.id)
        ]
        view_id = self.env.ref('ss_erp_stock.ss_erp_instruction_order_line_tree').id
        stock_inventory_id_list = list(set(self.stock_inventory_id.mapped('state')))
        if self.stock_inventory_id and 'draft' not in stock_inventory_id_list:
            view_id = self.env.ref('ss_erp_stock.ss_erp_instruction_order_line_tree_non_edit').id
        action['view_id'] = view_id
        action['context'] = context
        action['domain'] = domain
        return action

    def action_cancel_draft(self):
        for record in self:
            if record.stock_inventory_id:
                record.stock_inventory_id.write({
                    'state': 'cancel'
                })
        self.write({
            'state': 'cancel'
        })

    def action_draft(self):
        instruction_orders = self.filtered(lambda s: s.state in ['cancel'])
        instruction_orders.update({
            'state': 'draft',
        })

    def action_check(self):
        lines = self.line_ids.filtered(lambda x:x.difference_qty!=0)
        for line in lines:
            line._generate_moves()
            # line._generate_moves_account_move()

    def post_inventory(self):
        self.env['stock.move'].search([('instruction_order_id','=',self.id)]).filtered(lambda move: move.state != 'done')._action_done()
        return True

    def _action_start(self):
        for order in self:
            if not order.line_ids and not order.start_empty:
                x = order._get_inventory_lines_values()
                self.env['ss_erp.instruction.order.line'].create(order._get_inventory_lines_values())

    def _get_quantities(self):
        self.ensure_one()
        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids)]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]

        if self.organization_id.warehouse_id and self.organization_id.warehouse_id.view_location_id:
            domain_loc.append(('id', 'child_of', self.organization_id.warehouse_id.view_location_id.id))

        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

        # 2022/06/30 LPガスのプロダクトを棚卸集計しないように
        propane_gas_id = self.env['ir.config_parameter'].sudo().get_param('lpgus.order.propane_gas_id')
        if not propane_gas_id:
            raise UserError(
                _('プロダクトコードの取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（lpgus.order.propane_gas_id）'))

        if not self.env['product.template'].browse(int(propane_gas_id)):
            raise UserError(
                _('設定しているプロダクトIDは存在しません。'))

        domain = [('company_id', '=', self.company_id.id),
                  ('quantity', '!=', '0'),
                  ('location_id', 'in', locations_ids),
                  ('product_id', '!=', int(propane_gas_id))]

        if self.prefill_counted_quantity == 'zero':
            domain.append(('product_id.active', '=', True))

        if self.product_ids:
            domain = expression.AND([domain, [('product_id', 'in', self.product_ids.ids)]])

        fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'quantity:sum']
        group_by = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id']

        quants = self.env['stock.quant'].read_group(domain, fields, group_by, lazy=False)
        return {(
                    quant['product_id'] and quant['product_id'][0] or False,
                    quant['location_id'] and quant['location_id'][0] or False,
                    quant['lot_id'] and quant['lot_id'][0] or False,
                    quant['package_id'] and quant['package_id'][0] or False,
                    quant['owner_id'] and quant['owner_id'][0] or False):
                    quant['quantity'] for quant in quants
                }

    def _get_exhausted_inventory_lines_vals(self, non_exhausted_set):
        self.ensure_one()
        if self.product_ids:
            product_ids = self.product_ids.ids
        else:
            product_ids = self.env['product.product'].search_read([
                '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
                ('type', '=', 'product'),
                ('active', '=', True)], ['id'])
            product_ids = [p['id'] for p in product_ids]

        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids)]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]

        if self.organization_id.warehouse_id and self.organization_id.warehouse_id.view_location_id:
            domain_loc.append(('id', 'child_of', self.organization_id.warehouse_id.view_location_id.id))

        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

        vals = []
        for product_id in product_ids:
            for location_id in locations_ids:
                if ((product_id, location_id) not in non_exhausted_set):
                    vals.append({
                        # not clear the logic of this field? just wrong code???
                        # 'inventory_id': self.id,
                        'order_id': self.id,
                        'product_id': product_id,
                        'location_id': location_id,
                        'theoretical_qty': 0
                    })
        return vals

    def _get_inventory_lines_values(self):
        self.ensure_one()
        quants_groups = self._get_quantities()
        vals = []
        for (product_id, location_id, lot_id, package_id, owner_id), quantity in quants_groups.items():
            line_values = {'order_id': self.id,
                           'product_qty': 0 if self.prefill_counted_quantity == "zero" else quantity,
                           'theoretical_qty': quantity, 'prod_lot_id': lot_id, 'partner_id': owner_id,
                           'product_id': product_id, 'location_id': location_id, 'package_id': package_id,
                           'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id}
            vals.append(line_values)
        if self.exhausted:
            vals += self._get_exhausted_inventory_lines_vals({(l['product_id'], l['location_id']) for l in vals})
        return vals

    def action_create_inventory(self, ids, domain_record=[]):
        if domain_record:
            ids = self.env['ss_erp.instruction.order.line'].search(domain_record).ids
        lines = self.env['ss_erp.instruction.order.line'].browse(ids)
        if not self.stock_inventory_id:
            locations = lines.mapped('location_id')
            for location in locations:
                location_data = lines.filtered(lambda x: x.location_id.id == location.id)
                inventory_data = {
                    'name': self.env['ir.sequence'].next_by_code('stock.inventory.name'),
                    'company_id': self.company_id.id,
                    'location_ids': [(4, location.id)],
                    'organization_id': self.organization_id.id,
                    'responsible_dept_id': self.responsible_dept_id.id,
                    'responsible_user_id': self.responsible_user_id.id,
                    'accounting_date': self.accounting_date,
                    'prefill_counted_quantity': self.prefill_counted_quantity,
                    'instruction_order_id': self.id
                }
                line_ids = []
                for line in location_data:
                    line_data = {
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'location_id': line.location_id.id,
                        'prod_lot_id': line.prod_lot_id.id,
                        'inventory_order_line_id': line.id,
                        'product_qty': line.product_qty,
                    }
                    line_ids.append((0, 0, line_data))
                inventory_data['line_ids'] = line_ids
                self.env['stock.inventory'].create(inventory_data)
        else:
            exist_inventory_order_line_ids =list(set(self.env['stock.inventory.line'].search([('inventory_order_line_id', 'in', lines.ids)]).mapped('inventory_order_line_id')))
            new_lines = lines.filtered(lambda x:x.id not in exist_inventory_order_line_ids)
            locations = new_lines.mapped('location_id')
            for location in locations:
                location_data = new_lines.filtered(lambda x: x.location_id.id == location.id)
                inventory_data = {
                    'name': self.env['ir.sequence'].next_by_code('stock.inventory.name'),
                    'company_id': self.company_id.id,
                    'location_ids': [(4, location.id)],
                    'organization_id': self.organization_id.id,
                    'responsible_dept_id': self.responsible_dept_id.id,
                    'responsible_user_id': self.responsible_user_id.id,
                    'accounting_date': self.accounting_date,
                    'prefill_counted_quantity': self.prefill_counted_quantity,
                    'instruction_order_id': self.id
                }
                line_ids = []
                for line in location_data:
                    line_data = {
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'location_id': line.location_id.id,
                        'prod_lot_id': line.prod_lot_id.id,
                        'inventory_order_line_id': line.id,
                        'product_qty': line.product_qty,
                    }
                    line_ids.append((0, 0, line_data))
                inventory_data['line_ids'] = line_ids
                self.env['stock.inventory'].create(inventory_data)


    def action_inspection(self):
        self.action_check()
        self.post_inventory()
        self.write({'state': 'done'})
        self.stock_inventory_id.write({'state': 'validated'})
        # self.post_inventory()
