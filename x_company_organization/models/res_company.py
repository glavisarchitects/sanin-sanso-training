from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    x_code = fields.Char(
        string="Company Code", required=True, copy=False, size=20,
        help="Company's abbreviation name for internal purpose."
    )

    _sql_constraints = [
        ("code_uniq", "UNIQUE(x_code)", "Company's Abbreviation Name Should Be Unique!")
    ]

    def name_get(self):
        res = []
        for r in self:
            name = "%s (%s)" % (r.name, r.x_code) if r.x_code else r.name
            res.append((r.id, name))
        return res
