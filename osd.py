#!/usr/bin/env python3
# Dark Volume OSD (PyQt6 / PyQt5 compatible)
# Controls ALL playback sinks (PulseAudio/PipeWire via pactl)
# Black, glossy OSD; bar fill is pure #000000
# Copyright (c) 2025 JJ Posti <techtimejourney.net> This program comes with ABSOLUTELY NO WARRANTY; for details see: http://www.gnu.org/copyleft/gpl.html.  
# This is free software, and you are welcome to redistribute it under GPL Version 2, June 1991")

#!/usr/bin/env python3

import sys, threading, subprocess, time
sys.dont_write_bytecode = True
from evdev import InputDevice, ecodes, categorize, list_devices

# --- Try PyQt6 first, fallback to PyQt5 ---
USING_QT6 = False
try:
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QPoint
    from PyQt6.QtGui import QPalette, QColor, QPainter, QBrush, QLinearGradient
    from PyQt6.QtWidgets import (
        QApplication, QStyleFactory, QWidget, QVBoxLayout,
        QLabel, QGraphicsDropShadowEffect
    )
    USING_QT6 = True
    print("Using PyQt6")
except Exception as e:
    print("PyQt6 import failed, falling back to PyQt5:", e)
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QPoint
    from PyQt5.QtGui import QPalette, QColor, QPainter, QBrush, QLinearGradient
    from PyQt5.QtWidgets import (
        QApplication, QStyleFactory, QWidget, QVBoxLayout,
        QLabel, QDesktopWidget, QGraphicsDropShadowEffect
    )
    USING_QT6 = False
    print("Using PyQt5")

# -------- Cross-version helpers --------
def wflag(name: str):
    return getattr(Qt.WindowType, name) if USING_QT6 else getattr(Qt, name)

def alignflag(name: str):
    return getattr(Qt.AlignmentFlag, name) if USING_QT6 else getattr(Qt, name)

def role(name: str):
    return getattr(QPalette.ColorRole, name) if USING_QT6 else getattr(QPalette, name)

def pen_style(name: str):
    return getattr(Qt.PenStyle, name) if USING_QT6 else getattr(Qt, name)

def render_hint_antialiasing():
    return QPainter.RenderHint.Antialiasing if USING_QT6 else QPainter.Antialiasing

def available_geometry(widget: QWidget):
    if USING_QT6:
        scr = widget.screen() or QApplication.primaryScreen()
        return scr.availableGeometry()
    else:
        return QDesktopWidget().availableGeometry()

# -------- Audio helpers (PulseAudio/PipeWire via pactl) --------
def _run(cmd):
    return subprocess.check_output(cmd, text=True)

def list_playback_sinks():
    try:
        out = _run(["pactl", "list", "sinks", "short"])
    except Exception:
        return []
    sinks = []
    for line in out.splitlines():
        parts = line.split('\t')
        if parts and parts[0].strip().isdigit():
            sinks.append(parts[0].strip())
    return sinks

def get_all_volumes_and_mutes():
    try:
        out = _run(["pactl", "list", "sinks"])
    except Exception:
        return [], []
    volumes, mutes = [], []
    cur_vol, cur_mute = None, None
    for line in out.splitlines():
        ls = line.strip()
        if ls.startswith("Sink #"):
            if cur_vol is not None:
                volumes.append(cur_vol)
                mutes.append(cur_mute if cur_mute is not None else False)
            cur_vol, cur_mute = None, None
        elif ls.startswith("Volume:"):
            percent = None
            for token in ls.replace(',', ' ').split():
                if token.endswith('%'):
                    try:
                        percent = int(token.strip('%'))
                        break
                    except ValueError:
                        pass
            if percent is not None:
                cur_vol = max(0, min(100, percent))
        elif ls.startswith("Mute:"):
            cur_mute = ("yes" in ls.lower())
    if cur_vol is not None:
        volumes.append(cur_vol)
        mutes.append(cur_mute if cur_mute is not None else False)
    return volumes, mutes

def get_overall_volume():
    vols, _ = get_all_volumes_and_mutes()
    return int(round(sum(vols) / len(vols))) if vols else 0

def is_all_muted():
    _, mutes = get_all_volumes_and_mutes()
    return all(mutes) if mutes else False

def set_volume_all(volume: int):
    volume = max(0, min(100, volume))
    for sink in list_playback_sinks():
        subprocess.run(["pactl", "set-sink-volume", sink, f"{volume}%"], check=False)

def change_volume_all(delta: int):
    new = max(0, min(100, get_overall_volume() + delta))
    set_volume_all(new)
    return new

def toggle_mute_all():
    for sink in list_playback_sinks():
        subprocess.run(["pactl", "set-sink-mute", sink, "toggle"], check=False)

# -------- Black (pure #000000) Gloss Bar --------
class GlossBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.setMinimumHeight(28)

    def setValue(self, val: int):
        self._value = max(0, min(100, int(val)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(render_hint_antialiasing())

        r = self.rect()
        radius = 14

        # Outer dark glossy frame
        bg_grad = QLinearGradient(0, 0, 0, r.height())
        bg_grad.setColorAt(0.0, QColor(14, 14, 14))
        bg_grad.setColorAt(0.5, QColor(10, 10, 10))
        bg_grad.setColorAt(1.0, QColor(8, 8, 8))
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(QColor(32, 32, 32))
        painter.drawRoundedRect(r, radius, radius)

        # Filled portion → PURE BLACK (#000000)
        fill_w = int(r.width() * (self._value / 100.0))
        if fill_w > 0:
            fill_rect = r.adjusted(2, 2, -2, -2)
            fill_rect.setWidth(max(0, fill_w - 4))
            painter.setBrush(QColor(0, 0, 0))  # solid black
            painter.setPen(pen_style('NoPen'))
            painter.drawRoundedRect(fill_rect, radius-2, radius-2)

        # Subtle top glass highlight
        highlight = r.adjusted(4, 4, -4, -max(6, r.height() // 2))
        gloss = QLinearGradient(0, highlight.top(), 0, highlight.bottom())
        gloss.setColorAt(0.0, QColor(255, 255, 255, 12))
        gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(gloss))
        painter.setPen(pen_style('NoPen'))
        painter.drawRoundedRect(highlight, radius-4, radius-4)

# -------- Black & Shiny OSD --------
class VolumeOSD(QWidget):
    def __init__(self, step=5):
        super().__init__()
        self.step = step
        self._slide = None
        self._hidden_target = None
        self._visible_target = None
        self.init_ui()

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(1600)
        self.hide_timer.timeout.connect(self.slide_out)

        self.update_osd_from_system()

    def init_ui(self):
        self.setWindowTitle("Volume OSD")
        self.setWindowFlags(
            wflag('FramelessWindowHint')
            | wflag('WindowStaysOnTopHint')
            | wflag('Tool')
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(380, 130)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.label = QLabel("Volume: ??%")
        self.label.setAlignment(alignflag('AlignCenter'))
        self.label.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: 800;
                color: #f2f2f2;
                letter-spacing: 0.5px;
            }
        """)

        self.progress_bar = GlossBar()

        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(42)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 200))
        self.setGraphicsEffect(shadow)

        self._slide = QPropertyAnimation(self, b"pos")
        self._slide.setDuration(260)
        self._slide.setEasingCurve(QEasingCurve.Type.OutCubic)

    def compute_positions(self):
        geo = available_geometry(self)
        x = (geo.width() - self.width()) // 2 + geo.x()
        y_visible = int(geo.height() * 0.82 - self.height() // 2) + geo.y()
        y_hidden = y_visible + 40
        self._visible_target = QPoint(x, y_visible)
        self._hidden_target = QPoint(x, y_hidden)

    def slide_in(self):
        self.compute_positions()
        if not self.isVisible():
            self.move(self._hidden_target)
            self.show()
            self.raise_()
        self._slide.stop()
        self._slide.setStartValue(self.pos())
        self._slide.setEndValue(self._visible_target)
        self._slide.start()

    def slide_out(self):
        self.compute_positions()
        self._slide.stop()
        self._slide.setStartValue(self.pos())
        self._slide.setEndValue(self._hidden_target)
        self._slide.finished.connect(self.hide)
        self._slide.start()

    def show_osd_again(self):
        self.slide_in()
        self.hide_timer.start()

    def update_osd_from_system(self):
        if is_all_muted():
            self.label.setText("Muted")
            self.progress_bar.setValue(0)
        else:
            vol = get_overall_volume()
            self.label.setText(f"Volume: {vol}%")
            self.progress_bar.setValue(vol)
        self.slide_in()
        self.hide_timer.start()

    # Bound below
    def increase_volume(self): ...
    def decrease_volume(self): ...
    def toggle_mute(self): ...

class VolumeSignals(QObject):
    increase = pyqtSignal()
    decrease = pyqtSignal()
    mute = pyqtSignal()

# -------- evdev event loop --------
def read_keyboard_events(signals: VolumeSignals, dev_path: str):
    try:
        dev = InputDevice(dev_path)
        print(f"[INFO] Listening on {dev_path} for keyboard events.")
    except Exception as e:
        print(f"[ERROR] Could not open {dev_path}: {e}")
        return
    MIN_INTERVAL = 0.1
    last_event_times = {}
    KEY_UP = ecodes.KEY_UP
    KEY_DOWN = ecodes.KEY_DOWN
    KEY_M = ecodes.KEY_M
    KEY_VOLUMEUP = ecodes.KEY_VOLUMEUP
    KEY_VOLUMEDOWN = ecodes.KEY_VOLUMEDOWN
    KEY_MUTE = ecodes.KEY_MUTE
    KEY_LEFTALT = ecodes.KEY_LEFTALT
    KEY_RIGHTALT = ecodes.KEY_RIGHTALT
    alt_pressed = False
    for event in dev.read_loop():
        if event.type != ecodes.EV_KEY:
            continue
        key_event = categorize(event)
        current_time = time.monotonic()
        last_time = last_event_times.get(key_event.scancode, 0)
        if (current_time - last_time) < MIN_INTERVAL:
            continue
        last_event_times[key_event.scancode] = current_time
        if key_event.keystate == key_event.key_down:
            if key_event.scancode in (KEY_LEFTALT, KEY_RIGHTALT):
                alt_pressed = True
            if alt_pressed:
                if key_event.scancode == KEY_UP:
                    signals.increase.emit()
                elif key_event.scancode == KEY_DOWN:
                    signals.decrease.emit()
                elif key_event.scancode == KEY_M:
                    signals.mute.emit()
            if key_event.scancode == KEY_VOLUMEUP:
                signals.increase.emit()
            elif key_event.scancode == KEY_VOLUMEDOWN:
                signals.decrease.emit()
            elif key_event.scancode == KEY_MUTE:
                signals.mute.emit()
        elif key_event.keystate == key_event.key_up:
            if key_event.scancode in (KEY_LEFTALT, KEY_RIGHTALT):
                alt_pressed = False

# -------- Bind OSD actions to audio helpers --------
def bind_osd_methods():
    def increase_volume(self: VolumeOSD):
        new_vol = change_volume_all(self.step)
        self.label.setText(f"Volume: {new_vol}%")
        self.progress_bar.setValue(new_vol)
        self.show_osd_again()
    def decrease_volume(self: VolumeOSD):
        new_vol = change_volume_all(-self.step)
        self.label.setText(f"Volume: {new_vol}%")
        self.progress_bar.setValue(new_vol)
        self.show_osd_again()
    def toggle_mute(self: VolumeOSD):
        toggle_mute_all()
        if is_all_muted():
            self.label.setText("Muted")
            self.progress_bar.setValue(0)
        else:
            vol = get_overall_volume()
            self.label.setText(f"Volume: {vol}%")
            self.progress_bar.setValue(vol)
        self.show_osd_again()
    VolumeOSD.increase_volume = increase_volume
    VolumeOSD.decrease_volume = decrease_volume
    VolumeOSD.toggle_mute = toggle_mute

# -------- Keyboard device discovery (evdev) --------
def find_keyboard_devices():
    devices = list_devices()
    keyboard_paths = []
    for dev_path in devices:
        try:
            dev = InputDevice(dev_path)
        except Exception:
            continue
        if "keyboard" in (dev.name or "").lower():
            keyboard_paths.append(dev_path)
    if keyboard_paths:
        print("[INFO] Found keyboard devices:")
        for path in keyboard_paths:
            try:
                print(f"   {path}: {InputDevice(path).name}")
            except Exception:
                print(f"   {path}")
        return keyboard_paths
    # Fallback: KEY_A..KEY_Z capability
    fallback_paths = []
    for dev_path in devices:
        try:
            dev = InputDevice(dev_path)
            caps = dev.capabilities().get(ecodes.EV_KEY, [])
            if ecodes.KEY_A in caps and ecodes.KEY_Z in caps:
                fallback_paths.append(dev_path)
        except Exception:
            continue
    if fallback_paths:
        print("[INFO] Found devices via fallback (KEY_A..KEY_Z):")
        for path in fallback_paths:
            try:
                print(f"   {path}: {InputDevice(path).name}")
            except Exception:
                print(f"   {path}")
        return fallback_paths
    print("[ERROR] No suitable keyboard devices found.")
    sys.exit(1)


# -------- Main --------
def main():
    keyboard_paths = find_keyboard_devices()
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    pal = QPalette()
    pal.setColor(role('Window'), QColor(10, 10, 10))
    pal.setColor(role('AlternateBase'), QColor(16, 16, 16))
    pal.setColor(role('Base'), QColor(16, 16, 16))
    pal.setColor(role('WindowText'), QColor(235, 235, 235))
    pal.setColor(role('Text'), QColor(235, 235, 235))
    pal.setColor(role('Button'), QColor(12, 12, 12))
    pal.setColor(role('ButtonText'), QColor(235, 235, 235))
    pal.setColor(role('Highlight'), QColor(80, 120, 255))
    pal.setColor(role('HighlightedText'), QColor(0, 0, 0))
    app.setPalette(pal)
    osd = VolumeOSD(step=5)
    signals = VolumeSignals()
    signals.increase.connect(osd.increase_volume)
    signals.decrease.connect(osd.decrease_volume)
    signals.mute.connect(osd.toggle_mute)
    for path in keyboard_paths:
        t = threading.Thread(target=read_keyboard_events, args=(signals, path), daemon=True)
        t.start()
    sys.exit(app.exec() if USING_QT6 else app.exec_())

bind_osd_methods()

if __name__ == "__main__":
    main()
