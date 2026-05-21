"""Standalone FUTEK force sensor reader with COM port discovery and live plot."""

import sys
import os
import time

import numpy as np
import pyqtgraph as pg
import serial.tools.list_ports

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QLineEdit,
    QSizePolicy,
)

sys.path.insert(0, os.path.dirname(__file__))

PLOT_HISTORY_S = 10.0  # seconds of history shown in the live plot
UPDATE_INTERVAL_MS = 100  # UI refresh interval

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

        root.addWidget(self._build_connection_group())
        root.addWidget(self._build_reading_group())
        root.addWidget(self._build_plot_widget(), stretch=1)

        self.status_label = QLabel("Not connected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: grey; font-style: italic;")
        root.addWidget(self.status_label)

        self._timer = QTimer()
        self._timer.setInterval(UPDATE_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer)

        self._refresh_ports()

    # ── builders ──────────────────────────────────────────────────────────────

    def _build_connection_group(self) -> QGroupBox:
        group = QGroupBox("Connection")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        # COM port row (informational — shows what USB/serial devices are visible)
        com_row = QHBoxLayout()
        com_row.addWidget(QLabel("COM Port:"))
        self.com_combo = QComboBox()
        self.com_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        com_row.addWidget(self.com_combo, 1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(70)
        refresh_btn.clicked.connect(self._refresh_ports)
        com_row.addWidget(refresh_btn)
        layout.addLayout(com_row)

        # FUTEK serial-number row
        sn_row = QHBoxLayout()
        sn_row.addWidget(QLabel("Device Serial #:"))
        self.sn_edit = QLineEdit("725662")
        self.sn_edit.setPlaceholderText("e.g. 725662")
        self.sn_edit.setFixedWidth(120)
        sn_row.addWidget(self.sn_edit)
        sn_row.addStretch()
        layout.addLayout(sn_row)

        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedHeight(34)
        self.connect_btn.clicked.connect(self._toggle_connection)
        layout.addWidget(self.connect_btn)

        return group

    def _build_reading_group(self) -> QGroupBox:
        group = QGroupBox("Force Reading")
        layout = QVBoxLayout(group)

        self.force_label = QLabel("—")
        self.force_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.force_label.setStyleSheet(
            "font-size: 52px; font-weight: bold; color: #2196F3;"
        )
        layout.addWidget(self.force_label)

        self.unit_label = QLabel("mN")
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unit_label.setStyleSheet("font-size: 18px; color: #555;")
        layout.addWidget(self.unit_label)

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

    def _build_plot_widget(self) -> QWidget:
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Force", units="mN")
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen("#2196F3", width=2))
        self.plot_widget.setMinimumHeight(180)
        return self.plot_widget

    # ── port discovery ────────────────────────────────────────────────────────

    def _refresh_ports(self):
        self.com_combo.clear()
        ports = sorted(serial.tools.list_ports.comports(), key=lambda p: p.device)
        if ports:
            for p in ports:
                label = f"{p.device}  —  {p.description}"
                self.com_combo.addItem(label, p.device)
        else:
            self.com_combo.addItem("No serial ports found")

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

        self.sensor.start_recording()
        self._start_time = time.perf_counter()
        self._timer.start()

        self.connect_btn.setText("Disconnect")
        self.tare_btn.setEnabled(True)
        self._set_status(
            f"Connected  |  Capacity: {self.sensor.sensor_capacity:.1f} mN"
            f"  |  FW: {self.sensor.firmware_version}"
        )
        self.info_label.setText(
            f"S/N: {serial_number}   Capacity: {self.sensor.sensor_capacity:.1f} mN"
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

    def _on_timer(self):
        if self.sensor is None or not self.sensor.is_connected:
            return

        if self.sensor.sample < 1:
            return

        # Current value display
        force = self.sensor.get_current_force()
        self.force_label.setText(f"{force:+.2f}")

        # Plot update
        t_all, f_all = self.sensor.get_buffer()
        if len(t_all) == 0:
            return
        t_rel = t_all - self._start_time
        t_last = t_rel[-1]
        mask = t_rel >= t_last - PLOT_HISTORY_S
        self.plot_curve.setData(t_rel[mask], f_all[mask])

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
