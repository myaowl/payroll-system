from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QDialog, QTableWidgetItem,
                              QMessageBox, QHBoxLayout, QPushButton,
                              QVBoxLayout, QLabel, QLineEdit,
                              QTableWidget, QHeaderView, QApplication)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from database import get_connection
from confirm_dialog import confirm


# ── Add / Edit Employee Dialog ────────────────────────────────────────────────
class AddEmployeeDialog(QDialog):
    def __init__(self, emp_data=None, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/add_employee.ui", self)
        self.emp_data = emp_data
        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.reject)

        if emp_data:
            self.dlgTitle.setText("Edit Employee")
            self.txtEmpId.setText(emp_data["emp_id"])
            self.txtEmpId.setReadOnly(True)
            self.txtFirstName.setText(emp_data["first_name"])
            self.txtLastName.setText(emp_data["last_name"])
            idx = self.cmbDepartment.findText(emp_data["department"] or "")
            if idx >= 0: self.cmbDepartment.setCurrentIndex(idx)
            self.txtPosition.setText(emp_data["position"] or "")
            self.txtEmail.setText(emp_data["email"] or "")
            self.txtPhone.setText(emp_data["phone"] or "")
            if emp_data["hire_date"]:
                self.dtHireDate.setDate(QDate.fromString(emp_data["hire_date"], "yyyy-MM-dd"))
            idx2 = self.cmbStatus.findText(emp_data["status"] or "Active")
            if idx2 >= 0: self.cmbStatus.setCurrentIndex(idx2)

    def save(self):
        emp_id     = self.txtEmpId.text().strip()
        first_name = self.txtFirstName.text().strip()
        last_name  = self.txtLastName.text().strip()

        if not emp_id or not first_name or not last_name:
            self.errorLabel.setText("Employee ID, First Name and Last Name are required.")
            return

        conn   = get_connection()
        cursor = conn.cursor()
        try:
            if self.emp_data:
                conn.close()
                if not confirm(self, "Save Changes",
                        f"Save changes to employee {emp_id}?",
                        confirm_text="✔  Save", confirm_color="#4a9eff", icon="✏️"):
                    return
                conn = get_connection(); cursor = conn.cursor()
                cursor.execute("""
                    UPDATE employees SET first_name=?, last_name=?, department=?,
                    position=?, email=?, phone=?, hire_date=?, status=?
                    WHERE emp_id=?
                """, (first_name, last_name, self.cmbDepartment.currentText(),
                      self.txtPosition.text(), self.txtEmail.text(),
                      self.txtPhone.text(), self.dtHireDate.date().toString("yyyy-MM-dd"),
                      self.cmbStatus.currentText(), emp_id))
                conn.commit()
                self.accept()
            else:
                cursor.execute("""
                    INSERT INTO employees (emp_id,first_name,last_name,department,
                    position,email,phone,hire_date,status)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (emp_id, first_name, last_name, self.cmbDepartment.currentText(),
                      self.txtPosition.text(), self.txtEmail.text(),
                      self.txtPhone.text(), self.dtHireDate.date().toString("yyyy-MM-dd"),
                      self.cmbStatus.currentText()))

                username = emp_id.lower()
                password = first_name.lower() + emp_id[-4:].lower()
                cursor.execute("""
                    INSERT OR IGNORE INTO users (username, password, role, emp_id)
                    VALUES (?, ?, 'employee', ?)
                """, (username, password, emp_id))

                conn.commit()

                QMessageBox.information(self, "Employee Added",
                    f"✅  Employee created successfully!\n\n"
                    f"📋  Login Credentials:\n"
                    f"     Username :  {username}\n"
                    f"     Password :  {password}\n\n"
                    f"Please share these credentials with the employee.")
                self.accept()

        except Exception as e:
            self.errorLabel.setText(str(e))
        finally:
            conn.close()


# ── Credentials Dialog ────────────────────────────────────────────────────────
class CredentialsDialog(QDialog):
    """Shows username & password for an employee with a copy button."""
    def __init__(self, emp_id, emp_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Employee Credentials")
        self.setFixedSize(480, 300)
        self.setStyleSheet("background:#1e2a3a; color:#c8d6e5;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # Title
        title = QLabel("🔐  Login Credentials")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#ffffff;")
        layout.addWidget(title)

        sub = QLabel(f"Employee: {emp_name}  ({emp_id})")
        sub.setStyleSheet("color:#8a9bb0;font-size:12px;")
        layout.addWidget(sub)

        # Fetch from DB
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users WHERE emp_id=?", (emp_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            username, password = row[0], row[1]

            def field_row(label, value):
                from PyQt5.QtWidgets import QLineEdit
                box = QVBoxLayout(); box.setSpacing(4)
                lbl = QLabel(label)
                lbl.setStyleSheet("color:#8a9bb0;font-size:11px;")
                val_row = QHBoxLayout()

                # Use QLineEdit (readonly) instead of QLabel — renders text reliably
                val_edit = QLineEdit(value)
                val_edit.setReadOnly(True)
                val_edit.setMinimumWidth(280)
                val_edit.setFixedHeight(38)
                val_edit.setStyleSheet("""
                    QLineEdit {
                        background:#253447; border:1px solid #3a4f66;
                        border-radius:6px; padding:8px 14px;
                        color:#ffffff; font-size:15px;
                        font-family: Arial, sans-serif;
                        selection-background-color:#4a9eff;
                    }
                """)
                from PyQt5.QtGui import QFont as _QFont
                _f = _QFont("Arial", 12)
                _f.setBold(False)
                val_edit.setFont(_f)

                copy_btn = QPushButton("Copy")
                copy_btn.setFixedHeight(36)
                copy_btn.setFixedWidth(60)
                copy_btn.setStyleSheet("""
                    QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
                    border-radius:6px;font-size:12px;font-weight:bold;}
                    QPushButton:hover{background:#4a9eff;color:#fff;}
                """)
                copy_btn.clicked.connect(lambda _, v=value, b=copy_btn: (
                    QApplication.clipboard().setText(v),
                    b.setText("✔ Done"),
                    b.setStyleSheet("QPushButton{background:#2ecc71;color:#fff;border:none;border-radius:6px;font-size:11px;font-weight:bold;}")
                ))
                val_row.addWidget(val_edit, 1)
                val_row.addWidget(copy_btn)
                box.addWidget(lbl)
                box.addLayout(val_row)
                return box

            layout.addLayout(field_row("Username", username))
            layout.addLayout(field_row("Password", password))
        else:
            no_creds = QLabel("⚠  No login account found for this employee.")
            no_creds.setStyleSheet("color:#f39c12;font-size:13px;")
            no_creds.setWordWrap(True)
            layout.addWidget(no_creds)

        layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("""
            background:#2a3d55;color:#c8d6e5;border:none;
            border-radius:6px;padding:9px;font-size:13px;
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


# ── Manage Employees Widget ───────────────────────────────────────────────────
class ManageEmployees(QWidget):
    on_data_changed = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.load_employees()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("👥 Manage Employees")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#fff;")
        hdr.addWidget(title)
        hdr.addStretch()

        self.txtSearch = QLineEdit()
        self.txtSearch.setPlaceholderText("🔍 Search employees…")
        self.txtSearch.setFixedWidth(220)
        self.txtSearch.setStyleSheet("background:#253447;border:1px solid #3a4f66;border-radius:6px;padding:7px 10px;color:#fff;")
        self.txtSearch.textChanged.connect(self.filter_table)
        hdr.addWidget(self.txtSearch)

        btnAdd = QPushButton("+ Add Employee")
        btnAdd.setStyleSheet("background:#4a9eff;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;")
        btnAdd.clicked.connect(self.add_employee)
        hdr.addWidget(btnAdd)
        layout.addLayout(hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Emp ID", "Name", "Department", "Position",
            "Email", "Phone", "Hire Date", "Username", "Actions"
        ])

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)       # all columns share space
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Emp ID
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Phone
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Hire Date
        hh.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Username
        hh.setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 120)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.setStyleSheet("""
            QTableWidget {
                background:#253447; border:none; border-radius:8px;
                color:#c8d6e5; alternate-background-color:#1e2a3a;
                gridline-color:#2a3d55;
            }
            QTableWidget::item { padding:4px; }
            QTableWidget::item:selected { background:#4a9eff30; color:#ffffff; }
        """)
        hh.setStyleSheet("background:#1e2a3a;color:#8a9bb0;padding:4px;")
        layout.addWidget(self.table)

    def load_employees(self, search=""):
        conn   = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT e.emp_id, e.first_name||' '||e.last_name,
                   e.department, e.position, e.email, e.phone,
                   e.hire_date, COALESCE(u.username, '—')
            FROM employees e
            LEFT JOIN users u ON e.emp_id = u.emp_id
        """
        if search:
            query += " WHERE e.emp_id LIKE ? OR e.first_name LIKE ? OR e.last_name LIKE ?"
            cursor.execute(query + " ORDER BY e.emp_id",
                           (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            cursor.execute(query + " ORDER BY e.emp_id")
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            for col, val in enumerate(row_data):
                item = QTableWidgetItem(str(val or ""))
                item.setTextAlignment(Qt.AlignCenter)
                # Highlight username column subtly
                if col == 7:
                    item.setForeground(QColor("#4a9eff"))
                    f = QFont(); f.setBold(True)
                    item.setFont(f)
                self.table.setItem(row, col, item)

            # Actions cell
            emp_id   = row_data[0]
            emp_name = row_data[1]
            cell     = QWidget()
            h        = QHBoxLayout(cell)
            h.setContentsMargins(4, 2, 4, 2)
            h.setSpacing(4)

            def _icon_btn(icon, bg_hover):
                b = QPushButton(icon)
                b.setFixedSize(32, 32)
                b.setFocusPolicy(Qt.NoFocus)
                b.setCursor(Qt.PointingHandCursor)
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        font-size: 18px;
                        padding: 2px;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        background: {bg_hover};
                    }}
                    QPushButton:focus {{
                        background: transparent;
                        outline: none;
                        border: none;
                    }}
                """)
                return b

            btn_creds = _icon_btn("🔑", "#f39c12")
            btn_creds.clicked.connect(
                lambda _, eid=emp_id, ename=emp_name: self.show_credentials(eid, ename))

            btn_edit = _icon_btn("✏️", "#4a9eff")
            btn_edit.clicked.connect(lambda _, eid=emp_id: self.edit_employee(eid))

            btn_del = _icon_btn("🗑️", "#ff6b6b")
            btn_del.clicked.connect(lambda _, eid=emp_id: self.delete_employee(eid))

            h.addStretch()
            h.addWidget(btn_creds)
            h.addWidget(btn_edit)
            h.addWidget(btn_del)
            h.addStretch()
            self.table.setCellWidget(row, 8, cell)

    def filter_table(self, text):
        self.load_employees(text)

    def _notify(self):
        if callable(self.on_data_changed):
            self.on_data_changed()

    def show_credentials(self, emp_id, emp_name):
        dlg = CredentialsDialog(emp_id, emp_name, parent=self)
        dlg.exec_()

    def add_employee(self):
        dlg = AddEmployeeDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.load_employees()
            self._notify()

    def edit_employee(self, emp_id):
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            dlg = AddEmployeeDialog(emp_data=dict(row), parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self.load_employees()
                self._notify()

    def delete_employee(self, emp_id):
        if not confirm(self, "Delete Employee",
                f"Are you sure you want to delete employee {emp_id}?\n\nThis will also remove their salary, payslips, leave records and login account.",
                confirm_text="Delete", confirm_color="#e74c3c", icon="🗑"):
            return
        if True:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees      WHERE emp_id=?", (emp_id,))
            cursor.execute("DELETE FROM salary         WHERE emp_id=?", (emp_id,))
            cursor.execute("DELETE FROM payslips       WHERE emp_id=?", (emp_id,))
            cursor.execute("DELETE FROM leave_requests WHERE emp_id=?", (emp_id,))
            cursor.execute("DELETE FROM users          WHERE emp_id=?", (emp_id,))
            conn.commit()
            conn.close()
            self.load_employees()
            self._notify()