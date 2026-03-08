"""
Run this ONCE to clean up orphaned payslip/salary/leave records
left behind from employees deleted before the cascade-delete fix.

Usage:  python cleanup_orphans.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection

conn   = get_connection()
cursor = conn.cursor()

cursor.executescript("""
    DELETE FROM payslips
        WHERE emp_id NOT IN (SELECT emp_id FROM employees);

    DELETE FROM salary
        WHERE emp_id NOT IN (SELECT emp_id FROM employees);

    DELETE FROM leave_requests
        WHERE emp_id NOT IN (SELECT emp_id FROM employees);

    DELETE FROM users
        WHERE role = 'employee'
        AND emp_id NOT IN (SELECT emp_id FROM employees);
""")

conn.commit()
conn.close()
print("✅ Orphaned records cleaned up successfully.")