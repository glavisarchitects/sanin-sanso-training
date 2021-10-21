from odoo import fields, models
from odoo.models import NewId


class ResCompany(models.Model):
    _inherit = "res.company"

    x_company_code = fields.Char(
        string="会社コード", index=True, required=True,
    )
    x_payment_terms = fields.Html(
        string="支払条件当社規定", sanitize=True
    )
    x_construction_contract_notice = fields.Html(
        string="工事契約における注記事項", sanitize=True
    )
    x_construction_subcontract = fields.Html(
        string="下請工事の予定価格と見積期間", sanitize=True
    )

    def _default_company_code(self):
        if not isinstance(self.id, NewId):
            return "%05d" % self.id
        return ""

    # _sql_constraints = [(
    #     "company_code_uniq",
    #     "UNIQUE(x_company_code)",
    #     "Company code should be unique!"
    # )]
