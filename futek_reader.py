"""Standalone FUTEK force sensor reader with live plot."""

import sys
import os
import time

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QLineEdit,
    QTextEdit,
)

sys.path.insert(0, os.path.dirname(__file__))

PLOT_HISTORY_S = 10.0  # seconds of history shown in the live plot
UPDATE_INTERVAL_MS = 100  # UI refresh interval

DISPLAY_UNITS = {
    "mN":  1.0,
    "N":   1e-3,
    "gf":  1.0 / 9.80665,
    "lb":  1.0 / 4448.2216,
}

# Conversion factors from each unit to mN (inverse of DISPLAY_UNITS)
CAPACITY_UNITS_TO_MN = {u: 1.0 / s for u, s in DISPLAY_UNITS.items()}

# ──────────────────────────────────────────────────────────────────────────────

class FutekReaderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.sensor = None
        self._start_time = None

        self.setWindowTitle("FUTEK Sensor Reader")
        self.setMinimumSize(480, 600)

        root = QVBoxLayout(self)
        root.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.addWidget(self._build_connection_group())
        top_row.addWidget(self._build_registers_group(), stretch=1)
        root.addLayout(top_row)
        root.addWidget(self._build_reading_group())
        root.addWidget(self._build_plot_widget(), stretch=1)

        self.status_label = QLabel("Not connected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: grey; font-style: italic;")
        root.addWidget(self.status_label)

        self._timer = QTimer()
        self._timer.setInterval(UPDATE_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer)

    # ── builders ──────────────────────────────────────────────────────────────

    def _build_connection_group(self) -> QGroupBox:
        group = QGroupBox("Connection")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        # FUTEK serial-number row
        sn_row = QHBoxLayout()
        sn_row.addWidget(QLabel("Device Serial #:"))
        self.sn_edit = QLineEdit("725662")
        self.sn_edit.setPlaceholderText("e.g. 725662")
        self.sn_edit.setFixedWidth(120)
        sn_row.addWidget(self.sn_edit)
        sn_row.addStretch()
        layout.addLayout(sn_row)

        # Capacity override row
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

        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedHeight(34)
        self.connect_btn.clicked.connect(self._toggle_connection)
        layout.addWidget(self.connect_btn)

        return group

    def _build_reading_group(self) -> QGroupBox:
        group = QGroupBox("Force Reading")
        layout = QVBoxLayout(group)

        cap_style = "font-size: 52px; font-weight: bold; color: #e74c3c; padding: 0 8px;"
        reading_row = QHBoxLayout()
        self.cap_min_label = QLabel("—")
        self.cap_min_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.cap_min_label.setStyleSheet(cap_style)
        reading_row.addWidget(self.cap_min_label)

        self.force_label = QLabel("—")
        self.force_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.force_label.setStyleSheet(
            "font-size: 52px; font-weight: bold; color: #2196F3;"
        )
        reading_row.addWidget(self.force_label, stretch=1)

        self.cap_max_label = QLabel("—")
        self.cap_max_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cap_max_label.setStyleSheet(cap_style)
        reading_row.addWidget(self.cap_max_label)
        layout.addLayout(reading_row)

        unit_row = QHBoxLayout()
        unit_row.addStretch()
        self.unit_combo = QComboBox()
        for u in DISPLAY_UNITS:
            self.unit_combo.addItem(u)
        self.unit_combo.setFixedWidth(70)
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        unit_row.addWidget(self.unit_combo)
        unit_row.addStretch()
        layout.addLayout(unit_row)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.info_label)

        self.tare_btn = QPushButton("Tare")
        self.tare_btn.setFixedHeight(30)
        self.tare_btn.setEnabled(False)
        self.tare_btn.clicked.connect(self._tare)
        layout.addWidget(self.tare_btn)

        return group

    def _build_registers_group(self) -> QGroupBox:
        group = QGroupBox("Device Registers")
        layout = QVBoxLayout(group)
        self.registers_display = QTextEdit()
        self.registers_display.setReadOnly(True)
        self.registers_display.setFont(QFont("Courier New", 9))
        self.registers_display.setPlaceholderText("Connect to a device to see register values.")
        layout.addWidget(self.registers_display)
        return group

    def _build_plot_widget(self) -> QWidget:
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Force", units=next(iter(DISPLAY_UNITS)))
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen("#2196F3", width=2))
        self.plot_widget.setMinimumHeight(180)
        return self.plot_widget

    # ── connection ────────────────────────────────────────────────────────────

    def _toggle_connection(self):
        if self.sensor is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self):
        serial_number = self.sn_edit.text().strip()
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

    def _disconnect(self):
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

    def _tare(self):
        if self.sensor and self.sensor.is_connected:
            self.tare_btn.setEnabled(False)
            self.tare_btn.setText("Taring …")
            QApplication.processEvents()
            self.sensor.tare()
            self.tare_btn.setText("Tare")
            self.tare_btn.setEnabled(True)

    # ── live update ───────────────────────────────────────────────────────────

    def _update_registers(self):
        try:
            from ForceSensor.futek import FUTEK_UNITS_CODE
            s   = self.sensor
            dll = s.futek_dll
            h   = s.device_handle

            reg5_raw = dll.Get_Internal_Register(h, 5)
            reg6_raw = dll.Get_Internal_Register(h, 6)
            reg5 = int(reg5_raw)
            reg6 = int(reg6_raw)

            dp = reg6 >> 16
            uc = (reg6 & 0xFF00) >> 8
            dc = reg6 & 0xFF
            unit_name = FUTEK_UNITS_CODE[uc]["unit_name"] if uc in FUTEK_UNITS_CODE else "unknown"
            conv      = FUTEK_UNITS_CODE[uc]["conversion_to_mN"] if uc in FUTEK_UNITS_CODE else 1.0
            raw_cap   = reg5 * 10 ** (-dp)
            cap_mn    = raw_cap * conv * (1 if dc else -1)

            lines = [
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

    def _on_capacity_edited(self):
        text = self.capacity_edit.text().strip()
        if not text or self.sensor is None:
            return
        try:
            value = float(text)
        except ValueError:
            self.capacity_edit.setText(f"{self.sensor.sensor_capacity:.4g}")
            return
        unit = self.capacity_unit_combo.currentText()
        capacity_mn = value * CAPACITY_UNITS_TO_MN[unit]
        self.sensor.set_sensor_range(capacity_mn)
        self._update_capacity_labels()
        self.info_label.setText(
            f"IPM650 S/N: {self.sensor.device_sn}   LRF400 S/N: {self.sensor.sensor_id}"
            f"   Capacity: {value:.4g} {unit}  ({capacity_mn:.1f} mN)"
        )

    def _update_capacity_labels(self):
        if self.sensor is None:
            self.cap_min_label.setText("—")
            self.cap_max_label.setText("—")
            return
        scale = DISPLAY_UNITS[self.unit_combo.currentText()]
        unit  = self.unit_combo.currentText()
        cap   = self.sensor.sensor_capacity * scale
        self.cap_min_label.setText(f"{-cap:.4g} {unit}")
        self.cap_max_label.setText(f"+{cap:.4g} {unit}")

    def _on_unit_changed(self, unit: str):
        self.plot_widget.setLabel("left", "Force", units=unit)
        self._update_capacity_labels()

    def _on_timer(self):
        if self.sensor is None or not self.sensor.is_connected:
            return

        if self.sensor.sample < 1:
            return

        scale = DISPLAY_UNITS[self.unit_combo.currentText()]

        # Current value display
        force = self.sensor.get_current_force() * scale
        self.force_label.setText(f"{force:+.4f} {self.unit_combo.currentText()}")

        # Plot update
        t_all, f_all = self.sensor.get_buffer()
        if len(t_all) == 0:
            return
        t_rel = t_all - self._start_time
        t_last = t_rel[-1]
        mask = t_rel >= t_last - PLOT_HISTORY_S
        self.plot_curve.setData(t_rel[mask], f_all[mask] * scale)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, error: bool = False):
        color = "#c0392b" if error else "#27ae60" if "Connected" in msg else "grey"
        self.status_label.setStyleSheet(f"color: {color}; font-style: italic;")
        self.status_label.setText(msg)

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FutekReaderWindow()
    window.show()
    sys.exit(app.exec())
