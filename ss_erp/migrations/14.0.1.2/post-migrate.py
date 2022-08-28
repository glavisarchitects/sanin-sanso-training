def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    ss_erp_product_price
DROP CONSTRAINT IF EXISTS
    ss_erp_product_price__unique;
    """)
