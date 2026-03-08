from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QDialog, QTableWidgetItem,
                              QMessageBox, QHBoxLayout, QPushButton,
                              QVBoxLayout, QLabel, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from database import get_connection


class SalaryDialog(QDialog):
    def __init__(self, emp_id, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/salary_manage.ui", self)
        self.emp_id = emp_id
        self.txtEmpId.setText(emp_id)

        # live net-pay preview
        for spn in [self.spnBasic, self.spnAllowances, self.spnDeductions, self.spnTaxRate]:
            spn.valueChanged.connect(self.update_preview)

        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.reject)
        self.load_existing()

    def update_preview(self):
        basic      = self.spnBasic.value()
        allowances = self.spnAllowances.value()
        deductions = self.spnDeductions.value()
        tax_rate   = self.spnTaxRate.value() / 100
        gross      = basic + allowances
        tax        = gross * tax_rate
        net        = gross - tax - deductions
        self.lblNetPreview.setText(f"Net Pay Preview: ₱{net:,.2f}")

    def load_existing(self):
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM salary WHERE emp_id=? ORDER BY id DESC LIMIT 1", (self.emp_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.spnBasic.setValue(row["basic_salary"])
            self.spnAllowances.setValue(row["allowances"])
            self.spnDeductions.setValue(row["deductions"])
            self.spnTaxRate.setValue(row["tax_rate"])
            if row["effective_date"]:
                self.dtEffective.setDate(QDate.fromString(row["effective_date"], "yyyy-MM-dd"))
        self.update_preview()

    def save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO salary (emp_id, basic_salary, allowances, deductions, tax_rate, effective_date)
                VALUES (?,?,?,?,?,?)
            """, (self.emp_id, self.spnBasic.value(), self.spnAllowances.value(),
                  self.spnDeductions.value(), self.spnTaxRate.value(),
                  self.dtEffective.date().toString("yyyy-MM-dd")))
            conn.commit()
            self.accept()
        except Exception as e:
            self.errorLabel.setText(str(e))
        finally:
            conn.close()


class ManageSalary(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        from PyQt5.QtWidgets import QTableWidget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr   = QHBoxLayout()
        title = QLabel("💰 Manage Salaries")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#fff;")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Emp ID", "Name", "Basic (₱)", "Allowances (₱)", "Deductions (₱)", "Tax (%)", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("background:#253447;border:none;border-radius:8px;color:#c8d6e5;alternate-background-color:#1e2a3a;")
        self.table.horizontalHeader().setStyleSheet("background:#1e2a3a;color:#8a9bb0;")
        layout.addWidget(self.table)

    def load_data(self):
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.emp_id, e.first_name||' '||e.last_name,
                   COALESCE(s.basic_salary,0), COALESCE(s.allowances,0),
                   COALESCE(s.deductions,0),   COALESCE(s.tax_rate,0)
            FROM employees e
            LEFT JOIN salary s ON e.emp_id = s.emp_id
              AND s.id = (SELECT MAX(id) FROM salary WHERE emp_id=e.emp_id)
            ORDER BY e.emp_id
        """)
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data):
                text = f"₱{val:,.2f}" if col in (2,3,4) else (f"{val}%" if col==5 else str(val))
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            emp_id = row_data[0]
            cell   = QWidget()
            h      = QHBoxLayout(cell)
            h.setContentsMargins(4,2,4,2)
            btn = QPushButton("✏ Set Salary")
            btn.setStyleSheet("background:#4a9eff30;color:#4a9eff;border:none;border-radius:4px;padding:4px 10px;")
            btn.clicked.connect(lambda _, eid=emp_id: self.open_salary_dialog(eid))
            h.addWidget(btn)
            self.table.setCellWidget(row, 6, cell)

    def open_salary_dialog(self, emp_id):
        dlg = SalaryDialog(emp_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.load_data()