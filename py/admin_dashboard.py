from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QButtonGroup, QTableWidgetItem, QVBoxLayout, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from py.database import get_connection
from py.confirm_dialog import confirm


class AdminDashboard(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi("ui/admin_dashboard.ui", self)
        self.user = user
        self.lblUser.setText(f"👤 {user['username'].title()}")

        self.navGroup = QButtonGroup(self)
        self.navGroup.setExclusive(True)
        for btn in [self.btnNavDash, self.btnNavEmp, self.btnNavSalary,
                    self.btnNavLeave, self.btnNavPayslip, self.btnNavReport]:
            self.navGroup.addButton(btn)

        self.btnNavDash.clicked.connect(lambda: self.switch_page(0))
        self.btnNavEmp.clicked.connect(lambda: self.switch_page(1))
        self.btnNavSalary.clicked.connect(lambda: self.switch_page(2))
        self.btnNavLeave.clicked.connect(lambda: self.switch_page(3))
        self.btnNavPayslip.clicked.connect(lambda: self.switch_page(4))
        self.btnNavReport.clicked.connect(lambda: self.switch_page(5))
        self.btnLogout.clicked.connect(self.logout)

        self.load_sub_pages()
        self.refresh_all()
        self.showMaximized()

    def load_sub_pages(self):
        from py.manage_employees  import ManageEmployees
        from py.manage_salary     import ManageSalary
        from py.leave_page        import LeavePage
        from py.payslip_generator import PayslipGenerator
        from py.salary_report     import SalaryReport

        self.empWidget     = ManageEmployees()
        self.salaryWidget  = ManageSalary()
        self.leaveWidget   = LeavePage(is_admin=True)
        self.payslipWidget = PayslipGenerator()
        self.reportWidget  = SalaryReport()

        self.empWidget.on_data_changed = self.refresh_all

        self._inject(self.pageEmp,     self.empWidget)
        self._inject(self.pageSalary,  self.salaryWidget)
        self._inject(self.pageLeave,   self.leaveWidget)
        self._inject(self.pagePayslip, self.payslipWidget)
        self._inject(self.pageReport,  self.reportWidget)

    def _inject(self, page, widget):
        if page.layout() is None:
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 0, 0, 0)
        page.layout().addWidget(widget)

    def switch_page(self, index):
        self.stackedWidget.setCurrentIndex(index)
        refresh_map = {
            0: self.refresh_dashboard,
            1: self.empWidget.load_employees,
            2: self.salaryWidget.load_data,
            3: self.leaveWidget.load_data,
            4: self.payslipWidget.load_payslips,
            5: self.reportWidget.load_report,
        }
        if index in refresh_map:
            refresh_map[index]()

    def refresh_all(self):
        self.refresh_dashboard()
        self.salaryWidget.load_data()
        self.payslipWidget.load_payslips()
        self.reportWidget.load_report()
        if hasattr(self.payslipWidget, 'load_employees_combo'):
            self.payslipWidget.load_employees_combo()

    def refresh_dashboard(self):
        self.load_dashboard_stats()
        self.load_recent_payslips()

    def load_dashboard_stats(self):
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM employees")
        self.valEmp.setText(str(cursor.fetchone()[0]))

        cursor.execute("SELECT COUNT(*) FROM employees WHERE status='Active'")
        self.valActive.setText(str(cursor.fetchone()[0]))

        cursor.execute("SELECT COUNT(*) FROM leave_requests WHERE status='Pending'")
        self.valLeave.setText(str(cursor.fetchone()[0]))

        cursor.execute("""
            SELECT SUM(net_pay) FROM payslips
            WHERE month = strftime('%m', date('now'))
            AND   year  = strftime('%Y', date('now'))
        """)
        total = cursor.fetchone()[0] or 0
        self.valPayroll.setText(f"₱{total:,.2f}")
        conn.close()

    def load_recent_payslips(self):
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.emp_id,
                   e.first_name || ' ' || e.last_name,
                   p.month || '/' || p.year,
                   p.net_pay,
                   p.generated_on
            FROM payslips p
            INNER JOIN employees e ON p.emp_id = e.emp_id
            ORDER BY p.id DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        conn.close()

        tbl = self.tblRecentPayslips
        tbl.setRowCount(0)
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels([
            "Emp ID", "Employee Name", "Period", "Net Pay", "Generated On"
        ])
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setStretchLastSection(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet("""
            QTableWidget {
                background: #253447;
                alternate-background-color: #1e2a3a;
                border: none;
                border-radius: 8px;
                gridline-color: #2a3d55;
                color: #c8d6e5;
            }
            QTableWidget::item {
                padding: 6px 4px;
                color: #c8d6e5;
            }
            QTableWidget::item:selected {
                background: #4a9eff30;
                color: #ffffff;
            }
            QHeaderView::section {
                background: #1e2a3a;
                color: #8a9bb0;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #2a3d55;
            }
        """)

        bg_even = QColor("#253447")
        bg_odd  = QColor("#1e2a3a")
        c_white = QColor("#c8d6e5")
        c_green = QColor("#2ecc71")

        for row_data in rows:
            row = tbl.rowCount()
            tbl.insertRow(row)
            bg = bg_even if row % 2 == 0 else bg_odd

            for col, val in enumerate(row_data):
                if col == 3:
                    text  = f"₱{val:,.2f}"
                    color = c_green
                else:
                    text  = str(val) if val is not None else ""
                    color = c_white

                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(color)
                item.setBackground(bg)
                tbl.setItem(row, col, item)

    def logout(self):
        if not confirm(self, "Logout", "Are you sure you want to logout?",
                confirm_text="Logout", confirm_color="#e74c3c", icon="🚪"):
            return
        from py.login import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()