import logging
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PartnerRequestAbstract(models.AbstractModel):
    _name = "x.x_partner.partner_request_abstract"
    _description = "Partner Request Abstract"

    @api.model
    def _default_founding_year(self):
        return str(fields.Date.today().year)

    x_partner_code = fields.Char(string="取引先コード")
    x_furigana_name = fields.Char(string="フリガナ")
    x_contact_classification = fields.Selection(
        selection=[("customer", "得意先"), ("supplier", "仕入先")],
        string="連絡先区分", default="customer")
    x_founding_year = fields.Char(string="創立年度", default=_default_founding_year)
    x_capital = fields.Char(string="資本金")
    x_fax_number = fields.Char(string="FAX代表", size=20)
    x_payment_notice_fax_number = fields.Char(string="支払通知書FAX", size=20)
    x_payment_term_using = fields.Selection(
        selection=[("regular", "当社規定(規定詳細参照)"), ("other", "その他")],
        string="支払条件", required=True, default="regular"
    )
    x_other_payment_term = fields.Char(string="その他支払条件")
    x_reason_to_change_payment_term = fields.Text(string="変動理由")
    x_purchase_area = fields.Char(string="購買地域")
    x_transaction_basic_contract = fields.Selection(
        selection=[("conclusion", "締結"), ("no_fastening", "締結しない"), ("not_applicable", "該当なし")],
        string="取引基本契約書", required=True, default="conclusion"
    )
    x_contract_not_apply_reason = fields.Text(string="理由")


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "x.x_partner.partner_request_abstract"]


    @api.model
    def _default_transaction_classification(self):
        return self.env["x.transaction.classification"].search([("default", "=", True)]).ids

    @api.model
    def _default_department_classification(self):
        return self.env["x.department.classification"].search([("default", "=", True)]).ids

    x_contact_classification = fields.Selection(
        selection_add=[("other", "その他")], default="other"
    )
    x_transaction_classification = fields.Many2many(
        "x.transaction.classification", default=_default_transaction_classification,
        string="取引区分"
    )
    x_department_classification = fields.Many2one(
        comodel_name="x.department.classification", string="部門"
    )
    x_partner_performance = fields.One2many(
        comodel_name="x.partner.sales.information", inverse_name="partner_id",
        string="業績情報"
    )
    x_show_construction_permit = fields.Boolean(
        string="Show Construction Permit", compute="_compute_x_show_construction_permit",
        help="This is a technical field, to indicate whether or not construction permit "
             "should be shown on form"
    )
    x_partner_construction_permit = fields.One2many(
        comodel_name="x.x_partner.partner_construction_permit", inverse_name="partner_id",
        string="建設業許可"
    )
    x_control_account = fields.Many2one(
        comodel_name="account.account", string="統制勘定"
    )
    x_sale_area = fields.Char(string="Sale Area")
    x_minimum_sale = fields.Char("Minimum Sales", copy=False)
    x_receipt_place = fields.Many2one(
        comodel_name="stock.location", string="Receipt Location",
        ondelete="restrict", copy=False
    )
    x_purchase_person_id = fields.Many2one(
        comodel_name="res.users", string="購買担当者", domain=[("share", "=", False)]
    )
    x_minimum_purchase = fields.Char("最低仕入価格", copy=False)
    x_delivery_place = fields.Many2one(
        comodel_name="stock.location", string="納品場所",
        ondelete="restrict", copy=False
    )

    @api.onchange("x_transaction_classification")
    def _onchange_x_transaction_classification(self):
        for r in self:
            return {
                "domain": {
                    "x_department_classification":
                        [("transaction_classify_id", "in", r.x_transaction_classification.ids)]
                }
            }

    @api.depends("x_transaction_classification")
    def _compute_x_show_construction_permit(self):
        construction_id = self.env.ref("x_partner.transaction_classification_construction").id
        for r in self:
            r.x_show_construction_permit = construction_id in r.x_transaction_classification.ids

    @api.model
    def default_get(self, fields_list):
        res = super(ResPartner, self).default_get(fields_list)
        res.update({
            "country_id": self.env.ref("base.jp").id
        })
        return res
