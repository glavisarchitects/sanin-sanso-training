def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    ss_erp_ifdb_propane_sales_header    
DROP CONSTRAINT IF EXISTS    
    name_unique;    

ALTER TABLE
    ss_erp_ifdb_powernet_sales_header 
DROP CONSTRAINT IF EXISTS    
    name_uniq;    

ALTER TABLE
    ss_erp_ifdb_youki_kanri  
DROP CONSTRAINT IF EXISTS    
    name_uniq;    

ALTER TABLE
    ss_erp_ifdb_autogas_file_data_rec 
DROP CONSTRAINT IF EXISTS    
    card_number_length;    

ALTER TABLE
    ss_erp_ifdb_youkikensa_billing_file_header  
DROP CONSTRAINT IF EXISTS    
    name_uniq;

ALTER TABLE
    ss_erp_ifdb_autogas_file_header
DROP CONSTRAINT IF EXISTS    
    name_uniq;     
      
    """)