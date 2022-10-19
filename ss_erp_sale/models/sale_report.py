from odoo import fields, models, api


class SaleReport(models.Model):
    _inherit = 'sale.report'

    x_organization_id = fields.Many2one('ss_erp.organization', string="販売組織", readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['x_organization_id'] = ', s.x_organization_id as x_organization_id'
        groupby += """
            , s.x_organization_id
            """
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
