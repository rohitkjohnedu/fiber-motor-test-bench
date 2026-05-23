"""
Standalone FUTEK force sensor reader with live plot — dual-sensor version.

Provides a PyQt6 GUI that can connect to two FUTEK IPM650 USB force-measurement
amplifiers simultaneously. The Readout tab shows live force readings and rolling
plots for both sensors; the Raw Data tab shows device register dumps.

Hardware chain:
    LRF400 load cell → IPM650 amplifier → USB → FUTEK_USB_DLL.dll
    → pythonnet (clr) → ForceSensor.FutekSensor → this module.

Usage::

    python futek_reader.py
"""

import sys
import os
import time
from typing import Optional

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QLineEdit,
    QTextEdit, QTabWidget, QSplitter,
)

sys.path.insert(0, os.path.dirname(__file__))

# Rolling window of history shown in the live force plot.
PLOT_HISTORY_S: float = 10.0

# How often (ms) the QTimer fires to refresh the force display and plot.
UPDATE_INTERVAL_MS: int = 100

# Scale factors to convert the internal mN value to each display unit.
DISPLAY_UNITS: dict[str, float] = {
    "mN":  1.0,
    "N":   1e-3,
    "gf":  1.0 / 9.80665,
    "lb":  1.0 / 4448.2216,
}

# Inverse of DISPLAY_UNITS: multiply a value in the given unit to get mN.
CAPACITY_UNITS_TO_MN: dict[str, float] = {u: 1.0 / s for u, s in DISPLAY_UNITS.items()}

# ──────────────────────────────────────────────────────────────────────────────


class SensorPanel:
    """
    All state, logic, and composable widgets for one IPM650 sensor connection.

    Exposes two QGroupBox widgets that the main window places in separate tabs:

    ``readout_widget``
        Outer group box titled with ``name``. Contains a top row of
        [Connection group | Force Reading group] and a rolling plot below.

    ``registers_widget``
        Group box titled ``"<name> — Device Registers"``. Contains a read-only
        text dump of raw device registers, populated once on connect (before the
        background polling thread starts to avoid DLL thread-safety issues).
    """

    def __init__(self, name: str, default_sn: str = "") -> None:
        self.name = name
        self.sensor: Optional[object] = None
        self._start_time: Optional[float] = None

        self._timer = QTimer()
        self._timer.setInterval(UPDATE_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer)

        conn_grp     = self._build_connection_group(default_sn)
        reading_grp  = self._build_reading_group()
        plot_wgt     = self._build_plot_widget()
        self.registers_widget = self._build_registers_group()

        # Readout widget: outer group box that lives in the Readout tab.
        self.readout_widget = QGroupBox(name)
        outer = QVBoxLayout(self.readout_widget)

        top_row = QHBoxLayout()
        top_row.addWidget(conn_grp)
        top_row.addWidget(reading_grp, stretch=1)
        outer.addLayout(top_row)
        outer.addWidget(plot_wgt, stretch=1)

        self.status_label = QLabel("Not connected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: grey; font-style: italic;")
        outer.addWidget(self.status_label)

    # ── widget builders ───────────────────────────────────────────────────────

    def _build_connection_group(self, default_sn: str) -> QGroupBox:
        group  = QGroupBox("Connection")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        sn_row = QHBoxLayout()
        sn_row.addWidget(QLabel("Device Serial #:"))
        self.sn_edit = QLineEdit(default_sn)
        self.sn_edit.setPlaceholderText("e.g. 725662")
        self.sn_edit.setFixedWidth(120)
        sn_row.addWidget(self.sn_edit)
        sn_row.addStretch()
        layout.addLayout(sn_row)

        cap_row = QHBoxLayout()
        cap_row.addWidget(QLabel("Capacity:"))
        self.capacity_edit = QLineEdit()
        self.capacity_edit.setPlaceholderText("auto")
        self.capacity_edit.setFixedWidth(90)
        self.capacity_edit.setToolTip(
            "Auto-filled on connect. Override if the detected value is wrong\n"
            "(e.g. IPM650 stores capacity in wrong units)."
        )
        self.capacity_edit.editingFinished.connect(self._on_capacity_edited)
        cap_row.addWidget(self.capacity_edit)

        self.capacity_unit_combo = QComboBox()
        for u in CAPACITY_UNITS_TO_MN:
            self.capacity_unit_combo.addItem(u)
        self.capacity_unit_combo.setFixedWidth(60)
        self.capacity_unit_combo.currentTextChanged.connect(self._on_capacity_edited)
        cap_row.addWidget(self.capacity_unit_combo)
        cap_row.addStretch()
        layout.addLayout(cap_row)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedHeight(34)
        self.connect_btn.clicked.connect(self._toggle_connection)
        layout.addWidget(self.connect_btn)

        return group

    def _build_reading_group(self) -> QGroupBox:
        group      = QGroupBox("Force Reading")
        outer_row  = QHBoxLayout(group)  # readout content left, unit combo right

        # ── left: readout labels + info + tare ───────────────────────────────
        left = QVBoxLayout()

        cap_style = "font-size: 28px; font-weight: bold; color: #e74c3c; padding: 0 8px;"

        reading_row = QHBoxLayout()

        self.cap_min_label = QLabel("—")
        self.cap_min_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.cap_min_label.setStyleSheet(cap_style)
        reading_row.addWidget(self.cap_min_label)

        self.force_label = QLabel("—")
        self.force_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.force_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2196F3;")
        reading_row.addWidget(self.force_label, stretch=1)

        self.cap_max_label = QLabel("—")
        self.cap_max_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cap_max_label.setStyleSheet(cap_style)
        reading_row.addWidget(self.cap_max_label)
        left.addLayout(reading_row)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 11px; color: #888;")
        left.addWidget(self.info_label)

        self.tare_btn = QPushButton("Tare")
        self.tare_btn.setFixedHeight(30)
        self.tare_btn.setEnabled(False)
        self.tare_btn.clicked.connect(self._tare)
        left.addWidget(self.tare_btn)

        outer_row.addLayout(left, stretch=1)

        # ── right: unit selector, vertically centred ─────────────────────────
        self.unit_combo = QComboBox()
        for u in DISPLAY_UNITS:
            self.unit_combo.addItem(u)
        self.unit_combo.setFixedWidth(70)
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        outer_row.addWidget(self.unit_combo, alignment=Qt.AlignmentFlag.AlignVCenter)

        return group

    def _build_registers_group(self) -> QGroupBox:
        group  = QGroupBox(f"{self.name} — Device Registers")
        layout = QVBoxLayout(group)
        self.registers_display = QTextEdit()
        self.registers_display.setReadOnly(True)
        self.registers_display.setFont(QFont("Courier New", 9))
        self.registers_display.setPlaceholderText("Connect to a device to see register values.")
        layout.addWidget(self.registers_display)
        return group

    def _build_plot_widget(self) -> pg.PlotWidget:
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Force", units=next(iter(DISPLAY_UNITS)))
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen("#2196F3", width=2))
        self.plot_widget.setMinimumHeight(180)
        return self.plot_widget

    # ── connection management ─────────────────────────────────────────────────

    def _toggle_connection(self) -> None:
        if self.sensor is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self) -> None:
        serial_number: str = self.sn_edit.text().strip()
        if not serial_number:
            self._set_status("Enter a device serial number first.", error=True)
            return

        self._set_status("Connecting …")
        QApplication.processEvents()

        try:
            from ForceSensor import FutekSensor
            self.sensor = FutekSensor(serial_number=serial_number)
        except Exception as exc:
            self.sensor = None
            self._set_status(f"Import error: {exc}", error=True)
            return

        if not self.sensor.is_connected:
            self.sensor = None
            self._set_status("Connection failed — check serial number and USB cable.", error=True)
            return

        # Register read must happen before start_recording() — DLL is not
        # thread-safe while the background polling thread is running.
        self._update_registers()

        self.sensor.start_recording()
        self._start_time = time.perf_counter()
        self._timer.start()

        self.connect_btn.setText("Disconnect")
        self.tare_btn.setEnabled(True)
        self.capacity_edit.setText(f"{self.sensor.sensor_capacity:.4g}")
        self.capacity_unit_combo.setCurrentText("mN")
        self._update_capacity_labels()
        self._set_status(
            f"Connected  |  IPM650 S/N: {self.sensor.device_sn}"
            f"  |  Capacity: {self.sensor.sensor_capacity:.1f} mN"
            f"  |  FW: {self.sensor.firmware_version}"
        )
        self.info_label.setText(
            f"IPM650 S/N: {self.sensor.device_sn}   LRF400 S/N: {self.sensor.sensor_id}"
            f"   Capacity: {self.sensor.sensor_capacity:.1f} mN"
        )

    def _disconnect(self) -> None:
        self._timer.stop()
        if self.sensor is not None:
            self.sensor.disconnect()
            self.sensor = None

        self.connect_btn.setText("Connect")
        self.tare_btn.setEnabled(False)
        self.force_label.setText("—")
        self.info_label.setText("")
        self.registers_display.clear()
        self._update_capacity_labels()
        self.plot_curve.setData([], [])
        self._set_status("Disconnected")

    def _tare(self) -> None:
        if self.sensor and self.sensor.is_connected:
            self.tare_btn.setEnabled(False)
            self.tare_btn.setText("Taring …")
            QApplication.processEvents()
            self.sensor.tare()
            self.tare_btn.setText("Tare")
            self.tare_btn.setEnabled(True)

    # ── live data & UI updates ────────────────────────────────────────────────

    def _update_registers(self) -> None:
        try:
            from ForceSensor.futek import FUTEK_UNITS_CODE
            from ForceSensor import FutekSensor as _FS

            s:   object = self.sensor
            dll: object = s.futek_dll
            h:   object = s.device_handle

            with _FS.dll_lock:
                reg5_raw = dll.Get_Internal_Register(h, 5)
                reg6_raw = dll.Get_Internal_Register(h, 6)
            reg5: int = int(reg5_raw)
            reg6: int = int(reg6_raw)

            dp: int = reg6 >> 16
            uc: int = (reg6 & 0xFF00) >> 8
            dc: int = reg6 & 0xFF

            unit_name: str = FUTEK_UNITS_CODE[uc]["unit_name"] if uc in FUTEK_UNITS_CODE else "unknown"
            conv: float    = FUTEK_UNITS_CODE[uc]["conversion_to_mN"] if uc in FUTEK_UNITS_CODE else 1.0
            raw_cap: float = reg5 * 10 ** (-dp)
            cap_mn: float  = raw_cap * conv * (1 if dc else -1)

            lines: list[str] = [
                f"{'Firmware:':<14}{s.firmware_version:<12}  {'Board type:':<14}{s.board_type}",
                f"{'IPM650 S/N:':<14}{s.device_sn:<12}  {'Sensor ID:':<14}{s.sensor_id}",
                "",
                f"{'Register':<10}{'Value':>12}    Description",
                "-" * 52,
                f"{'Reg 1':<10}{s.tare_register_value:>12,.0f}    Tare register",
                f"{'Reg 2':<10}{s.offset:>12,.0f}    Zero (offset)",
                f"{'Reg 3':<10}{s.fullscale_value:>12,.0f}    Full scale",
                f"{'Reg 5':<10}{reg5:>12,}    Capacity raw value",
                f"{'Reg 6':<10}{reg6:>12,}    Capacity details:",
                f"{'':10}{'':>12}      decimal_point = {dp}  (x 10^-{dp})",
                f"{'':10}{'':>12}      unit_code     = {uc}  ({unit_name}, x{conv} mN)",
                f"{'':10}{'':>12}      direction     = {dc}  ({'positive' if dc else 'negative'})",
                "",
                f"Computed: {reg5} x 10^-{dp} x {conv} = {cap_mn:.4g} mN",
            ]
            self.registers_display.setPlainText("\n".join(lines))
        except Exception as exc:
            self.registers_display.setPlainText(f"Error reading registers:\n{exc}")

    def _on_capacity_edited(self) -> None:
        text: str = self.capacity_edit.text().strip()
        if not text or self.sensor is None:
            return

        try:
            value: float = float(text)
        except ValueError:
            self.capacity_edit.setText(f"{self.sensor.sensor_capacity:.4g}")
            return

        unit: str          = self.capacity_unit_combo.currentText()
        capacity_mn: float = value * CAPACITY_UNITS_TO_MN[unit]
        self.sensor.set_sensor_range(capacity_mn)
        self._update_capacity_labels()
        self.info_label.setText(
            f"IPM650 S/N: {self.sensor.device_sn}   LRF400 S/N: {self.sensor.sensor_id}"
            f"   Capacity: {value:.4g} {unit}  ({capacity_mn:.1f} mN)"
        )

    def _update_capacity_labels(self) -> None:
        if self.sensor is None:
            self.cap_min_label.setText("—")
            self.cap_max_label.setText("—")
            return

        scale: float = DISPLAY_UNITS[self.unit_combo.currentText()]
        unit: str    = self.unit_combo.currentText()
        cap: float   = self.sensor.sensor_capacity * scale
        self.cap_min_label.setText(f"{-cap:.4g} {unit}")
        self.cap_max_label.setText(f"+{cap:.4g} {unit}")

    def _on_unit_changed(self, unit: str) -> None:
        self.plot_widget.setLabel("left", "Force", units=unit)
        self._update_capacity_labels()

    def _on_timer(self) -> None:
        if self.sensor is None or not self.sensor.is_connected:
            return
        if self.sensor.sample < 1:
            return

        scale: float = DISPLAY_UNITS[self.unit_combo.currentText()]

        force: float = self.sensor.get_current_force() * scale
        self.force_label.setText(f"{force:+.4f} {self.unit_combo.currentText()}")

        t_all: np.ndarray
        f_all: np.ndarray
        t_all, f_all = self.sensor.get_buffer()
        if len(t_all) == 0:
            return

        t_rel: np.ndarray = t_all - self._start_time
        t_last: float     = t_rel[-1]
        mask: np.ndarray  = t_rel >= t_last - PLOT_HISTORY_S
        self.plot_curve.setData(t_rel[mask], f_all[mask] * scale)

    def _set_status(self, msg: str, error: bool = False) -> None:
        color: str = "#c0392b" if error else "#27ae60" if "Connected" in msg else "grey"
        self.status_label.setStyleSheet(f"color: {color}; font-style: italic;")
        self.status_label.setText(msg)

    def cleanup(self) -> None:
        self._disconnect()


# ──────────────────────────────────────────────────────────────────────────────


class FutekReaderWindow(QWidget):
    """
    Main application window hosting two SensorPanel instances.

    Readout tab
        Two sensor panels in a vertical QSplitter. Each panel shows
        [Connection | Force Reading] side-by-side on top, with a rolling
        force plot spanning the full width below.

    Raw Data tab
        Device register dumps for both sensors placed side by side.
    """

    def __init__(self) -> None:
        super().__init__()

        # Must be set before any PlotWidget is created.
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        self.setWindowTitle("FUTEK Sensor Reader")
        self.setMinimumSize(900, 750)

        self.sensor1 = SensorPanel("Sensor 1", default_sn="725662")
        self.sensor2 = SensorPanel("Sensor 2")

        root = QVBoxLayout(self)
        root.setSpacing(8)

        tabs = QTabWidget()
        root.addWidget(tabs, stretch=1)

        # ── Readout tab ──────────────────────────────────────────────────────
        readout_tab = QWidget()
        readout_layout = QVBoxLayout(readout_tab)
        readout_layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.sensor1.readout_widget)
        splitter.addWidget(self.sensor2.readout_widget)
        splitter.setSizes([500, 500])

        readout_layout.addWidget(splitter)
        tabs.addTab(readout_tab, "Readout")

        # ── Raw Data tab ─────────────────────────────────────────────────────
        raw_tab = QWidget()
        raw_layout = QHBoxLayout(raw_tab)
        raw_layout.addWidget(self.sensor1.registers_widget)
        raw_layout.addWidget(self.sensor2.registers_widget)
        tabs.addTab(raw_tab, "Raw Data")

    def closeEvent(self, event) -> None:
        self.sensor1.cleanup()
        self.sensor2.cleanup()
        super().closeEvent(event)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    app.setStyle("Fusion")
    window: FutekReaderWindow = FutekReaderWindow()
    window.show()
    sys.exit(app.exec())
