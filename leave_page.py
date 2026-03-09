import os
import shutil
import datetime

from PyQt5.QtWidgets import (
    QWidget, QDialog, QTableWidgetItem, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QHeaderView, QTableWidget, QFileDialog,
    QFrame, QScrollArea, QComboBox, QDateEdit, QTextEdit, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont, QPixmap

from database import get_connection
from confirm_dialog import confirm

# Resolve attachments folder relative to THIS file, works from any cwd
_HERE      = os.path.dirname(os.path.abspath(__file__))
_BASE      = _HERE if os.path.basename(_HERE) != "py" else os.path.dirname(_HERE)
ATTACH_DIR = os.path.join(_BASE, "attachments")
os.makedirs(ATTACH_DIR, exist_ok=True)


def _ensure_attachment_column():
    conn = get_connection()
    try:
        conn.execute("ALTER TABLE leave_requests ADD COLUMN attachment_path TEXT")
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

_ensure_attachment_column()


def _bold(size=12):
    f = QFont()
    f.setBold(True)
    f.setPointSize(size)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Leave Review Dialog (admin)
# ─────────────────────────────────────────────────────────────────────────────
class LeaveReviewDialog(QDialog):
    def __init__(self, leave_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Leave Request Review")
        self.setMinimumSize(540, 580)
        self.setStyleSheet("background:#1e2a3a; color:#c8d6e5;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        title = QLabel("🗓  Leave Request Details")
        title.setFont(_bold(17))
        title.setStyleSheet("color:#ffffff;")
        layout.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#2a3d55;")
        layout.addWidget(sep)

        # Info grid
        grid  = QHBoxLayout()
        left  = QVBoxLayout(); left.setSpacing(10)
        right = QVBoxLayout(); right.setSpacing(10)

        def info_row(label, value, color="#ffffff"):
            box = QVBoxLayout(); box.setSpacing(2)
            l = QLabel(label)
            l.setStyleSheet("color:#8a9bb0;font-size:11px;")
            v = QLabel(str(value))
            v.setStyleSheet(f"color:{color};font-size:13px;font-weight:bold;")
            v.setWordWrap(True)
            box.addWidget(l); box.addWidget(v)
            return box

        sc = {"Pending":"#f39c12","Approved":"#2ecc71","Rejected":"#e74c3c"}.get(
             leave_data.get("status",""), "#c8d6e5")

        left.addLayout(info_row("Employee",    leave_data.get("emp_name", leave_data.get("emp_id",""))))
        left.addLayout(info_row("Leave Type",  leave_data.get("leave_type","")))
        left.addLayout(info_row("Start Date",  leave_data.get("start_date","")))
        left.addLayout(info_row("End Date",    leave_data.get("end_date","")))
        left.addLayout(info_row("Days",        leave_data.get("days","")))
        right.addLayout(info_row("Status",     leave_data.get("status",""), sc))
        right.addLayout(info_row("Applied On", leave_data.get("applied_on","")))
        right.addStretch()

        grid.addLayout(left); grid.addSpacing(24); grid.addLayout(right)
        layout.addLayout(grid)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color:#2a3d55;")
        layout.addWidget(sep2)

        # Reason (scrollable)
        lbl_r = QLabel("Reason")
        lbl_r.setStyleSheet("color:#8a9bb0;font-size:11px;")
        layout.addWidget(lbl_r)

        reason_lbl = QLabel(leave_data.get("reason","—") or "—")
        reason_lbl.setWordWrap(True)
        reason_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        reason_lbl.setStyleSheet("background:#253447;color:#ffffff;font-size:13px;padding:12px;")

        reason_scroll = QScrollArea()
        reason_scroll.setWidgetResizable(True)
        reason_scroll.setFixedHeight(120)
        reason_scroll.setStyleSheet("""
            QScrollArea { border:1px solid #2a3d55; border-radius:6px; background:#253447; }
            QScrollBar:vertical { background:#1e2a3a; width:8px; border-radius:4px; }
            QScrollBar::handle:vertical { background:#3a4f66; border-radius:4px; min-height:20px; }
            QScrollBar::handle:vertical:hover { background:#4a9eff; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)
        reason_scroll.setWidget(reason_lbl)
        layout.addWidget(reason_scroll)

        # Attachment
        attach_path = leave_data.get("attachment_path","")
        if attach_path and os.path.exists(attach_path):
            sep3 = QFrame(); sep3.setFrameShape(QFrame.HLine)
            sep3.setStyleSheet("color:#2a3d55;")
            layout.addWidget(sep3)

            lbl_a = QLabel("📎  Attachment")
            lbl_a.setStyleSheet("color:#8a9bb0;font-size:11px;")
            layout.addWidget(lbl_a)

            ext = os.path.splitext(attach_path)[1].lower()
            if ext in (".png",".jpg",".jpeg",".bmp",".gif",".webp"):
                pix = QPixmap(attach_path)
                if not pix.isNull():
                    img_lbl = QLabel()
                    img_lbl.setPixmap(pix.scaledToWidth(460, Qt.SmoothTransformation))
                    img_lbl.setAlignment(Qt.AlignCenter)
                    img_lbl.setStyleSheet("border:1px solid #2a3d55;border-radius:6px;padding:4px;")
                    img_scroll = QScrollArea()
                    img_scroll.setWidgetResizable(True)
                    img_scroll.setMaximumHeight(220)
                    img_scroll.setStyleSheet("border:none;background:#1e2a3a;")
                    img_scroll.setWidget(img_lbl)
                    layout.addWidget(img_scroll)
            else:
                btn_open = QPushButton(f"📄  Open: {os.path.basename(attach_path)}")
                btn_open.setStyleSheet("""
                    background:#253447;color:#4a9eff;border:1px solid #3a4f66;
                    border-radius:6px;padding:8px 14px;font-size:12px;
                """)
                btn_open.clicked.connect(
                    lambda: os.system(f'xdg-open "{attach_path}"'))
                layout.addWidget(btn_open)
        else:
            lbl_no = QLabel("No attachment provided.")
            lbl_no.setStyleSheet("color:#5a6f88;font-size:12px;font-style:italic;")
            layout.addWidget(lbl_no)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("""
            QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
            border-radius:6px;padding:9px 20px;font-size:13px;}
            QPushButton:hover{background:#3a4f66;}
        """)
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)

        if leave_data.get("status") == "Pending" and leave_data.get("is_admin"):
            btn_approve = QPushButton("✔  Approve")
            btn_approve.setStyleSheet("""
                QPushButton{background:#2ecc71;color:#fff;border:none;
                border-radius:6px;padding:9px 20px;font-weight:bold;font-size:13px;}
                QPushButton:hover{background:#27ae60;}
            """)
            btn_approve.clicked.connect(lambda: self.done(2))

            btn_reject = QPushButton("✖  Reject")
            btn_reject.setStyleSheet("""
                QPushButton{background:#e74c3c;color:#fff;border:none;
                border-radius:6px;padding:9px 20px;font-weight:bold;font-size:13px;}
                QPushButton:hover{background:#c0392b;}
            """)
            btn_reject.clicked.connect(lambda: self.done(3))

            btn_row.addWidget(btn_approve)
            btn_row.addWidget(btn_reject)

        layout.addLayout(btn_row)


# ─────────────────────────────────────────────────────────────────────────────
# Leave Apply Dialog (employee) — 100% programmatic, no .ui file
# ─────────────────────────────────────────────────────────────────────────────
class LeaveDialog(QDialog):
    def __init__(self, emp_id, parent=None):
        super().__init__(parent)
        self.emp_id       = emp_id
        self._attach_path = None

        self.setWindowTitle("Apply for Leave")
        self.setFixedSize(520, 530)
        self.setStyleSheet("""
            QDialog   { background:#1e2a3a; }
            QLabel    { color:#c8d6e5; font-size:13px; }
            QComboBox, QDateEdit, QTextEdit {
                background:#253447; border:1px solid #3a4f66;
                border-radius:6px; padding:7px 10px;
                color:#ffffff; font-size:13px;
            }
            QComboBox:focus, QDateEdit:focus, QTextEdit:focus { border-color:#4a9eff; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#253447; color:#fff;
                selection-background-color:#4a9eff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        # Title
        title = QLabel("🗓  Apply for Leave")
        title.setStyleSheet("color:#ffffff;font-size:17px;font-weight:bold;")
        layout.addWidget(title)

        # Form
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft)

        self.cmbLeaveType = QComboBox()
        self.cmbLeaveType.addItems([
            "Vacation Leave", "Sick Leave", "Emergency Leave",
            "Maternity/Paternity Leave", "Other"
        ])

        self.dtStart = QDateEdit()
        self.dtStart.setCalendarPopup(True)
        self.dtStart.setDisplayFormat("yyyy-MM-dd")
        self.dtStart.setDate(QDate.currentDate())

        self.dtEnd = QDateEdit()
        self.dtEnd.setCalendarPopup(True)
        self.dtEnd.setDisplayFormat("yyyy-MM-dd")
        self.dtEnd.setDate(QDate.currentDate())

        self.txtReason = QTextEdit()
        self.txtReason.setMaximumHeight(80)
        self.txtReason.setPlaceholderText("Enter reason for leave…")

        form.addRow(QLabel("Leave Type"), self.cmbLeaveType)
        form.addRow(QLabel("Start Date"), self.dtStart)
        form.addRow(QLabel("End Date"),   self.dtEnd)
        form.addRow(QLabel("Reason"),     self.txtReason)
        layout.addLayout(form)

        # Attachment box
        attach_frame = QFrame()
        attach_frame.setStyleSheet("""
            QFrame {
                background:#1a2535;
                border:1px dashed #3a4f66;
                border-radius:8px;
            }
        """)
        af = QVBoxLayout(attach_frame)
        af.setContentsMargins(12, 10, 12, 10)
        af.setSpacing(6)

        top_row = QHBoxLayout()
        lbl_attach = QLabel("📎  Proof / Attachment")
        lbl_attach.setStyleSheet("color:#c8d6e5;font-size:13px;background:transparent;border:none;")
        lbl_opt = QLabel("(optional)")
        lbl_opt.setStyleSheet("color:#5a6f88;font-size:11px;background:transparent;border:none;")

        self.btnAttach = QPushButton("📂  Browse File")
        self.btnAttach.setStyleSheet("""
            QPushButton {
                background:#2a3d55; color:#8a9bb0;
                border:none; border-radius:6px;
                font-size:12px; padding:6px 12px;
            }
            QPushButton:hover { background:#3a4f66; color:#fff; }
        """)
        self.btnAttach.clicked.connect(self._browse_file)

        top_row.addWidget(lbl_attach)
        top_row.addWidget(lbl_opt)
        top_row.addStretch()
        top_row.addWidget(self.btnAttach)
        af.addLayout(top_row)

        self.lblFileName = QLabel("No file selected")
        self.lblFileName.setStyleSheet("color:#5a6f88;font-size:11px;background:transparent;border:none;")
        af.addWidget(self.lblFileName)
        layout.addWidget(attach_frame)

        # Error label
        self.errorLabel = QLabel("")
        self.errorLabel.setStyleSheet("color:#ff5f5f;font-size:12px;")
        layout.addWidget(self.errorLabel)

        # Buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
            border-radius:6px;font-size:13px;padding:10px;}
            QPushButton:hover{background:#3a4f66;}
        """)
        btn_cancel.clicked.connect(self.reject)

        self.btnSubmit = QPushButton("Submit Request")
        self.btnSubmit.setStyleSheet("""
            QPushButton{background:#4a9eff;color:#fff;border:none;
            border-radius:6px;font-size:14px;font-weight:bold;padding:10px;}
            QPushButton:hover{background:#3a8ef0;}
        """)
        self.btnSubmit.clicked.connect(self.submit)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btnSubmit)
        layout.addLayout(btn_row)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Proof / Attachment", "",
            "Images & Documents (*.png *.jpg *.jpeg *.pdf *.docx *.doc *.bmp *.gif)"
        )
        if path:
            self._attach_path = path
            self.lblFileName.setText(f"📄  {os.path.basename(path)}")
            self.lblFileName.setStyleSheet(
                "color:#4a9eff;font-size:11px;background:transparent;border:none;")
        else:
            self._attach_path = None
            self.lblFileName.setText("No file selected")
            self.lblFileName.setStyleSheet(
                "color:#5a6f88;font-size:11px;background:transparent;border:none;")

    def submit(self):
        start = self.dtStart.date().toString("yyyy-MM-dd")
        end   = self.dtEnd.date().toString("yyyy-MM-dd")
        if start > end:
            self.errorLabel.setText("End date must be after start date.")
            return
        if not confirm(self, "Submit Leave Request",
                f"Submit {self.cmbLeaveType.currentText()}\nfrom {start} to {end}?",
                confirm_text="✔  Submit", confirm_color="#4a9eff", icon="🗓"):
            return

        saved_path = None
        if self._attach_path and os.path.exists(self._attach_path):
            ext      = os.path.splitext(self._attach_path)[1]
            filename = (f"{self.emp_id}_{datetime.date.today()}_"
                        f"{datetime.datetime.now().strftime('%H%M%S')}{ext}")
            dest = os.path.join(ATTACH_DIR, filename)
            shutil.copy2(self._attach_path, dest)
            saved_path = dest

        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO leave_requests
                    (emp_id, leave_type, start_date, end_date, reason,
                     status, applied_on, attachment_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.emp_id, self.cmbLeaveType.currentText(),
                  start, end, self.txtReason.toPlainText().strip(),
                  "Pending", datetime.date.today().isoformat(), saved_path))
            conn.commit()
            self.accept()
        except Exception as e:
            self.errorLabel.setText(str(e))
        finally:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Main Leave Page
# ─────────────────────────────────────────────────────────────────────────────
class LeavePage(QWidget):
    def __init__(self, is_admin=False, emp_id=None, parent=None):
        super().__init__(parent)
        self.is_admin = is_admin
        self.emp_id   = emp_id
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr   = QHBoxLayout()
        title = QLabel("🗓 Leave Management")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#fff;")
        hdr.addWidget(title)
        hdr.addStretch()

        if not self.is_admin and self.emp_id:
            btn = QPushButton("+ Apply for Leave")
            btn.setStyleSheet("""
                background:#4a9eff;color:#fff;border:none;
                border-radius:6px;padding:8px 16px;font-weight:bold;
            """)
            btn.clicked.connect(self.apply_leave)
            hdr.addWidget(btn)
        layout.addLayout(hdr)

        cols = ["ID", "Employee", "Type", "Start", "End", "Days", "Status", "Actions"]
        self.table = QTableWidget()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)   # Type stretches
        hh.setSectionResizeMode(1, QHeaderView.Fixed)     # Employee fixed
        hh.setSectionResizeMode(7, QHeaderView.Fixed)     # Actions fixed
        self.table.setColumnWidth(1, 130)                 # Employee name
        self.table.setColumnWidth(7, 155)                 # Actions — enough for "🔍 View Details"
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setStyleSheet("""
            QTableWidget {
                background:#253447; border:none; border-radius:8px;
                color:#c8d6e5; alternate-background-color:#1e2a3a;
                gridline-color:#2a3d55;
            }
            QTableWidget::item { padding:6px 4px; }
            QTableWidget::item:selected { background:#4a9eff30; color:#fff; }
        """)
        hh.setStyleSheet("background:#1e2a3a;color:#8a9bb0;padding:4px;")
        layout.addWidget(self.table)

    def load_data(self):
        conn   = get_connection()
        cursor = conn.cursor()
        if self.is_admin:
            cursor.execute("""
                SELECT lr.id, lr.emp_id,
                       COALESCE(e.first_name||' '||e.last_name, lr.emp_id),
                       lr.leave_type, lr.start_date, lr.end_date,
                       lr.reason, lr.status, lr.applied_on,
                       COALESCE(lr.attachment_path,'')
                FROM leave_requests lr
                LEFT JOIN employees e ON lr.emp_id = e.emp_id
                ORDER BY lr.id DESC
            """)
        else:
            cursor.execute("""
                SELECT lr.id, lr.emp_id, lr.emp_id,
                       lr.leave_type, lr.start_date, lr.end_date,
                       lr.reason, lr.status, lr.applied_on,
                       COALESCE(lr.attachment_path,'')
                FROM leave_requests lr
                WHERE lr.emp_id = ?
                ORDER BY lr.id DESC
            """, (self.emp_id,))
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        status_colors = {
            "Pending":  QColor("#f39c12"),
            "Approved": QColor("#2ecc71"),
            "Rejected": QColor("#e74c3c"),
        }

        for row_data in rows:
            row      = self.table.rowCount()
            self.table.insertRow(row)

            leave_id   = row_data[0]
            emp_id     = row_data[1]
            emp_name   = row_data[2]
            leave_type = row_data[3]
            start      = row_data[4]
            end        = row_data[5]
            reason     = row_data[6] or ""
            status     = row_data[7]
            applied_on = row_data[8] or ""
            attach     = row_data[9]

            try:
                days = str((datetime.date.fromisoformat(end) -
                            datetime.date.fromisoformat(start)).days + 1)
            except Exception:
                days = "-"

            for col, val in enumerate([str(leave_id), emp_name, leave_type,
                                        start, end, days, status]):
                item = QTableWidgetItem(val or "")
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor("#c8d6e5"))
                if col == 6 and val in status_colors:
                    item.setForeground(status_colors[val])
                    item.setFont(_bold(12))
                self.table.setItem(row, col, item)

            # View button
            cell = QWidget()
            h    = QHBoxLayout(cell)
            h.setContentsMargins(6, 4, 6, 4)

            btn_view = QPushButton("🔍 View Details")
            btn_view.setFixedHeight(30)
            btn_view.setStyleSheet("""
                QPushButton{background:#2a3d55;color:#c8d6e5;border:none;
                border-radius:5px;font-size:12px;padding:0 12px;}
                QPushButton:hover{background:#4a9eff;color:#fff;}
            """)
            leave_info = {
                "id": leave_id, "emp_id": emp_id, "emp_name": emp_name,
                "leave_type": leave_type, "start_date": start, "end_date": end,
                "days": days, "reason": reason, "status": status,
                "applied_on": applied_on, "attachment_path": attach,
                "is_admin": self.is_admin,
            }
            btn_view.clicked.connect(lambda _, li=leave_info: self._open_review(li))
            h.addWidget(btn_view)
            self.table.setCellWidget(row, 7, cell)

    def _open_review(self, leave_info):
        dlg    = LeaveReviewDialog(leave_info, parent=self)
        result = dlg.exec_()
        if result == 2:
            self.update_status(leave_info["id"], "Approved")
        elif result == 3:
            self.update_status(leave_info["id"], "Rejected")

    def update_status(self, leave_id, status):
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE leave_requests SET status=? WHERE id=?", (status, leave_id))
        conn.commit()
        conn.close()
        self.load_data()

    def apply_leave(self):
        dlg = LeaveDialog(self.emp_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.load_data()