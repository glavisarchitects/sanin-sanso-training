def migrate(cr, version):
    cr.execute(
        """
ALTER TABLE
    ss_erp_instruction_order_line
DROP CONSTRAINT IF EXISTS 
    ss_erp_instruction_order_line_product_qty_fkey;
ALTER TABLE
    ss_erp_instruction_order_line
DROP CONSTRAINT IF EXISTS
    ss_erp_instruction_order_line_product_cost_fkey;
ALTER TABLE
    stock_inventory_line
DROP CONSTRAINT IF EXISTS
    stock_inventory_line_product_cost_fkey;
ALTER TABLE
    ss_erp_instruction_order_line
ALTER COLUMN product_qty SET DATA TYPE DOUBLE PRECISION
USING product_qty::DOUBLE PRECISION,
ALTER COLUMN product_cost SET DATA TYPE DOUBLE PRECISION
USING product_cost::DOUBLE PRECISION;
ALTER TABLE
    stock_inventory_line
ALTER COLUMN product_cost SET DATA TYPE DOUBLE PRECISION
USING product_cost::DOUBLE PRECISION;
        """
    )