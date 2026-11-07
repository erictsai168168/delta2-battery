"""
ROG Delta II 電量監看（2.4G）
深色、扁平的小視窗 + 系統匣圖示，自動讀取耳機電量。
"""
import math
import os
import sys
import tempfile
import time
from datetime import datetime

from PySide6.QtCore import (
    QLockFile,
    QPointF,
    QRect,
    QRectF,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from delta2_core import BatteryReader

APP_NAME = "ROG Delta II 電量"
QUERY_INTERVAL = 30.0   # 每幾秒主動查詢一次
OFFLINE_AFTER = 4.0     # 查詢後幾秒沒回應就視為耳機未連線
LOW_NOTIFY = 20         # 低於等於此值跳通知
LOW_RESET = 30          # 回升到此值以上才會再次通知

BG = "#141416"
BORDER = "#2A2A2F"
TRACK = "#26262B"
TEXT = "#EDEDEF"
MUTED = "#7C7C85"
DIM = "#4A4A50"
GREEN = "#3DDC84"
AMBER = "#FFB020"
RED = "#FF4D4F"


def level_color(pct):
    if pct <= 15:
        return RED
    if pct <= 30:
        return AMBER
    return GREEN


# ---------------------------------------------------------------- 背景讀取
class Monitor(QThread):
    battery = Signal(int)
    charging = Signal(bool)
    state = Signal(str)  # "online" / "offline" / "nodongle"

    def __init__(self):
        super().__init__()
        self._stop = False
        self._force = False

    def stop(self):
        self._stop = True

    def refresh(self):
        self._force = True

    def run(self):
        reader = BatteryReader()
        last_query = 0.0
        pending_since = None
        cur_state = None
        cur_charging = None

        def set_state(s):
            nonlocal cur_state
            if s != cur_state:
                cur_state = s
                self.state.emit(s)

        while not self._stop:
            now = time.monotonic()
            try:
                if not reader.is_open:
                    if not reader.open():
                        set_state("nodongle")
                        pending_since = None
                        self.msleep(2000)
                        continue
                    last_query = 0.0
                if self._force or now - last_query >= QUERY_INTERVAL:
                    self._force = False
                    reader.send_query()
                    last_query = now
                    if pending_since is None:
                        pending_since = now
                pct, chg = reader.read_status()
            except OSError:
                reader.close()
                set_state("nodongle")
                pending_since = None
                self.msleep(2000)
                continue

            if pct is not None or chg is not None:
                pending_since = None
                set_state("online")
                if chg is not None and chg != cur_charging:
                    cur_charging = chg
                    self.charging.emit(chg)
                if pct is not None:
                    self.battery.emit(pct)
            elif pending_since is not None and now - pending_since > OFFLINE_AFTER:
                set_state("offline")
            self.msleep(300)
        reader.close()


# ---------------------------------------------------------------- 介面元件
class Bar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(6)
        self.value = 0
        self.color = DIM

    def set(self, value, color):
        self.value = value
        self.color = color
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        r = QRectF(self.rect())
        p.setBrush(QColor(TRACK))
        p.drawRoundedRect(r, 3, 3)
        w = r.width() * max(0, min(100, self.value)) / 100
        if w > 0:
            p.setBrush(QColor(self.color))
            p.drawRoundedRect(QRectF(0, 0, max(w, 6), r.height()), 3, 3)


BOLT = [(0.62, 0.0), (0.10, 0.57), (0.44, 0.57), (0.36, 1.0),
        (0.90, 0.39), (0.55, 0.39)]


class Bolt(QWidget):
    """平面閃電圖示（充電中顯示）。"""

    def __init__(self):
        super().__init__()
        self.setFixedSize(26, 50)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(GREEN))
        w, h = self.width(), self.height()
        p.drawPolygon(QPolygonF([QPointF(x * w, y * h) for x, y in BOLT]))


class Panel(QWidget):
    STATUS = {
        None: (MUTED, "連線中…"),
        "online": (GREEN, "2.4G 已連線"),
        "offline": (AMBER, "耳機未連線"),
        "nodongle": (RED, "未偵測到接收器"),
    }

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 210)
        self._drag = None
        self.pct = None
        self.state = None
        self.updated = None
        self.charging = False

        btn_css = (
            "QPushButton{background:transparent;border:none;color:%s;"
            "font-size:18px;padding:0 4px;}"
            "QPushButton:hover{color:%s;}" % (MUTED, TEXT)
        )

        title = QLabel("ROG DELTA II")
        tf = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
        tf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        title.setFont(tf)
        title.setStyleSheet(f"color:{MUTED};")

        b_min = QPushButton("–")
        b_close = QPushButton("×")
        for b in (b_min, b_close):
            b.setStyleSheet(btn_css)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedSize(26, 26)
        b_min.clicked.connect(self.hide)
        b_close.clicked.connect(self.hide)

        head = QHBoxLayout()
        head.addWidget(title)
        head.addStretch(1)
        head.addWidget(b_min)
        head.addWidget(b_close)

        self.big = QLabel()
        self.big.setTextFormat(Qt.TextFormat.RichText)
        self.bolt = Bolt()
        self.bar = Bar()

        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.RichText)
        self.status.setStyleSheet(f"color:{MUTED};font-size:12px;")
        self.time = QLabel()
        self.time.setStyleSheet(f"color:{DIM};font-size:12px;")
        foot = QHBoxLayout()
        foot.addWidget(self.status)
        foot.addStretch(1)
        foot.addWidget(self.time)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 14, 18, 18)
        root.setSpacing(0)
        root.addLayout(head)
        root.addStretch(1)
        numrow = QHBoxLayout()
        numrow.setSpacing(6)
        numrow.addWidget(self.big)
        numrow.addWidget(self.bolt, 0, Qt.AlignmentFlag.AlignVCenter)
        numrow.addStretch(1)
        root.addLayout(numrow)
        root.addSpacing(10)
        root.addWidget(self.bar)
        root.addStretch(1)
        root.addLayout(foot)

        self.render_state()

    def place_bottom_right(self):
        g = QGuiApplication.primaryScreen().availableGeometry()
        self.move(g.right() - self.width() - 16, g.bottom() - self.height() - 16)

    # ---- 狀態更新
    def set_battery(self, pct):
        self.pct = pct
        self.updated = datetime.now()
        self.render_state()

    def set_state(self, state):
        self.state = state
        self.render_state()

    def set_charging(self, charging):
        self.charging = charging
        self.render_state()

    def render_state(self):
        online = self.state == "online"
        self.bolt.setVisible(online and self.charging)
        if self.pct is None:
            num, num_color, bar_color, val = "--", DIM, DIM, 0
        else:
            num = str(self.pct)
            val = self.pct
            if online:
                num_color = TEXT
                bar_color = level_color(self.pct)
            else:
                num_color, bar_color = DIM, DIM
        self.big.setText(
            f"<span style=\"font-family:'Segoe UI Light','Segoe UI';"
            f"font-size:68px;color:{num_color};\">{num}</span>"
            f"<span style=\"font-family:'Segoe UI';font-size:24px;"
            f"color:{DIM};\"> %</span>"
        )
        self.bar.set(val, bar_color)
        dot, text = self.STATUS.get(self.state, self.STATUS[None])
        self.status.setText(f"<span style='color:{dot};'>●</span>&nbsp;&nbsp;{text}")
        self.time.setText(
            self.updated.strftime("更新 %H:%M") if self.updated else ""
        )

    # ---- 繪製圓角底板
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(QColor(BG))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 14, 14)

    # ---- 拖曳視窗
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _):
        self._drag = None

    def closeEvent(self, e):
        e.ignore()
        self.hide()


# ---------------------------------------------------------------- 系統匣
def make_icon(text, color, alpha=255):
    """系統匣圖示；alpha < 255 時數字變暗（充電呼吸效果用）。"""
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(BG))
    p.drawRoundedRect(QRectF(0, 0, 64, 64), 12, 12)
    size = 40 if len(text) <= 2 else 30
    p.setFont(QFont("Segoe UI", size, QFont.Weight.Bold))
    c = QColor(color)
    if alpha < 255:
        c.setAlpha(alpha)
    p.setPen(c)
    p.drawText(QRect(0, 0, 64, 64), Qt.AlignmentFlag.AlignCenter, text)
    p.end()
    return QIcon(pm)


# 充電時數字「慢慢漸暗、再慢慢漸亮」（呼吸效果）
BREATH_SEC = 5.0   # 一個完整循環的秒數，越大越慢
MIN_ALPHA = 110    # 最暗時的不透明度（0~255），越大越不明顯
TICK_MS = 120      # 多久更新一次畫面
ALPHA_STEP = 8     # 不透明度以此為單位進位，變化不大時不重畫圖示


def breathe_alpha(t):
    """t 秒時的數字不透明度：從全亮開始，用餘弦曲線漸暗再漸亮。"""
    k = 0.5 + 0.5 * math.cos(2 * math.pi * t / BREATH_SEC)
    a = MIN_ALPHA + (255 - MIN_ALPHA) * k
    return min(255, int(round(a / ALPHA_STEP)) * ALPHA_STEP)


def tray_view(state, pct, charging):
    """決定系統匣圖示：回傳 (文字, 顏色, 是否呼吸, 提示文字)。"""
    if state == "online" and pct is not None:
        tip = f"{APP_NAME}：{pct}%" + ("（充電中）" if charging else "")
        return str(pct), level_color(pct), bool(charging), tip
    if state == "offline":
        return "–", AMBER, False, f"{APP_NAME}：耳機未連線"
    if state == "nodongle":
        return "×", RED, False, f"{APP_NAME}：未偵測到接收器"
    return None


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "DeltaBattery"


MINIMIZED_FLAG = "--minimized"


def _autostart_command():
    """開機自啟動的命令列；帶 --minimized，啟動後只留在系統匣。"""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" {MINIMIZED_FLAG}'
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    return f'"{exe}" "{os.path.abspath(__file__)}" {MINIMIZED_FLAG}'


def is_autostart():
    if sys.platform != "win32":
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, RUN_NAME)
            return True
    except OSError:
        return False


def set_autostart(on):
    if sys.platform != "win32":
        return
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as k:
        if on:
            winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, _autostart_command())
        else:
            try:
                winreg.DeleteValue(k, RUN_NAME)
            except FileNotFoundError:
                pass


class Controller:
    def __init__(self, app):
        self.app = app
        self.panel = Panel()
        self.mon = Monitor()
        self.notified = False
        self.pct = None
        self.state = None
        self.charging = False
        self.alpha = 255
        self.breath_t0 = 0.0
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.on_blink)

        self.tray = QSystemTrayIcon(make_icon("…", MUTED))
        self.tray.setToolTip(APP_NAME)

        self.menu = QMenu()
        a_show = QAction("顯示視窗", self.menu)
        a_refresh = QAction("立即更新", self.menu)
        self.a_auto = QAction("開機自動啟動", self.menu)
        self.a_auto.setCheckable(True)
        self.a_auto.setChecked(is_autostart())
        a_quit = QAction("結束", self.menu)
        a_show.triggered.connect(self.show_panel)
        a_refresh.triggered.connect(self.mon.refresh)
        self.a_auto.toggled.connect(self.toggle_autostart)
        a_quit.triggered.connect(app.quit)
        for a in (a_show, a_refresh):
            self.menu.addAction(a)
        self.menu.addSeparator()
        self.menu.addAction(self.a_auto)
        self.menu.addSeparator()
        self.menu.addAction(a_quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray)

        self.mon.battery.connect(self.on_battery)
        self.mon.charging.connect(self.on_charging)
        self.mon.state.connect(self.on_state)
        app.aboutToQuit.connect(self.shutdown)

    def start(self, show_panel=True):
        self.tray.show()
        self.panel.place_bottom_right()
        if show_panel:
            self.panel.show()
        self.mon.start()

    def shutdown(self):
        self.mon.stop()
        self.mon.wait(3000)
        self.tray.hide()

    def show_panel(self):
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()

    def on_tray(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.panel.isVisible():
                self.panel.hide()
            else:
                self.show_panel()

    def toggle_autostart(self, on):
        try:
            set_autostart(on)
        except OSError:
            self.a_auto.blockSignals(True)
            self.a_auto.setChecked(not on)
            self.a_auto.blockSignals(False)

    def on_battery(self, pct):
        self.pct = pct
        self.panel.set_battery(pct)
        self.refresh_tray()
        if pct <= LOW_NOTIFY and not self.notified:
            self.notified = True
            self.tray.showMessage(
                APP_NAME,
                f"耳機電量剩 {pct}%，記得充電",
                QSystemTrayIcon.MessageIcon.Warning,
                8000,
            )
        elif pct >= LOW_RESET:
            self.notified = False

    def on_charging(self, charging):
        self.charging = charging
        self.panel.set_charging(charging)
        self.refresh_tray()

    def on_state(self, state):
        self.state = state
        self.panel.set_state(state)
        self.refresh_tray()

    def on_blink(self):
        alpha = breathe_alpha(time.monotonic() - self.breath_t0)
        if alpha != self.alpha:  # 沒變就不重畫，減少系統匣更新
            self.alpha = alpha
            self.refresh_tray()

    def refresh_tray(self):
        v = tray_view(self.state, self.pct, self.charging)
        if v is None:
            return
        text, color, breathe, tip = v
        if breathe and not self.blink_timer.isActive():
            self.breath_t0 = time.monotonic()
            self.alpha = 255
            self.blink_timer.start(TICK_MS)
        elif not breathe and self.blink_timer.isActive():
            self.blink_timer.stop()
            self.alpha = 255
        self.tray.setIcon(make_icon(text, color, self.alpha if breathe else 255))
        self.tray.setToolTip(tip)


MENU_CSS = (
    f"QMenu{{background:#1B1B1F;color:{TEXT};border:1px solid {BORDER};"
    "padding:4px;font-family:'Segoe UI';font-size:13px;}"
    "QMenu::item{padding:6px 24px;}"
    "QMenu::item:selected{background:#2A2A30;}"
    f"QMenu::separator{{height:1px;background:{BORDER};margin:4px 8px;}}"
    f"QToolTip{{background:#1B1B1F;color:{TEXT};border:1px solid {BORDER};}}"
)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(MENU_CSS)

    # 只允許開一個實例
    lock = QLockFile(os.path.join(tempfile.gettempdir(), "delta2_battery.lock"))
    if not lock.tryLock(0):
        sys.exit(0)

    # 舊版寫入的自啟動項目沒有 --minimized；已啟用的話順手更新成新命令
    try:
        if is_autostart():
            set_autostart(True)
    except OSError:
        pass

    ctl = Controller(app)
    ctl.start(show_panel=MINIMIZED_FLAG not in sys.argv[1:])
    code = app.exec()
    lock.unlock()
    sys.exit(code)


if __name__ == "__main__":
    main()
