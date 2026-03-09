from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QButtonGroup, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from database import get_connection
from confirm_dialog import confirm


class EmployeeDashboard(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi("ui/employee_dashboard.ui", self)
        self.user   = user
        self.emp_id = user.get("emp_id")
        self.lblUser.setText(f"👤 {user['username'].title()}")

        # Nav
        self.navGroup = QButtonGroup(self)
        self.navGroup.setExclusive(True)
        for btn in [self.btnNavHome, self.btnNavPayslip, self.btnNavLeave]:
            self.navGroup.addButton(btn)

        self.btnNavHome.clicked.connect(lambda: self.switch_page(0))
        self.btnNavPayslip.clicked.connect(lambda: self.switch_page(1))
        self.btnNavLeave.clicked.connect(lambda: self.switch_page(2))
        self.btnLogout.clicked.connect(self.logout)

        self.load_home()
        self.load_sub_pages()
        self.showMaximized()

    def load_home(self):
        if not self.emp_id:
            return

        conn   = get_connection()
        cursor = conn.cursor()

        # Employee info
        cursor.execute("SELECT * FROM employees WHERE emp_id=?", (self.emp_id,))
        emp = cursor.fetchone()

        # Salary
        cursor.execute("SELECT * FROM salary WHERE emp_id=? ORDER BY id DESC LIMIT 1", (self.emp_id,))
        sal = cursor.fetchone()

        # Latest payslip net
        cursor.execute("SELECT net_pay FROM payslips WHERE emp_id=? ORDER BY id DESC LIMIT 1", (self.emp_id,))
        ps = cursor.fetchone()

        # Pending leaves
        cursor.execute("SELECT COUNT(*) FROM leave_requests WHERE emp_id=? AND status='Pending'", (self.emp_id,))
        pending = cursor.fetchone()[0]

        conn.close()

        name = f"{emp['first_name']} {emp['last_name']}" if emp else self.user['username'].title()
        self.lblWelcome.setText(f"Welcome back, {name}! 👋")

        if sal:
            self.lblBasic.setText(f"₱{sal['basic_salary']:,.2f}")
        if ps:
            self.lblNet.setText(f"₱{ps[0]:,.2f}")
        self.lblLeave.setText(str(pending))

        # Info cards
        if emp:
            layout = self.infoForm
            fields = [
                ("Employee ID",  emp["emp_id"]),
                ("Department",   emp["department"] or "—"),
                ("Position",     emp["position"]   or "—"),
                ("Email",        emp["email"]       or "—"),
                ("Phone",        emp["phone"]       or "—"),
                ("Hire Date",    emp["hire_date"]   or "—"),
                ("Status",       emp["status"]      or "—"),
            ]
            for lbl_text, val_text in fields:
                lbl = QLabel(lbl_text)
                lbl.setStyleSheet("color:#8a9bb0;")
                val = QLabel(val_text)
                val.setStyleSheet("color:#ffffff;font-weight:bold;")
                layout.addRow(lbl, val)

    def load_sub_pages(self):
        from payslip_generator import PayslipGenerator
        from leave_page        import LeavePage

        self.payslipWidget = PayslipGenerator(emp_id=self.emp_id)
        self.leaveWidget   = LeavePage(is_admin=False, emp_id=self.emp_id)

        self._inject(self.pagePayslip, self.payslipWidget)
        self._inject(self.pageLeave,   self.leaveWidget)

    def _inject(self, page, widget):
        if page.layout() is None:
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 0, 0, 0)
        page.layout().addWidget(widget)

    def switch_page(self, index):
        self.stackedWidget.setCurrentIndex(index)

    def logout(self):
        if not confirm(self, "Logout", "Are you sure you want to logout?",
                confirm_text="Logout", confirm_color="#e74c3c", icon="🚪"):
            return
        from login import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()