def migrate(cr, version):
    cr.execute("""
ALTER TABLE res_partner_bank ALTER COLUMN partner_id DROP NOT NULL;
    """)