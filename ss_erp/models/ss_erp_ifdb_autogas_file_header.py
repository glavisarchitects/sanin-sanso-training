from odoo import _, api, fields, models


class IFDBAutogasFileHeader(models.Model):
    _name = "ss_erp.ifdb.autogas.file.header"
    _description = "Autogas File Header"

    upload_date = fields.Datetime(
        string="アップロード日時",
        index=True,
        required=True,
        readonly=True
    )
    name = fields.Char(
        string="名称",
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="担当者",
        required=True,
        index=True
    )
    branch_id = fields.Many2one(
        comodel_name="ss_erp.organization",
        string="支店",
        index=True
    )
    status = fields.Selection(
        selection=[
            ("wait", "処理待ち"),
            ("success", "成功"),
            ("error", "エラーあり")
        ],
        string="ステータス",
        required=True,
        index=True,
        default="wait"
    )
    autogas_data_record_ids = fields.One2many(
        comodel_name="ss_erp.ifdb.autogas.file.data.rec",
        inverse_name="autogas_file_header_id",
        string="データレコード"
    )

    def action_processing_excution(self):
        for r in self:
            r._processing_excution()

    def _processing_excution(self):
        self.ensure_one()
        return True
