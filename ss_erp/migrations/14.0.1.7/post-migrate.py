def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    ss_erp_res_partner_form    
DROP CONSTRAINT IF EXISTS    
    ss_erp_res_partner_form_phone_unique;    
    """)
