from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    x_organization_id = fields.Many2one(
        'ss_erp.organization', string='担当組織', default=lambda self: self._get_default_x_organization_id())
    x_responsible_dept_id = fields.Many2one(
        'ss_erp.responsible.department', string='管轄部門', default=lambda self: self._get_default_x_responsible_dept_id())
    user_id = fields.Many2one('res.users', string='担当者', default=lambda self: self.env.user)
    x_require_responsible_dept = fields.Boolean(default=True)

    x_warehouse_location_id = fields.Many2one('stock.location',
                                              related='x_organization_id.warehouse_id.view_location_id', store=True)

    def _get_default_x_organization_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id.organization_first
        else:
            return False

    def _get_default_x_responsible_dept_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id and employee_id.department_jurisdiction_first:
            return employee_id.department_jurisdiction_first[0]
        else:
            return False

    @api.onchange('x_organization_id')
    def _onchange_x_organization_id(self):
        if self.x_organization_id:
            self.location_id = False
            self.x_responsible_dept_id = False
            # self.scrap_type = False
            self.scrap_location_id = False
            if self.x_organization_id.name == '安来ガスセンター':
                self.x_require_responsible_dept = False
            else:
                self.x_require_responsible_dept = True

    @api.constrains('user_id', 'x_responsible_id', 'x_organization_id')
    def _validate_responsible_department(self):
        for rec in self:
            employee_id = self.env['hr.employee'].search([('user_id', '=', rec.user_id.id)], limit=1)
            if employee_id:
                if rec.x_organization_id:
                    org_ids = [employee_id.organization_first, employee_id.organization_second,
                               employee_id.organization_third]
                    if rec.x_organization_id not in org_ids:
                        raise UserError('担当者の所属組織を選択してください')
                if rec.x_responsible_dept_id:
                    derp_ids = [employee_id.department_jurisdiction_first,
                                employee_id.department_jurisdiction_second,
                                employee_id.department_jurisdiction_third]
                    if rec.x_responsible_dept_id not in derp_ids:
                        raise UserError('担当者の所属部署を選択してください')
            else:
                raise UserError('選択した担当者は従業員に紐づけしていません。')

    scrap_type = fields.Many2one('ss_erp.stock.scrap.category', string='廃棄種別', required=False, )


class ScrapCategory(models.Model):
    _name = 'ss_erp.stock.scrap.category'
    _description = '廃棄種別'

    name = fields.Char('廃棄種別名称')