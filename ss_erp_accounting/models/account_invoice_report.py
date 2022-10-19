from odoo import fields, models, api


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    x_organization_id = fields.Many2one('ss_erp.organization', string="販売組織", readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", move.x_organization_id as x_organization_id"

    def _where(self):
        return '''
            WHERE move.move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt','counstruction_out_invoice','construction_in_invoice')
                AND line.account_id IS NOT NULL
                AND NOT line.exclude_from_invoice_tab
        '''
