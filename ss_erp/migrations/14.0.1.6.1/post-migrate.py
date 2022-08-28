from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    approval_request_internal_notedit_rule = env.ref(
        "ss_erp.approval_request_internal_notedit_rule",
        raise_if_not_found=False
    )
    if approval_request_internal_notedit_rule:
        approval_request_internal_notedit_rule.unlink()
