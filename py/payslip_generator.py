import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox,
                              QDialog, QScrollArea, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from py.database import get_connection
from py.confirm_dialog import confirm


class PayslipPreviewDialog(QDialog):
    """Shows a printable payslip."""
    def __init__(self, payslip_data, emp_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Payslip Preview")
        self.setMinimumSize(500, 640)
        self.setStyleSheet("background:#1e2a3a; color:#c8d6e5;")
        self._payslip_data = payslip_data
        self._emp_data     = emp_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        layout.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background:#ffffff; color:#000000;")
        scroll.setWidget(content)

        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(8)

        def lbl(text, size=12, bold=False, color="#000000", align=Qt.AlignLeft):
            l = QLabel(text)
            f = QFont()
            f.setPointSize(size)
            f.setBold(bold)
            l.setFont(f)
            l.setStyleSheet(f"color:{color};")
            l.setAlignment(align)
            return l

        cl.addWidget(lbl("💼  PAYROLL SYSTEM", 18, True, "#1e3a5f", Qt.AlignCenter))
        cl.addWidget(lbl("PAY SLIP", 14, True, "#1e3a5f", Qt.AlignCenter))
        cl.addWidget(lbl(f"For the month of {payslip_data['month']}/{payslip_data['year']}", 11, False, "#444", Qt.AlignCenter))

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color:#cccccc;"); cl.addWidget(sep)

        # Employee info
        cl.addWidget(lbl("EMPLOYEE INFORMATION", 11, True, "#333"))
        cl.addWidget(lbl(f"Employee ID : {emp_data['emp_id']}"))
        cl.addWidget(lbl(f"Name        : {emp_data['first_name']} {emp_data['last_name']}"))
        cl.addWidget(lbl(f"Department  : {emp_data.get('department','')}"))
        cl.addWidget(lbl(f"Position    : {emp_data.get('position','')}"))

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine); sep2.setStyleSheet("color:#cccccc;"); cl.addWidget(sep2)

        # Earnings
        cl.addWidget(lbl("EARNINGS", 11, True, "#333"))
        cl.addWidget(lbl(f"Basic Salary  : ₱{payslip_data['basic_salary']:>12,.2f}"))
        cl.addWidget(lbl(f"Allowances    : ₱{payslip_data['allowances']:>12,.2f}"))
        cl.addWidget(lbl(f"Gross Pay     : ₱{(payslip_data['basic_salary']+payslip_data['allowances']):>12,.2f}", bold=True))

        sep3 = QFrame(); sep3.setFrameShape(QFrame.HLine); sep3.setStyleSheet("color:#cccccc;"); cl.addWidget(sep3)

        # Deductions
        cl.addWidget(lbl("DEDUCTIONS", 11, True, "#333"))
        cl.addWidget(lbl(f"Deductions    : ₱{payslip_data['deductions']:>12,.2f}"))
        cl.addWidget(lbl(f"Tax           : ₱{payslip_data['tax_amount']:>12,.2f}"))
        cl.addWidget(lbl(f"Total Deductions: ₱{(payslip_data['deductions']+payslip_data['tax_amount']):>10,.2f}", bold=True))

        sep4 = QFrame(); sep4.setFrameShape(QFrame.HLine); sep4.setStyleSheet("color:#1e3a5f;"); cl.addWidget(sep4)

        cl.addWidget(lbl(f"NET PAY  :  ₱{payslip_data['net_pay']:,.2f}", 16, True, "#1e3a5f"))

        sep5 = QFrame(); sep5.setFrameShape(QFrame.HLine); sep5.setStyleSheet("color:#cccccc;"); cl.addWidget(sep5)
        cl.addWidget(lbl(f"Generated on: {payslip_data['generated_on']}", 9, False, "#888"))
        cl.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(16, 8, 16, 12)
        btn_row.setSpacing(10)

        btn_save = QPushButton("💾  Save as PDF")
        btn_save.setFixedHeight(38)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton{background:#2ecc71;color:#fff;border:none;
            border-radius:6px;padding:8px 20px;font-size:13px;font-weight:bold;}
            QPushButton:hover{background:#27ae60;}
        """)
        btn_save.clicked.connect(self._save_pdf)

        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(38)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
            border-radius:6px;padding:8px 20px;font-size:13px;font-weight:bold;}
            QPushButton:hover{background:#3a4f66;color:#fff;}
        """)
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _save_pdf(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtWidgets import QFileDialog
        p  = self._payslip_data
        e  = self._emp_data
        name = f"{e['first_name']}_{e['last_name']}_{p['month']}-{p['year']}"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Payslip as PDF", f"Payslip_{name}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPrinter.A4)

        from PyQt5.QtGui import QPainter, QFont as QF, QColor as QC
        from PyQt5.QtCore import QRectF
        painter = QPainter(printer)
        painter.begin(printer)

        pw = printer.pageRect().width()
        y  = 80

        def draw(text, size=28, bold=False, color="#000000", center=False):
            nonlocal y
            f = QF(); f.setPointSize(size); f.setBold(bold)
            painter.setFont(f)
            painter.setPen(QC(color))
            flags = Qt.AlignCenter if center else Qt.AlignLeft
            rect  = QRectF(80, y, pw - 160, size * 6)
            painter.drawText(rect, flags, text)
            y += size * 5

        def hline(color="#cccccc"):
            nonlocal y
            painter.setPen(QC(color))
            painter.drawLine(80, y, pw - 80, y)
            y += 30

        draw("PAYROLL SYSTEM", 36, True, "#1e3a5f", center=True)
        draw("PAY SLIP", 28, True, "#1e3a5f", center=True)
        draw(f"For the month of {p['month']}/{p['year']}", 22, False, "#444444", center=True)
        y += 20; hline()

        draw("EMPLOYEE INFORMATION", 22, True, "#333333")
        draw(f"Employee ID : {e['emp_id']}", 22)
        draw(f"Name        : {e['first_name']} {e['last_name']}", 22)
        draw(f"Department  : {e.get('department','')}", 22)
        draw(f"Position    : {e.get('position','')}", 22)
        y += 10; hline()

        draw("EARNINGS", 22, True, "#333333")
        draw(f"Basic Salary  :  P{p['basic_salary']:>12,.2f}", 22)
        draw(f"Allowances    :  P{p['allowances']:>12,.2f}", 22)
        draw(f"Gross Pay     :  P{(p['basic_salary']+p['allowances']):>12,.2f}", 22, True)
        y += 10; hline()

        draw("DEDUCTIONS", 22, True, "#333333")
        draw(f"Deductions    :  P{p['deductions']:>12,.2f}", 22)
        draw(f"Tax           :  P{p['tax_amount']:>12,.2f}", 22)
        draw(f"Total Deduct  :  P{(p['deductions']+p['tax_amount']):>12,.2f}", 22, True)
        y += 10; hline("#1e3a5f")

        draw(f"NET PAY  :  P{p['net_pay']:,.2f}", 32, True, "#1e3a5f")
        y += 10; hline()
        draw(f"Generated on: {p['generated_on']}", 18, False, "#888888")

        painter.end()

        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Saved", f"✅  Payslip saved to:\n{path}")


class PayslipGenerator(QWidget):
    def __init__(self, emp_id=None, parent=None):
        super().__init__(parent)
        self.fixed_emp_id = emp_id
        self._build_ui()
        self.load_payslips()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr   = QHBoxLayout()
        title = QLabel("🧾 Payslip Generator")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#fff;")
        hdr.addWidget(title)
        hdr.addStretch()

        if not self.fixed_emp_id:
            self.cmbEmp = QComboBox()
            self.cmbEmp.setFixedWidth(180)
            self.cmbEmp.setStyleSheet("background:#253447;border:1px solid #3a4f66;border-radius:6px;padding:6px;color:#fff;")
            self.load_employees_combo()
            hdr.addWidget(QLabel("Employee:"))
            hdr.addWidget(self.cmbEmp)

        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        self.cmbMonth = QComboBox()
        self.cmbMonth.addItems(months)
        self.cmbMonth.setCurrentIndex(datetime.date.today().month - 1)
        self.cmbMonth.setStyleSheet("background:#253447;border:1px solid #3a4f66;border-radius:6px;padding:6px;color:#fff;")
        hdr.addWidget(QLabel("Month:"))
        hdr.addWidget(self.cmbMonth)

        self.cmbYear = QComboBox()
        cur_yr = datetime.date.today().year
        self.cmbYear.addItems([str(y) for y in range(cur_yr - 3, cur_yr + 2)])
        self.cmbYear.setCurrentText(str(cur_yr))
        self.cmbYear.setStyleSheet("background:#253447;border:1px solid #3a4f66;border-radius:6px;padding:6px;color:#fff;")
        hdr.addWidget(QLabel("Year:"))
        hdr.addWidget(self.cmbYear)

        btn_gen = QPushButton("⚡ Generate")
        btn_gen.setStyleSheet("background:#4a9eff;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;")
        btn_gen.clicked.connect(self.generate_payslip)
        hdr.addWidget(btn_gen)
        layout.addLayout(hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Emp ID", "Month/Year", "Gross", "Deductions", "Tax", "Net Pay", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("background:#253447;border:none;border-radius:8px;color:#c8d6e5;alternate-background-color:#1e2a3a;")
        self.table.horizontalHeader().setStyleSheet("background:#1e2a3a;color:#8a9bb0;")
        layout.addWidget(self.table)

    def load_employees_combo(self):
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emp_id, first_name||' '||last_name FROM employees WHERE status='Active'")
        rows = cursor.fetchall()
        conn.close()
        self.cmbEmp.clear()
        for r in rows:
            self.cmbEmp.addItem(f"{r[0]} – {r[1]}", r[0])

    def load_payslips(self):
        conn   = get_connection()
        cursor = conn.cursor()
        if self.fixed_emp_id:
            cursor.execute("SELECT emp_id,month,year,basic_salary+allowances,deductions,tax_amount,net_pay,id FROM payslips WHERE emp_id=? ORDER BY id DESC", (self.fixed_emp_id,))
        else:
            cursor.execute("SELECT emp_id,month,year,basic_salary+allowances,deductions,tax_amount,net_pay,id FROM payslips ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [row_data[0], f"{row_data[1]}/{row_data[2]}",
                    f"₱{row_data[3]:,.2f}", f"₱{row_data[4]:,.2f}",
                    f"₱{row_data[5]:,.2f}", f"₱{row_data[6]:,.2f}"]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            ps_id  = row_data[7]
            emp_id = row_data[0]
            cell   = QWidget()
            h      = QHBoxLayout(cell)
            h.setContentsMargins(4,2,4,2)
            btn_view = QPushButton("👁 View")
            btn_view.setFixedHeight(30)
            btn_view.setStyleSheet("""
                QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
                border-radius:5px;font-size:12px;padding:0 12px;}
                QPushButton:hover{background:#4a9eff;color:#fff;}
            """)
            btn_view.clicked.connect(lambda _, pid=ps_id, eid=emp_id: self.view_payslip(pid, eid))
            h.addWidget(btn_view)
            self.table.setCellWidget(row, 6, cell)

    def generate_payslip(self):
        month_name = self.cmbMonth.currentText()
        month_num  = str(self.cmbMonth.currentIndex() + 1).zfill(2)
        year       = self.cmbYear.currentText()

        emp_id = self.fixed_emp_id if self.fixed_emp_id else self.cmbEmp.currentData()
        if not emp_id:
            QMessageBox.warning(self, "Warning", "Please select an employee.")
            return
        if not confirm(self, "Generate Payslip",
                f"Generate payslip for {emp_id}\nPeriod: {month_name} {year}?",
                confirm_text="✔  Generate", confirm_color="#2ecc71", icon="📄"):
            return

        conn   = get_connection()
        cursor = conn.cursor()

        # Check duplicate
        cursor.execute("SELECT id FROM payslips WHERE emp_id=? AND month=? AND year=?", (emp_id, month_num, year))
        if cursor.fetchone():
            conn.close()
            QMessageBox.warning(self, "Duplicate", f"Payslip for {month_name} {year} already exists.")
            return

        # Get salary
        cursor.execute("SELECT * FROM salary WHERE emp_id=? ORDER BY id DESC LIMIT 1", (emp_id,))
        sal = cursor.fetchone()
        if not sal:
            conn.close()
            QMessageBox.warning(self, "No Salary", "No salary record found for this employee.")
            return

        basic      = sal["basic_salary"]
        allowances = sal["allowances"]
        deductions = sal["deductions"]
        tax_rate   = sal["tax_rate"] / 100
        gross      = basic + allowances
        tax_amount = gross * tax_rate
        net_pay    = gross - tax_amount - deductions

        cursor.execute("""
            INSERT INTO payslips (emp_id,month,year,basic_salary,allowances,deductions,tax_amount,net_pay,generated_on)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (emp_id, month_num, year, basic, allowances, deductions, tax_amount, net_pay,
              datetime.date.today().isoformat()))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", f"Payslip generated! Net Pay: ₱{net_pay:,.2f}")
        self.load_payslips()

    def view_payslip(self, ps_id, emp_id):
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payslips WHERE id=?", (ps_id,))
        ps = dict(cursor.fetchone())
        cursor.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,))
        emp = dict(cursor.fetchone())
        conn.close()
        dlg = PayslipPreviewDialog(ps, emp, parent=self)
        dlg.exec_()