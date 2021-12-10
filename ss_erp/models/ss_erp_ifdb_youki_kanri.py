from odoo import models, fields, api


class YoukiKanri(models.Model):
    _name = "ss_erp.ifdb.youki.kanri"
    _description = "Youki Kanri"

    name = fields.Char(
        string="名称"
    )
    upload_date = fields.Datetime(
        string="アップロード日時",
        index=True
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="担当者",
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
            ("error", "エラーあり"),
        ],
        string="ステータス",
        required=True,
        default="wait",
        index=True,
        readonly=True
    )
    youki_kanri_detail_ids = fields.One2many(comodel_name="ss_erp.ifdb.youki.kanri.detail",
                                             inverse_name="ifdb_youki_kanri_id")

    _sql_constraints = [
        (
            "name_uniq",
            "UNIQUE(name)",
            "Name is used for searching, please make it unique!"
        )
    ]

    def action_import(self):
        self.ensure_one()
        self.upload_date = fields.Datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "import",
            "params": {
                "model": "ss_erp.ifdb.youki.kanri.detail",
                "context": {
                    "default_import_file_header_model": self._name,
                    "default_import_file_header_id": self.id,
                },
            }
        }

    def action_processing_execution(self):
        for r in self:
            r._processing_execution()

    def _processing_execution(self):
        self.ensure_one()
        return True
