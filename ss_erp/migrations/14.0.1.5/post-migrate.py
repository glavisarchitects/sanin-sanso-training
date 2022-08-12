def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    ss_erp_organization_category    
DROP CONSTRAINT IF EXISTS    
    ss_erp_organization_category_check_hierarchy_number;    
    """)
