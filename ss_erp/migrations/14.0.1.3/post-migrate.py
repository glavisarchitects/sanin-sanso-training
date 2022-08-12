def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    ss_erp_organization
DROP CONSTRAINT IF EXISTS
    ss_erp_organization_unique_organization_code;
    """)
