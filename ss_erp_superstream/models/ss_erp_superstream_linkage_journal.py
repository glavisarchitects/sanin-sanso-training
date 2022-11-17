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
                                         ], string="仕訳作成")
    slip_date_edit = fields.Selection([('first_day', '月初日'),
                                       ('last_day', '月末日')
                                       ], string="伝票日付編集")
    product_ctg = fields.Selection([('merchandise', '商品'),
                                    ('product', '製品'),
                                    ('stock', '製品'),
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

    # field use for technical function (query)
    # categ_product_id_char = fields.Char(compute='_compute_categ_product_id_char', store=True, copy=False)
    # sanhot_product_id_char = fields.Char(compute='_compute_sanhot_product_id_char', store=True, copy=False)
    categ_product_id_char = fields.Char(store=True, copy=False)
    sanhot_product_id_char = fields.Char(store=True, copy=False)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        all_categ = self.env['product.category'].sudo().search([]).ids
        string_all_categ = ','.join([str(x) for x in all_categ])
        if vals.get('materials_grouping'):
            product_ctg_merchandise = self.env['ir.config_parameter'].sudo().get_param(
                'A007_product_ctg_merchandise')
            if not product_ctg_merchandise:
                res.categ_product_id_char = ''
                raise UserError(
                    'プロダクトカテゴリ（原材料）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_material)')
            res.categ_product_id_char = product_ctg_merchandise
        else:
            res.categ_product_id_char = string_all_categ

        all_product = self.env['product.template'].sudo().search([]).ids
        string_all_product = ','.join([str(x) for x in all_product])
        if vals.get('sanhot_point'):
            product_sanhot = self.env['ir.config_parameter'].sudo().get_param('A007_sanhot_point_product_id')
            if not product_sanhot:
                res.sanhot_product_id_char = ''
                raise UserError(
                    'さんほっとポイントのプロダクトID取得に失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_sanhot_point_product_id)')
            res.sanhot_product_id_char = product_sanhot
        else:
            res.sanhot_product_id_char = string_all_product
        return res

    def write(self, vals):
        res = super().write(vals)
        all_categ = self.env['product.category'].sudo().search([]).ids
        string_all_categ = ','.join([str(x) for x in all_categ])
        if vals.get('materials_grouping'):
            if self.materials_grouping:
                product_ctg_merchandise = self.env['ir.config_parameter'].sudo().get_param(
                    'A007_product_ctg_merchandise')
                if not product_ctg_merchandise:
                    self.categ_product_id_char = ''
                    raise UserError(
                        'プロダクトカテゴリ（原材料）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。（A007_product_ctg_material）')
                self.categ_product_id_char = product_ctg_merchandise
            else:
                self.categ_product_id_char = string_all_categ

        all_product = self.env['product.template'].sudo().search([]).ids
        string_all_product = ','.join([str(x) for x in all_product])
        if vals.get('sanhot_point'):
            if self.sanhot_point:
                product_sanhot = self.env['ir.config_parameter'].sudo().get_param('A007_sanhot_point_product_id')
                if not product_sanhot:
                    self.sanhot_product_id_char = ''
                    raise UserError(
                        'さんほっとポイントのプロダクトID取得に失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_sanhot_point_product_id)')
                self.sanhot_product_id_char = product_sanhot
            else:
                self.sanhot_product_id_char = string_all_product
        return res

    # @api.depends('materials_grouping')
    # def _compute_categ_product_id_char(self, categ_product_id=False):
    #     all_categ = self.env['product.category'].search([]).ids
    #     string_all_categ = ','.join([str(x) for x in all_categ])
    #     for rec in self:
    #         if rec.materials_grouping:
    #             product_ctg_merchandise = categ_product_id or rec.env['ir.config_parameter'].sudo().get_param(
    #                 'A007_product_ctg_merchandise')
    #             if not product_ctg_merchandise:
    #                 rec.categ_product_id_char = ''
    #                 raise UserError(
    #                     'プロダクトカテゴリ（商品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_merchandise)')
    #             rec.categ_product_id_char = product_ctg_merchandise
    #         else:
    #             rec.categ_product_id_char = string_all_categ
    #
    # @api.depends('sanhot_point')
    # def _compute_sanhot_product_id_char(self, sanhot_point_product_id=False):
    #     all_product = self.env['product.template'].search([]).ids
    #     string_all_product = ','.join([str(x) for x in all_product])
    #     for rec in self:
    #         if rec.sanhot_point:
    #             product_sanhot = sanhot_point_product_id or rec.env['ir.config_parameter'].sudo().get_param('A007_sanhot_point_product_id')
    #             if not product_sanhot:
    #                 rec.sanhot_product_id_char = ''
    #                 raise UserError(
    #                     'プロダクトカテゴリ（商品）の取得失敗しました。システムパラメータに次のキーが設定されているか確認してください。(A007_product_ctg_merchandise)')
    #             rec.sanhot_product_id_char = product_sanhot
    #         else:
    #             rec.sanhot_product_id_char = string_all_product
