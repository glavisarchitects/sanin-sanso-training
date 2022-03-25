# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class ConvertCodeType(models.Model):
    _name = 'ss_erp.convert.code.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '変換コード種別'

    name = fields.Char(
        string='変換コード種別名', index=True, required=True, copy=False)
    code = fields.Char(string='コード', index=True, required=True, copy=False)
    model = fields.Many2one(
        'ir.model', string='モデル', required=True, ondelete="cascade", copy=False)
    fields = fields.Many2one(
        'ir.model.fields', string='項目', required=True,
        ondelete='cascade', domain="[('model_id', '=', model)]", copy=False)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        res = super(ConvertCodeType, self).copy(default)
        return res

    @api.onchange('model')
    def onchange_model(self):
        if self.model:
            if self.fields and self.fields.model_id != self.model:
                self.fields = False

    @api.constrains('name', 'code', 'model', 'fields')
    def _check_duplicate(self):
        for rec in self:
            convert_code_types = self.env['ss_erp.convert.code.type'].search([('name', '=', rec.name),
                                                                              ('code', '=', rec.code),
                                                                              ('model', '=', rec.model.id),
                                                                              ('fields', '=', rec.fields.id)])
            if len(convert_code_types) > 1:
                raise UserError(_('入力された変換コード種別定義は既に登録済みです。'))
