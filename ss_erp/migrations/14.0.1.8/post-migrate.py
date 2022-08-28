def migrate(cr, version):
    cr.execute("""
ALTER TABLE
    hr_employee    
DROP CONSTRAINT IF EXISTS    
    hr_employee_employee_number_uniq;    
    """)
