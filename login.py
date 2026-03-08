import sys
from PyQt5 import uic
from PyQt5.QtWidgets import (QMainWindow, QApplication, QPushButton,
                              QLineEdit, QSizePolicy)
from PyQt5.QtCore import Qt
from database import get_connection, initialize_db


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/login.ui", self)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.btnLogin.clicked.connect(self.handle_login)
        self.txtPassword.returnPressed.connect(self.handle_login)
        self._pwd_visible = False
        self._add_eye_button()

    def _add_eye_button(self):
        """Overlay a visible eye button inside the password field."""
        self.eyeBtn = QPushButton("👁", self.txtPassword)
        self.eyeBtn.setFixedSize(28, 28)
        self.eyeBtn.setCursor(Qt.PointingHandCursor)
        self.eyeBtn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8a9bb0;
                font-size: 16px;
                padding: 0;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        self.eyeBtn.clicked.connect(self._toggle_password)

        # Add right padding to the field so text doesn't overlap the button
        self.txtPassword.setStyleSheet(
            self.txtPassword.styleSheet() + "padding-right: 34px;"
        )

        # Position the eye button — will be repositioned on resize
        self._reposition_eye()

    def _reposition_eye(self):
        fw = self.txtPassword.width()
        fh = self.txtPassword.height()
        bw = self.eyeBtn.width()
        bh = self.eyeBtn.height()
        self.eyeBtn.move(fw - bw - 6, (fh - bh) // 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_eye()

    def showEvent(self, event):
        super().showEvent(event)
        self._reposition_eye()

    def _toggle_password(self):
        self._pwd_visible = not self._pwd_visible
        if self._pwd_visible:
            self.txtPassword.setEchoMode(QLineEdit.Normal)
            self.eyeBtn.setText("⌣")
        else:
            self.txtPassword.setEchoMode(QLineEdit.Password)
            self.eyeBtn.setText("👁")

    def handle_login(self):
        username = self.txtUsername.text().strip()
        password = self.txtPassword.text().strip()
        role     = self.cmbRole.currentText().lower()

        if not username or not password:
            self.errorLabel.setText("Please fill in all fields.")
            return

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role=?",
            (username, password, role)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            self.errorLabel.setText("")
            self.open_dashboard(role, dict(user))
        else:
            self.errorLabel.setText("Invalid credentials. Please try again.")
            self.txtPassword.clear()

    def open_dashboard(self, role, user):
        if role == "admin":
            from admin_dashboard import AdminDashboard
            self.dashboard = AdminDashboard(user)
        else:
            from employee_dashboard import EmployeeDashboard
            self.dashboard = EmployeeDashboard(user)
        self.dashboard.show()
        self.close()


if __name__ == "__main__":
    initialize_db()
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())