from odoo import _, api, fields, models
from odoo.exceptions import UserError


class IfdbAutogasFileDataRec(models.Model):
    _name = "ss_erp.ifdb.autogas.file.data.rec"
    _description = "Autogas File Data Record"

    autogas_file_header_id = fields.Many2one(
        comodel_name="ss_erp.ifdb.autogas.file.header",
        string="オートガスPOSファイルヘッダ",
        required=True,
        ondelete="cascade"
    )
    status = fields.Selection(
        selection=[
            ("wait", "処理待ち"),
            ("success", "成功"),
            ("error", "エラー")
        ],
        string="ステータス",
        readonly=True,
        required=True,
        index=True,
        default="wait"
    )
    processing_date = fields.Datetime(
        string="処理日時",
        readonly=True
    )
    card_classification = fields.Char(
        string="カード区分"
    )
    processing_division = fields.Char(
        string="処理区分"
    )
    unused = fields.Char(
        string="未使用"
    )
    group_division = fields.Char(
        string="グループ区分"
    )
    actual_car_number = fields.Char(
        string="実車番"
    )
    card_number = fields.Char(
        string="カード番号"
    )
    product_code = fields.Char(
        string="商品コード"
    )
    data_no = fields.Char(
        string="データNo"
    )
    quantity_1 = fields.Char(
        string="数量1"
    )
    unit_price = fields.Char(
        string="単価"
    )
    amount_of_money = fields.Char(
        string="金額"
    )
    staff_code = fields.Char(
        string="係員コード"
    )
    processing_time = fields.Char(
        string="処理時刻"
    )
    calendar_date = fields.Char(
        string="カレンダー日付"
    )
    consumption_tax_output_classification = fields.Char(
        string="消費税出力区分"
    )
    consumption_tax = fields.Char(
        string="消費税"
    )
    credit_terminal_processing_serial_number = fields.Char(
        string="クレジット端末処理通番"
    )
    credit_classification = fields.Char(
        string="クレジット区分"
    )
    credit_data_no = fields.Char(
        string="クレジットデータNo"
    )
    tax_classification_code = fields.Char(
        string="課税区分コード"
    )
    filer1 = fields.Char(
        string="Filer1"
    )
    quantity_2 = fields.Char(
        string="数量2"
    )
    filer2 = fields.Char(
        string="Filer2"
    )
    error_message = fields.Char(
        string="エラーメッセージ",
        readonly=True
    )
    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="販売オーダ参照",
        readonly=True
    )
    customer_code = fields.Char(
        string="得意先コード",
        compute="_compute_customer_code",
        store=True,
        size=4
    )

    _sql_constraints = [
        ("card_number_length",
        "CHECK(LENGTH(card_number) >= 12)",
        "Card Number length must be bigger than 12")
    ]

    @api.depends("card_number")
    def _compute_customer_code(self):
        for r in self:
            r.customer_code = r.card_number[7:11]
