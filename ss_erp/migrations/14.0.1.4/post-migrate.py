def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    ss_erp_organization_category
DROP CONSTRAINT IF EXISTS
    ss_erp_organization_category_name_uniq;
ALTER TABLE
    ss_erp_organization_category    
DROP CONSTRAINT IF EXISTS    
    ss_erp_organization_category_name_hierarchy_number;
ALTER TABLE
    ss_erp_organization_category    
DROP CONSTRAINT IF EXISTS    
    ss_erp_organization_category_check_hierarchy_number;    
    """)
