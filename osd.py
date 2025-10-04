#!/usr/bin/env python3
"""
Dark Volume OSD with Themes (PyQt6 / PyQt5)
- Controls ALL playback sinks (PulseAudio/PipeWire via pactl)
- Themed OSD panel via Qt Style Sheets (QSS)
- Themed custom GlossBar via qproperty-* (pyqtProperty)
- Robust keyboard handling with ALT combos + hardware volume keys
- GPLv2 JJ Posti <techtimejourney.net>
"""

import sys, threading, subprocess, time, os
sys.dont_write_bytecode = True
from evdev import InputDevice, ecodes, categorize, list_devices

# ──────────────────────────────── Qt imports (Qt6 → Qt5 fallback) ────────────────────────────────
USING_QT6 = False
try:
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QPoint, pyqtProperty
    from PyQt6.QtGui import QPalette, QColor, QPainter, QBrush, QLinearGradient
    from PyQt6.QtWidgets import QApplication, QStyleFactory, QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
    USING_QT6 = True
    print("Using PyQt6")
except Exception as e:
    print("PyQt6 import failed, falling back to PyQt5:", e)
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QPoint, pyqtProperty
    from PyQt5.QtGui import QPalette, QColor, QPainter, QBrush, QLinearGradient
    from PyQt5.QtWidgets import QApplication, QStyleFactory, QWidget, QVBoxLayout, QLabel, QDesktopWidget, QGraphicsDropShadowEffect
    USING_QT6 = False
    print("Using PyQt5")

# ──────────────────────────────── Cross‑Qt helpers ────────────────────────────────
def wflag(name: str):
    return getattr(Qt.WindowType, name) if USING_QT6 else getattr(Qt, name)

def alignflag(name: str):
    return getattr(Qt.AlignmentFlag, name) if USING_QT6 else getattr(Qt, name)

def role(name: str):
    return getattr(QPalette.ColorRole, name) if USING_QT6 else getattr(QPalette, name)

def pen_style(name: str):
    return getattr(Qt.PenStyle, name) if USING_QT6 else getattr(Qt, name)

def easing(name: str):
    return getattr(QEasingCurve.Type, name) if USING_QT6 else getattr(QEasingCurve, name)

def aa_hint():
    return QPainter.RenderHint.Antialiasing if USING_QT6 else QPainter.Antialiasing

def available_geometry(widget: QWidget):
    """Screen work area for positioning the OSD (Qt6/Qt5 compatible)."""
    if USING_QT6:
        scr = widget.screen() or QApplication.primaryScreen()
        return scr.availableGeometry()
    return QDesktopWidget().availableGeometry()

# ──────────────────────────────── THEMES (QSS + shadow colors) ────────────────────────────────
THEMES = {
    # Sleek dark theme (default)
    "dark": {
        "qss": """
        QWidget#panel {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                      stop:0 #141414, stop:0.5 #0f0f0f, stop:1 #0a0a0a);
            border: 1px solid #262626;
            border-radius: 16px;
        }
        QWidget#panel QLabel {
            color: #f2f2f2;
            font-size: 26px;
            font-weight: 800;
        }
        GlossBar {
            qproperty-frameStart: #141414;
            qproperty-frameMid:   #0F0F0F;
            qproperty-frameEnd:   #0B0B0B;
            qproperty-outline:    #202020;
            qproperty-fill:       #000000;               /* pure black */
            qproperty-glossStart: rgba(255,255,255,30);
            qproperty-glossEnd:   rgba(255,255,255,0);
            qproperty-radius:     14;
        }
        """,
        "shadow": QColor(0, 0, 0, 200),
    },

    # Futuristic blue / cyber look
    "blue": {
        "qss": """
        QWidget#panel {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                      stop:0 #0a1625, stop:0.45 #081529, stop:1 #061021);
            border: 1px solid #1b6bff;
            border-radius: 16px;
        }
        QWidget#panel QLabel {
            color: #9bd6ff;
            font-size: 26px;
            font-weight: 900;
        }
        GlossBar {
            qproperty-frameStart: #0b223a;
            qproperty-frameMid:   #0a1a31;
            qproperty-frameEnd:   #081529;
            qproperty-outline:    #1f3d66;
            qproperty-fill:       #00b7ff;               /* bright aqua fill */
            qproperty-glossStart: rgba(160,220,255,70);
            qproperty-glossEnd:   rgba(160,220,255,0);
            qproperty-radius:     14;
        }
        """,
        "shadow": QColor(0, 96, 196, 170),
    },

    # Grey, worn-out, industrial
    "grey": {
        "qss": """
        QWidget#panel {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                      stop:0 #333333, stop:0.5 #2a2a2a, stop:1 #1f1f1f);
            border: 1px solid #3a3a3a;
            border-radius: 16px;
        }
        QWidget#panel QLabel {
            color: #dedede;
            font-size: 26px;
            font-weight: 700;
        }
        GlossBar {
            qproperty-frameStart: #3a3a3a;
            qproperty-frameMid:   #2b2b2b;
            qproperty-frameEnd:   #242424;
            qproperty-outline:    #4a4a4a;
            qproperty-fill:       #2a2a2a;               /* dark steel */
            qproperty-glossStart: rgba(255,255,255,25);
            qproperty-glossEnd:   rgba(255,255,255,0);
            qproperty-radius:     14;
        }
        """,
        "shadow": QColor(0, 0, 0, 180),
    },

    # Warm wood‑like feel (approx via gradients)
    "wood": {
        "qss": """
        QWidget#panel {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                      stop:0 #8b5a2b, stop:0.35 #7a4a21, stop:0.7 #6a3f1b, stop:1 #523311);
            border: 1px solid #3b2210;
            border-radius: 16px;
        }
        QWidget#panel QLabel {
            color: #f9ecda;
            font-size: 26px;
            font-weight: 800;
        }
        GlossBar {
            qproperty-frameStart: #6b3f1c;
            qproperty-frameMid:   #5a3417;
            qproperty-frameEnd:   #4a2b12;
            qproperty-outline:    #3b2210;
            qproperty-fill:       #3b230a;               /* dark chocolate */
            qproperty-glossStart: rgba(255,230,180,60);  /* warm highlight */
            qproperty-glossEnd:   rgba(255,230,180,0);
            qproperty-radius:     14;
        }
        """,
        "shadow": QColor(70, 40, 10, 190),
    },
}

DEFAULT_THEME = "dark"

# ──────────────────────────────── Audio helpers (pactl) ────────────────────────────────
def _check_output(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True)

def list_playback_sinks() -> list[str]:
    """Return sink IDs (strings). Empty if pactl not available."""
    try:
        out = _check_output(["pactl", "list", "sinks", "short"])
    except Exception:
        return []
    sinks = []
    for line in out.splitlines():
        parts = line.split('\t')
        if parts and parts[0].strip().isdigit():
            sinks.append(parts[0].strip())
    return sinks

def get_all_volumes_and_mutes():
    """Parse 'pactl list sinks' → ([vol%...], [mute-bool...])."""
    try:
        out = _check_output(["pactl", "list", "sinks"])
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
            for token in ls.replace(',', ' ').split():
                if token.endswith('%'):
                    try:
                        cur_vol = max(0, min(100, int(token[:-1])))
                        break
                    except ValueError:
                        pass
        elif ls.startswith("Mute:"):
            cur_mute = ("yes" in ls.lower())
    if cur_vol is not None:
        volumes.append(cur_vol)
        mutes.append(cur_mute if cur_mute is not None else False)
    return volumes, mutes

def get_state():
    """Return (overall_volume:int 0..100, all_muted:bool)."""
    vols, mutes = get_all_volumes_and_mutes()
    overall = int(round(sum(vols) / len(vols))) if vols else 0
    return overall, (all(mutes) if mutes else False)

def set_volume_all(volume: int):
    """Clamp 0..100 and apply to every sink."""
    v = max(0, min(100, int(volume)))
    for sink in list_playback_sinks():
        subprocess.run(["pactl", "set-sink-volume", sink, f"{v}%"], check=False)

def change_volume_all(delta: int) -> int:
    """Relative change across all sinks → returns new overall volume."""
    cur, _ = get_state()
    new_v = max(0, min(100, cur + int(delta)))
    set_volume_all(new_v)
    return new_v

def toggle_mute_all():
    """Toggle mute on every sink."""
    for sink in list_playback_sinks():
        subprocess.run(["pactl", "set-sink-mute", sink, "toggle"], check=False)

# ──────────────────────────────── UI: themeable GlossBar (via pyqtProperty) ────────────────────────────────
class GlossBar(QWidget):
    """
    Rounded progress bar with themeable frame/fill/gloss via QSS:
      GlossBar {
          qproperty-frameStart: #141414;
          qproperty-frameMid:   #0F0F0F;
          qproperty-frameEnd:   #0B0B0B;
          qproperty-outline:    #202020;
          qproperty-fill:       #000000;
          qproperty-glossStart: rgba(255,255,255,30);
          qproperty-glossEnd:   rgba(255,255,255,0);
          qproperty-radius:     14;
      }
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        # Defaults (overridden by QSS)
        self._frameStart = QColor(20, 20, 20)
        self._frameMid   = QColor(15, 15, 15)
        self._frameEnd   = QColor(11, 11, 11)
        self._outline    = QColor(32, 32, 32)
        self._fill       = QColor(0, 0, 0)
        self._glossStart = QColor(255, 255, 255, 30)
        self._glossEnd   = QColor(255, 255, 255, 0)
        self._radius     = 14
        self.setMinimumHeight(28)

    # ---- properties for QSS (qproperty-*) ----
    def _getFrameStart(self): return self._frameStart
    def _setFrameStart(self, c): self._frameStart = QColor(c); self.update()
    frameStart = pyqtProperty(QColor, fget=_getFrameStart, fset=_setFrameStart)

    def _getFrameMid(self): return self._frameMid
    def _setFrameMid(self, c): self._frameMid = QColor(c); self.update()
    frameMid = pyqtProperty(QColor, fget=_getFrameMid, fset=_setFrameMid)

    def _getFrameEnd(self): return self._frameEnd
    def _setFrameEnd(self, c): self._frameEnd = QColor(c); self.update()
    frameEnd = pyqtProperty(QColor, fget=_getFrameEnd, fset=_setFrameEnd)

    def _getOutline(self): return self._outline
    def _setOutline(self, c): self._outline = QColor(c); self.update()
    outline = pyqtProperty(QColor, fget=_getOutline, fset=_setOutline)

    def _getFill(self): return self._fill
    def _setFill(self, c): self._fill = QColor(c); self.update()
    fill = pyqtProperty(QColor, fget=_getFill, fset=_setFill)

    def _getGlossStart(self): return self._glossStart
    def _setGlossStart(self, c): self._glossStart = QColor(c); self.update()
    glossStart = pyqtProperty(QColor, fget=_getGlossStart, fset=_setGlossStart)

    def _getGlossEnd(self): return self._glossEnd
    def _setGlossEnd(self, c): self._glossEnd = QColor(c); self.update()
    glossEnd = pyqtProperty(QColor, fget=_getGlossEnd, fset=_setGlossEnd)

    def _getRadius(self): return self._radius
    def _setRadius(self, v): self._radius = int(v); self.update()
    radius = pyqtProperty(int, fget=_getRadius, fset=_setRadius)

    # ---- API ----
    def setValue(self, val: int):
        self._value = max(0, min(100, int(val)))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(aa_hint())
        r = self.rect(); rad = self._radius

        # Outer frame
        bg = QLinearGradient(0, 0, 0, r.height())
        bg.setColorAt(0.0, self._frameStart)
        bg.setColorAt(0.5, self._frameMid)
        bg.setColorAt(1.0, self._frameEnd)
        p.setBrush(QBrush(bg)); p.setPen(self._outline)
        p.drawRoundedRect(r, rad, rad)

        # Fill
        fill_w = int(r.width() * (self._value / 100.0))
        if fill_w > 0:
            fill = r.adjusted(2, 2, -2, -2); fill.setWidth(max(0, fill_w - 4))
            p.setBrush(self._fill); p.setPen(pen_style('NoPen'))
            p.drawRoundedRect(fill, max(0, rad - 2), max(0, rad - 2))

        # Gloss highlight
        hi = r.adjusted(4, 4, -4, -max(6, r.height() // 2))
        gloss = QLinearGradient(0, hi.top(), 0, hi.bottom())
        gloss.setColorAt(0.0, self._glossStart); gloss.setColorAt(1.0, self._glossEnd)
        p.setBrush(QBrush(gloss)); p.setPen(pen_style('NoPen'))
        p.drawRoundedRect(hi, max(0, rad - 4), max(0, rad - 4))

# ──────────────────────────────── UI: OSD widget ────────────────────────────────
class VolumeOSD(QWidget):
    """On‑screen display that mirrors system volume state and animates in/out."""
    def __init__(self, step: int = 5, theme: str = DEFAULT_THEME):
        super().__init__()
        self.step = int(step)
        self._slide = QPropertyAnimation(self, b"pos")
        self._visible_target = self._hidden_target = QPoint(0, 0)

        self._build_ui()
        self.apply_theme(theme)          # apply a theme here
        self._setup_anim()
        self._setup_autohide()
        self.refresh_from_system()

    # --- UI setup ---
    def _build_ui(self):
        self.setWindowTitle("Volume OSD")
        self.setWindowFlags(
            wflag('FramelessWindowHint') |
            wflag('WindowStaysOnTopHint') |
            wflag('Tool')
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(380, 130)

        # The inner 'panel' gets the themed background & border.
        self.panel = QWidget(self)
        self.panel.setObjectName("panel")
        lay = QVBoxLayout(self.panel); lay.setContentsMargins(18, 18, 18, 18); lay.setSpacing(12)

        self.label = QLabel("Volume: ??%", self.panel)
        self.label.setAlignment(alignflag('AlignCenter'))

        self.bar = GlossBar(self.panel)

        lay.addWidget(self.label); lay.addWidget(self.bar)

        # Shadow around the panel (color adjusted per theme)
        self._shadow = QGraphicsDropShadowEffect(self.panel)
        self._shadow.setBlurRadius(42); self._shadow.setXOffset(0); self._shadow.setYOffset(10)
        self.panel.setGraphicsEffect(self._shadow)

        # Fit panel to top-level widget rect
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.addWidget(self.panel)

    def _setup_anim(self):
        self._slide.setDuration(260)
        self._slide.setEasingCurve(easing('OutCubic'))
        self._slide.finished.connect(self._on_slide_finished)

    def _setup_autohide(self):
        self._hide_timer = QTimer(self); self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(1600); self._hide_timer.timeout.connect(self.slide_out)

    # --- Theme application ---
    def apply_theme(self, name: str):
        """Apply a theme by name: dark | blue | grey | wood."""
        key = (name or "").lower()
        theme = THEMES.get(key, THEMES[DEFAULT_THEME])

        # Apply QSS at the application level so all widgets (including custom ones) receive it.
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme["qss"])
        else:
            # Fallback: set on this widget (shouldn't happen because app exists here)
            self.setStyleSheet(theme["qss"])

        # Shadow color (not style-able via QSS)
        self._shadow.setColor(theme.get("shadow", QColor(0, 0, 0, 200)))
        print(f"[THEME] QSS applied for '{key}'")

    # --- Positioning/animation ---
    def _compute_targets(self):
        geo = available_geometry(self)
        x = (geo.width() - self.width()) // 2 + geo.x()
        y_visible = int(geo.height() * 0.82 - self.height() // 2) + geo.y()
        y_hidden = y_visible + 40
        self._visible_target = QPoint(x, y_visible)
        self._hidden_target = QPoint(x, y_hidden)

    def _on_slide_finished(self):
        if self.pos() == self._hidden_target:
            self.hide()

    def slide_in(self):
        self._compute_targets()
        if not self.isVisible():
            self.move(self._hidden_target); self.show(); self.raise_()
        self._slide.stop(); self._slide.setStartValue(self.pos()); self._slide.setEndValue(self._visible_target); self._slide.start()

    def slide_out(self):
        self._compute_targets()
        self._slide.stop(); self._slide.setStartValue(self.pos()); self._slide.setEndValue(self._hidden_target); self._slide.start()

    def _show_and_arm_hide(self):
        self.slide_in()
        self._hide_timer.start()

    # --- State sync + actions ---
    def refresh_from_system(self):
        vol, muted = get_state()
        if muted:
            self.label.setText("Muted"); self.bar.setValue(0)
        else:
            self.label.setText(f"Volume: {vol}%"); self.bar.setValue(vol)
        self._show_and_arm_hide()

    def increase_volume(self):
        v = change_volume_all(self.step)
        self.label.setText(f"Volume: {v}%"); self.bar.setValue(v)
        self._show_and_arm_hide()

    def decrease_volume(self):
        v = change_volume_all(-self.step)
        self.label.setText(f"Volume: {v}%"); self.bar.setValue(v)
        self._show_and_arm_hide()

    def toggle_mute(self):
        toggle_mute_all()
        self.refresh_from_system()

# ──────────────────────────────── Signals to cross threads → Qt main thread ────────────────────────────────
class VolumeSignals(QObject):
    increase = pyqtSignal()
    decrease = pyqtSignal()
    mute     = pyqtSignal()

# ──────────────────────────────── Modifier & rate limiting ────────────────────────────────
class ModifierState:
    """Thread‑safe ALT tracker across devices (press on one, release on another)."""
    def __init__(self):
        self._lock = threading.Lock()
        self._alt_count = 0
    def press_alt(self):
        with self._lock: self._alt_count += 1
    def release_alt(self):
        with self._lock: self._alt_count = max(0, self._alt_count - 1)
    def is_alt_active(self) -> bool:
        with self._lock: return self._alt_count > 0

class RateLimiter:
    """Limit action emission rate (do NOT limit modifier state changes)."""
    def __init__(self, incdec=0.08, mute=0.20):
        self._lock = threading.Lock()
        self._last = {"inc": 0.0, "dec": 0.0, "mute": 0.0}
        self._gap  = {"inc": float(incdec), "dec": float(incdec), "mute": float(mute)}
    def allow(self, kind: str) -> bool:
        now = time.monotonic()
        with self._lock:
            if now - self._last.get(kind, 0.0) >= self._gap[kind]:
                self._last[kind] = now
                return True
            return False

# ──────────────────────────────── Keyboard event loop (evdev) ────────────────────────────────
def read_keyboard_events(signals: VolumeSignals, dev_path: str, mods: ModifierState, rate: RateLimiter):
    """Read key events from one device and emit debounced volume actions."""
    try:
        dev = InputDevice(dev_path)
        print(f"[INFO] Listening on {dev_path} ({dev.name})")
    except Exception as e:
        print(f"[ERROR] Could not open {dev_path}: {e}")
        return

    KEY_UP, KEY_DOWN, KEY_M = ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_M
    KEY_VOLUMEUP, KEY_VOLUMEDOWN, KEY_MUTE = ecodes.KEY_VOLUMEUP, ecodes.KEY_VOLUMEDOWN, ecodes.KEY_MUTE
    KEY_LEFTALT, KEY_RIGHTALT = ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT

    for event in dev.read_loop():
        if event.type != ecodes.EV_KEY:
            continue
        ke = categorize(event)
        ks = ke.keystate  # 0=up, 1=down, 2=hold
        is_press_or_hold = ks in (ke.key_down, getattr(ke, "key_hold", 2))

        # Always update ALT state immediately (never rate limit modifiers)
        if ke.scancode in (KEY_LEFTALT, KEY_RIGHTALT):
            if ks == ke.key_down:
                mods.press_alt()
            elif ks == ke.key_up:
                mods.release_alt()
            continue

        # Hardware volume keys
        if is_press_or_hold:
            if ke.scancode == KEY_VOLUMEUP and rate.allow("inc"):
                signals.increase.emit(); continue
            if ke.scancode == KEY_VOLUMEDOWN and rate.allow("dec"):
                signals.decrease.emit(); continue
            if ke.scancode == KEY_MUTE and rate.allow("mute"):
                signals.mute.emit(); continue

        # ALT combos (Up/Down/M)
        if mods.is_alt_active() and is_press_or_hold:
            if ke.scancode == KEY_UP and rate.allow("inc"):
                signals.increase.emit()
            elif ke.scancode == KEY_DOWN and rate.allow("dec"):
                signals.decrease.emit()
            elif ke.scancode == KEY_M and rate.allow("mute"):
                signals.mute.emit()

# ──────────────────────────────── Device discovery ────────────────────────────────
def find_keyboard_devices() -> list[str]:
    """Prefer devices with 'keyboard' in name; fallback to those exposing A..Z."""
    paths = []
    for p in list_devices():
        try:
            dev = InputDevice(p)
            if "keyboard" in (dev.name or "").lower():
                paths.append(p)
        except Exception:
            pass
    if paths:
        print("[INFO] Keyboard devices:")
        for p in paths:
            try: print(f"   {p}: {InputDevice(p).name}")
            except Exception: print(f"   {p}")
        return paths

    fallback = []
    for p in list_devices():
        try:
            caps = InputDevice(p).capabilities().get(ecodes.EV_KEY, [])
            if ecodes.KEY_A in caps and ecodes.KEY_Z in caps:
                fallback.append(p)
        except Exception:
            pass
    if fallback:
        print("[INFO] Fallback devices (KEY_A..KEY_Z):")
        for p in fallback:
            try: print(f"   {p}: {InputDevice(p).name}")
            except Exception: print(f"   {p}")
        return fallback

    print("[ERROR] No suitable keyboard devices found."); sys.exit(1)

# ──────────────────────────────── App palette (optional; avoid overriding QSS) ────────────────────────────────
def apply_dark_palette(app: QApplication):
    pal = QPalette()
    setc = pal.setColor
    setc(role('Window'),          QColor(10, 10, 10))
    setc(role('AlternateBase'),   QColor(16, 16, 16))
    setc(role('Base'),            QColor(16, 16, 16))
    setc(role('WindowText'),      QColor(235, 235, 235))
    setc(role('Text'),            QColor(235, 235, 235))
    setc(role('Button'),          QColor(12, 12, 12))
    setc(role('ButtonText'),      QColor(235, 235, 235))
    setc(role('Highlight'),       QColor(80, 120, 255))
    setc(role('HighlightedText'), QColor(0, 0, 0))
    app.setPalette(pal)

# ──────────────────────────────── Parse CLI theme ────────────────────────────────
def resolve_theme() -> str:
    # 1) CLI flag
    for arg in sys.argv[1:]:
        if arg.startswith("--theme="):
            t = arg.split("=", 1)[1].strip().lower()
            if t in THEMES:
                print(f"[THEME] Using '{t}' (from CLI)")
                return t
            print(f"[WARN] Theme '{t}' not found. Available: {', '.join(THEMES)}")
            return DEFAULT_THEME

    # 2) Environment variable
    t_env = os.environ.get("OSD_THEME", "").strip().lower()
    if t_env:
        if t_env in THEMES:
            print(f"[THEME] Using '{t_env}' (from env OSD_THEME)")
            return t_env
        print(f"[WARN] OSD_THEME '{t_env}' not recognized. Available: {', '.join(THEMES)}")

    # 3) Config files (first hit wins)
    cfg_candidates = []
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        cfg_candidates += [
            os.path.join(xdg, "osd.conf"),
            os.path.join(xdg, "volume-osd", "osd.conf"),
        ]
    home_cfg = os.path.expanduser("~/.config")
    cfg_candidates += [
        os.path.join(home_cfg, "osd.conf"),
        os.path.join(home_cfg, "volume-osd", "osd.conf"),
    ]

    for path in cfg_candidates:
        try:
            with open(path) as f:
                for raw in f:
                    s = raw.strip()
                    if not s or s.startswith("#"):
                        continue
                    if s.startswith("theme="):
                        t = s.split("=", 1)[1].strip().lower()
                        if t in THEMES:
                            print(f"[THEME] Using '{t}' (from {path})")
                            return t
                        print(f"[WARN] Theme '{t}' in {path} not recognized. Available: {', '.join(THEMES)}")
                        break
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"[WARN] Failed reading {path}: {e}")

    # 4) Fallback
    print(f"[THEME] Using '{DEFAULT_THEME}' (default)")
    return DEFAULT_THEME

# ──────────────────────────────── Main ────────────────────────────────
def main():
    kb_paths = find_keyboard_devices()

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))

    # If you really want a base palette, apply it BEFORE theming and be aware it can affect colors.
    # For strict theming via QSS, keep this disabled:
    # apply_dark_palette(app)

    theme = resolve_theme()
    osd = VolumeOSD(step=5, theme=theme)

    signals = VolumeSignals()
    signals.increase.connect(osd.increase_volume)
    signals.decrease.connect(osd.decrease_volume)
    signals.mute.connect(osd.toggle_mute)

    mods = ModifierState()
    rate = RateLimiter(incdec=0.08, mute=0.20)  # tune repeats here

    for path in kb_paths:
        threading.Thread(target=read_keyboard_events, args=(signals, path, mods, rate), daemon=True).start()

    sys.exit(app.exec() if USING_QT6 else app.exec_())

if __name__ == "__main__":
    main()
