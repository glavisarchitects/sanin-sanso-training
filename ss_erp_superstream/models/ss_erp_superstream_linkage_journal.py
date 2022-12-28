# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SSSuperStreamLinkageJournal(models.Model):
    _name = 'ss_erp.superstream.linkage.journal'
    _description = 'SuperStream連携仕訳'
    _rec_name = 'journal'

    name = fields.Char(string="名")
    # journal_id = fields.Many2one('account.journal', string="仕訳名")
    journal = fields.Char(string="仕訳名")
    journal_creation = fields.Selection([('odoo_journal', 'Odoo仕訳'),
                                         ('move_within_base', '拠点内移動'),
                                         ('transfer_between_base', '拠点間移動'),
                                         ('sanhot_point', 'さんほっとポイント'),
                                         ], string="仕訳作成")
    slip_date_edit = fields.Selection([('first_day', '月初日'),
                                       ('last_day', '月末日')
                                       ], string="伝票日付編集")
    product_ctg = fields.Selection([('merchandise', '商品'),
                                    ('product', '製品'),
                                    ('stock', '貯蔵品'),
                                    ], string="プロダクトカテゴリ")
    materials_grouping = fields.Boolean(string="原材料グルーピング", default=False)
    sanhot_point = fields.Boolean(string="さんほっとポイント", default=False)
    debit_account = fields.Many2one('account.account', string="借方勘定科目")
    debit_related_organization = fields.Many2one('ss_erp.organization', string="借方関連組織")
    debit_related_org_except = fields.Boolean(string='借方関連組織除外')
    debit_sub_account = fields.Many2one('ss_erp.account.subaccount', string="借方補助科目")
    debit_accounting_department_code = fields.Char(string="借方経理部門コード")
    debit_department_edit_classification = fields.Selection([('no_edits', '編集なし'),
                                                             ('first_two_digits', '前2桁上書き'),
                                                             ('all', 'すべて上書き')
                                                             ], string="借方部門編集区分")
    debit_application_edit_indicator = fields.Selection([('month', '月'),
                                                         ('month_and_branch', '月/支店'),
                                                         ('org_from_to_month', '移動元組織/移動先組織と月'),
                                                         ('month_and_materials', '移動元部門と移動先部門と月')
                                                         ], string="借方適用編集区分")
    debit_tax_calculation = fields.Boolean(string="借方税計算")
    debit_account_employee_category = fields.Selection([('no_used', '未使用'),
                                                        ('customer', '得意先'),
                                                        ('vendor', '仕入先'),
                                                        ('employee', '社員')
                                                        ], string="借方取引先・社員区分")
    debit_application = fields.Char(string="借方適用")
    credit_account = fields.Many2one('account.account', string="貸方勘定科目")
    credit_sub_account = fields.Many2one('ss_erp.account.subaccount', string="貸方補助科目")
    credit_related_organization = fields.Many2one('ss_erp.organization', string="貸方関連組織")
    credit_related_org_except = fields.Boolean(string="貸方関連組織除外")
    credit_accounting_department_code = fields.Char(string="貸方経理部門コード")
    credit_department_editing_classification = fields.Selection([('no_edits', '編集なし'),
                                                                 ('first_two_digits', '前2桁上書き'),
                                                                 ('all', 'すべて上書き')
                                                                 ], string="貸方部門編集区分")
    credit_application_edit_indicator = fields.Selection([('month', '月'),
                                                          ('month_and_branch', '月/支店'),
                                                          ('org_from_to_month', '移動元組織/移動先組織と月'),
                                                          ('month_and_materials', '移動元部門と移動先部門と月')
                                                          ], string="貸方適用編集区分")
    credit_tax_calculation = fields.Boolean("貸方税計算")
    credit_account_employee_category = fields.Selection([('no_used', '未使用'),
                                                         ('customer', '得意先'),
                                                         ('vendor', '仕入先'),
                                                         ('employee', '社員')
                                                         ], string="貸方取引先・社員区分")
    credit_application = fields.Char(string="貸方適用")
    categ_product_id_char = fields.Char(store=True, copy=False)
    sanhot_product_id_char = fields.Char(store=True, copy=False)

    debit_related_org_id_char = fields.Char(store=True, copy=False, compute='compute_debit_related_org_id_char')
    credit_related_org_id_char = fields.Char(store=True, copy=False, compute='compute_credit_related_org_id_char')

    @api.depends('debit_related_organization', 'debit_related_org_except')
    def compute_debit_related_org_id_char(self):
        for rec in self:
            if rec.debit_related_org_except:
                all_organization_except_current = self.env['ss_erp.organization'].search([('id', '!=', rec.debit_related_organization.id)]).ids
                str_all_organization_except_current = ','.join([str(x) for x in all_organization_except_current])
                rec.debit_related_org_id_char = str_all_organization_except_current
            else:
                rec.debit_related_org_id_char = str(rec.debit_related_organization.id)

    @api.depends('credit_related_organization', 'credit_related_org_except')
    def compute_credit_related_org_id_char(self):
        for rec in self:
            if rec.credit_related_org_except:
                all_organization_except_current = self.env['ss_erp.organization'].search([('id', '!=', rec.credit_related_organization.id)]).ids
                str_all_organization_except_current = ','.join([str(x) for x in all_organization_except_current])
                rec.credit_related_org_id_char = str_all_organization_except_current
            else:
                rec.credit_related_org_id_char = str(rec.credit_related_organization.id)

    def _recalculate_product_category_char(self, is_materials_grouping=None):
        if is_materials_grouping:
            product_ctg_merchandise = self.env['ir.config_parameter'].sudo().get_param(
                'A007_product_ctg_merchandise')
            if not product_ctg_merchandise:
                raise UserError(
                    'プロダクトカテゴリ（原材料）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_material)')
            return product_ctg_merchandise
        else:
            all_categ = self.env['product.category'].sudo().search([]).ids
            string_all_categ = ','.join([str(x) for x in all_categ])
            return string_all_categ

    def _recalculate_sanhot_product_id_char(self, is_sanhot_point=None):
        if is_sanhot_point:
            product_sanhot = self.env['ir.config_parameter'].sudo().get_param('A007_sanhot_point_product_id')
            if not product_sanhot:
                raise UserError(
                    'さんほっとポイントのプロダクトID取得に失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_sanhot_point_product_id)')
            return product_sanhot
        else:
            all_product = self.env['product.template'].sudo().search([]).ids
            string_all_product = ','.join([str(x) for x in all_product])
            return string_all_product

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.categ_product_id_char = res.sudo()._recalculate_product_category_char(
            is_materials_grouping=res.materials_grouping)

        res.sanhot_product_id_char = res.sudo()._recalculate_sanhot_product_id_char(
            is_sanhot_point=res.sanhot_point)
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('materials_grouping'):
            self.categ_product_id_char = self.sudo()._recalculate_product_category_char(
                is_materials_groupingvals=vals.get('materials_grouping'))

        if vals.get('sanhot_point'):
            self.sanhot_product_id_char = self.sudo()._recalculate_sanhot_product_id_char(
                is_sanhot_point=vals.get('sanhot_point'))
        return res


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def _recalculate_product_category_char(self):
        linkage_ids = self.env['ss_erp.superstream.linkage.journal'].sudo().search([])
        for linkage in linkage_ids:
            linkage.categ_product_id_char = linkage.sudo()._recalculate_product_category_char(
                is_materials_grouping=linkage.materials_grouping)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _recalculate_sanhot_product_id_char(self):
        linkage_ids = self.env['ss_erp.superstream.linkage.journal'].sudo().search([])
        for linkage in linkage_ids:
            linkage.sanhot_product_id_char = linkage.sudo()._recalculate_sanhot_product_id_char(
                is_sanhot_point=linkage.sanhot_point)
