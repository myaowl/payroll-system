import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "payroll.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id      TEXT UNIQUE NOT NULL,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            department  TEXT,
            position    TEXT,
            email       TEXT,
            phone       TEXT,
            hire_date   TEXT,
            status      TEXT DEFAULT 'Active'
        );

        CREATE TABLE IF NOT EXISTS salary (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id          TEXT NOT NULL,
            basic_salary    REAL DEFAULT 0,
            allowances      REAL DEFAULT 0,
            deductions      REAL DEFAULT 0,
            tax_rate        REAL DEFAULT 0,
            effective_date  TEXT,
            FOREIGN KEY(emp_id) REFERENCES employees(emp_id)
        );

        CREATE TABLE IF NOT EXISTS leave_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id      TEXT NOT NULL,
            leave_type  TEXT,
            start_date  TEXT,
            end_date    TEXT,
            reason      TEXT,
            status      TEXT DEFAULT 'Pending',
            applied_on  TEXT,
            FOREIGN KEY(emp_id) REFERENCES employees(emp_id)
        );

        CREATE TABLE IF NOT EXISTS payslips (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id          TEXT NOT NULL,
            month           TEXT,
            year            TEXT,
            basic_salary    REAL,
            allowances      REAL,
            deductions      REAL,
            tax_amount      REAL,
            net_pay         REAL,
            generated_on    TEXT,
            FOREIGN KEY(emp_id) REFERENCES employees(emp_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT DEFAULT 'employee',
            emp_id      TEXT
        );
    """)

    # Default admin user (password: admin123)
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES ('admin', 'admin123', 'admin')
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_db()
    print("Database initialized successfully.")