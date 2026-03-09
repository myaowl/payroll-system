import csv
import datetime
from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QTableWidgetItem, QMessageBox,
                              QFileDialog, QHeaderView)
from PyQt5.QtCore import Qt
from database import get_connection


class SalaryReport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/salary_report.ui", self)
        self._setup_filters()
        self.btnFilter.clicked.connect(self.load_report)
        self.btnExport.clicked.connect(self.export_csv)
        self.load_report()

    def _setup_filters(self):
        cur_yr = datetime.date.today().year
        self.cmbYear.addItem("All")
        for y in range(cur_yr - 3, cur_yr + 2):
            self.cmbYear.addItem(str(y))
        self.cmbYear.setCurrentText(str(cur_yr))

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM employees WHERE department IS NOT NULL ORDER BY department")
        depts = [r[0] for r in cursor.fetchall()]
        conn.close()
        self.cmbDept.addItem("All")
        self.cmbDept.addItems(depts)

    def load_report(self):
        month = self.cmbMonth.currentText()
        year  = self.cmbYear.currentText()
        dept  = self.cmbDept.currentText()

        query  = """
            SELECT p.emp_id, e.first_name||' '||e.last_name, e.department,
                   p.month||'/'||p.year,
                   p.basic_salary + p.allowances,
                   p.deductions, p.tax_amount, p.net_pay
            FROM payslips p
            LEFT JOIN employees e ON p.emp_id = e.emp_id
            WHERE 1=1
        """
        params = []
        if month != "All":
            query += " AND p.month=?"; params.append(month)
        if year != "All":
            query += " AND p.year=?";  params.append(year)
        if dept != "All":
            query += " AND e.department=?"; params.append(dept)
        query += " ORDER BY p.year DESC, p.month DESC, p.emp_id"

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Summary
        total_net  = sum(r[7] for r in rows)
        avg_net    = total_net / len(rows) if rows else 0
        total_tax  = sum(r[6] for r in rows)
        count      = len(rows)
        self.valTotalPayroll.setText(f"₱{total_net:,.2f}")
        self.valAvgPay.setText(f"₱{avg_net:,.2f}")
        self.valTotalTax.setText(f"₱{total_tax:,.2f}")
        self.valCount.setText(str(count))

        # Table
        self.tblReport.setRowCount(0)
        self.tblReport.setColumnCount(8)
        self.tblReport.setHorizontalHeaderLabels([
            "Emp ID", "Employee Name", "Department", "Period",
            "Basic Salary", "Allowances", "Tax Deducted", "Net Pay"
        ])
        hh = self.tblReport.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tblReport.setAlternatingRowColors(True)
        self.tblReport.setStyleSheet("""
            QTableWidget {
                background:#253447; alternate-background-color:#1e2a3a;
                border:none; border-radius:8px; gridline-color:#2a3d55; color:#c8d6e5;
            }
            QTableWidget::item { padding:6px 4px; color:#c8d6e5; }
            QTableWidget::item:selected { background:#4a9eff30; color:#fff; }
            QHeaderView::section {
                background:#1e2a3a; color:#8a9bb0; padding:8px;
                border:none; border-bottom:1px solid #2a3d55; font-weight:bold;
            }
        """)
        bg_even = __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#253447")
        bg_odd  = __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#1e2a3a")
        c_white = __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#c8d6e5")
        c_green = __import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#2ecc71")
        for row_data in rows:
            row = self.tblReport.rowCount()
            self.tblReport.insertRow(row)
            formatted = [
                row_data[0], row_data[1] or "", row_data[2] or "",
                row_data[3],
                f"₱{row_data[4]:,.2f}", f"₱{row_data[5]:,.2f}",
                f"₱{row_data[6]:,.2f}", f"₱{row_data[7]:,.2f}"
            ]
            bg = bg_even if row % 2 == 0 else bg_odd
            for col, val in enumerate(formatted):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                item.setForeground(c_green if col == 7 else c_white)
                self.tblReport.setItem(row, col, item)

        self._raw_rows = rows  # keep for export

    def export_csv(self):
        if not hasattr(self, "_raw_rows") or not self._raw_rows:
            QMessageBox.information(self, "No Data", "No data to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", f"salary_report_{datetime.date.today()}.csv", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Emp ID", "Name", "Department", "Month/Year",
                              "Gross", "Deductions", "Tax", "Net Pay"])
            for r in self._raw_rows:
                writer.writerow([r[0], r[1], r[2], r[3],
                                 f"{r[4]:.2f}", f"{r[5]:.2f}", f"{r[6]:.2f}", f"{r[7]:.2f}"])

        QMessageBox.information(self, "Exported", f"Report saved to:\n{path}")