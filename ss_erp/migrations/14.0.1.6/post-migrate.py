def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    ss_erp_responsible_department    
DROP CONSTRAINT IF EXISTS    
    ss_erp_responsible_department_unique_department_code;    
    """)
