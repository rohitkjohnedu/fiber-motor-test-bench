"""
Standalone FUTEK force sensor reader with live plot.

Provides a PyQt6 GUI that connects to a FUTEK IPM650 USB force-measurement
amplifier (paired with an LRF400 load cell), reads force data in real-time,
displays a rolling live plot, and exposes raw device register values for
diagnostics.

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
    QTextEdit,
)

sys.path.insert(0, os.path.dirname(__file__))

# Rolling window of history shown in the live force plot.
PLOT_HISTORY_S: float = 10.0

# How often (ms) the QTimer fires to refresh the force display and plot.
UPDATE_INTERVAL_MS: int = 100

# Scale factors to convert the internal mN value to each display unit.
# Keys are unit labels; values multiply mN to produce the display unit.
DISPLAY_UNITS: dict[str, float] = {
    "mN":  1.0,
    "N":   1e-3,
    "gf":  1.0 / 9.80665,
    "lb":  1.0 / 4448.2216,
}

# Inverse of DISPLAY_UNITS: multiply a value in the given unit by this factor
# to get millinewtons. Used when the user overrides sensor capacity.
CAPACITY_UNITS_TO_MN: dict[str, float] = {u: 1.0 / s for u, s in DISPLAY_UNITS.items()}

# ──────────────────────────────────────────────────────────────────────────────


class FutekReaderWindow(QWidget):
    """
    Main application window for the standalone FUTEK sensor reader.

    Responsibilities:
    - Let the user enter an IPM650 serial number and connect / disconnect.
    - Display raw device registers (populated before the polling thread starts
      to avoid DLL thread-safety issues).
    - Show the live force reading in a selectable unit with ± capacity limits.
    - Render a rolling pyqtgraph live plot of the last PLOT_HISTORY_S seconds.
    - Expose a Tare button that zero-offsets subsequent readings.

    The sensor backend is ``ForceSensor.FutekSensor``, loaded lazily on connect
    so that the GUI starts even when the FUTEK DLL is absent.
    """

    # ── construction ──────────────────────────────────────────────────────────

    def __init__(self) -> None:
        """
        Initialise the window, build all child widgets, and wire the QTimer.

        The sensor is not connected here; the user presses "Connect" to do so.
        """
        super().__init__()

        # Active FutekSensor instance; None when disconnected.
        self.sensor: Optional[object] = None

        # Wall-clock timestamp (perf_counter) captured at sensor start, used to
        # compute relative time for the plot x-axis.
        self._start_time: Optional[float] = None

        self.setWindowTitle("FUTEK Sensor Reader")
        self.setMinimumSize(480, 600)

        root: QVBoxLayout = QVBoxLayout(self)
        root.setSpacing(8)

        top_row: QHBoxLayout = QHBoxLayout()
        top_row.addWidget(self._build_connection_group())
        top_row.addWidget(self._build_registers_group(), stretch=1)
        root.addLayout(top_row)
        root.addWidget(self._build_reading_group())
        root.addWidget(self._build_plot_widget(), stretch=1)

        self.status_label: QLabel = QLabel("Not connected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: grey; font-style: italic;")
        root.addWidget(self.status_label)

        # Periodic timer that drives UI refresh; started only while connected.
        self._timer: QTimer = QTimer()
        self._timer.setInterval(UPDATE_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer)

    # ── widget builders ───────────────────────────────────────────────────────

    def _build_connection_group(self) -> QGroupBox:
        """
        Build the "Connection" group box.

        Contains:
        - A serial-number ``QLineEdit`` for the IPM650 device.
        - A capacity override row (value + unit) that maps to
          ``sensor.set_sensor_range()`` in mN.
        - A Connect / Disconnect toggle button.

        Returns:
            The fully populated QGroupBox widget.
        """
        group: QGroupBox = QGroupBox("Connection")
        layout: QVBoxLayout = QVBoxLayout(group)
        layout.setSpacing(6)

        # Row: device serial number entry
        sn_row: QHBoxLayout = QHBoxLayout()
        sn_row.addWidget(QLabel("Device Serial #:"))
        self.sn_edit: QLineEdit = QLineEdit("725662")
        self.sn_edit.setPlaceholderText("e.g. 725662")
        self.sn_edit.setFixedWidth(120)
        sn_row.addWidget(self.sn_edit)
        sn_row.addStretch()
        layout.addLayout(sn_row)

        # Row: sensor capacity override — auto-filled on connect; editable
        # because some IPM650 firmware versions store capacity in unexpected
        # units (e.g. unit_code mismatch in register 6).
        cap_row: QHBoxLayout = QHBoxLayout()
        cap_row.addWidget(QLabel("Capacity:"))
        self.capacity_edit: QLineEdit = QLineEdit()
        self.capacity_edit.setPlaceholderText("auto")
        self.capacity_edit.setFixedWidth(90)
        self.capacity_edit.setToolTip(
            "Auto-filled on connect. Override if the detected value is wrong\n"
            "(e.g. IPM650 stores capacity in wrong units)."
        )
        self.capacity_edit.editingFinished.connect(self._on_capacity_edited)
        cap_row.addWidget(self.capacity_edit)

        # Unit selector for the capacity field — independent of the display unit.
        self.capacity_unit_combo: QComboBox = QComboBox()
        for u in CAPACITY_UNITS_TO_MN:
            self.capacity_unit_combo.addItem(u)
        self.capacity_unit_combo.setFixedWidth(60)
        self.capacity_unit_combo.currentTextChanged.connect(self._on_capacity_edited)
        cap_row.addWidget(self.capacity_unit_combo)
        cap_row.addStretch()
        layout.addLayout(cap_row)

        self.connect_btn: QPushButton = QPushButton("Connect")
        self.connect_btn.setFixedHeight(34)
        self.connect_btn.clicked.connect(self._toggle_connection)
        layout.addWidget(self.connect_btn)

        return group

    def _build_reading_group(self) -> QGroupBox:
        """
        Build the "Force Reading" group box.

        Contains:
        - A large blue centre label showing the current force value with unit.
        - Two red flanking labels showing ± sensor capacity in the current unit.
        - A unit selector ``QComboBox`` (mN / N / gf / lb).
        - A small info label with device identification.
        - A Tare button.

        Returns:
            The fully populated QGroupBox widget.
        """
        group: QGroupBox = QGroupBox("Force Reading")
        layout: QVBoxLayout = QVBoxLayout(group)

        # Shared style for the ± capacity limit labels.
        cap_style: str = "font-size: 52px; font-weight: bold; color: #e74c3c; padding: 0 8px;"

        reading_row: QHBoxLayout = QHBoxLayout()

        # Left label: negative (minimum) capacity limit.
        self.cap_min_label: QLabel = QLabel("—")
        self.cap_min_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.cap_min_label.setStyleSheet(cap_style)
        reading_row.addWidget(self.cap_min_label)

        # Centre label: live force value; updated every UPDATE_INTERVAL_MS ms.
        self.force_label: QLabel = QLabel("—")
        self.force_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.force_label.setStyleSheet(
            "font-size: 52px; font-weight: bold; color: #2196F3;"
        )
        reading_row.addWidget(self.force_label, stretch=1)

        # Right label: positive (maximum) capacity limit.
        self.cap_max_label: QLabel = QLabel("—")
        self.cap_max_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cap_max_label.setStyleSheet(cap_style)
        reading_row.addWidget(self.cap_max_label)
        layout.addLayout(reading_row)

        unit_row: QHBoxLayout = QHBoxLayout()
        unit_row.addStretch()

        # Display unit selector; changing it rescales the live readout and plot
        # without reconnecting, purely by multiplying by DISPLAY_UNITS[unit].
        self.unit_combo: QComboBox = QComboBox()
        for u in DISPLAY_UNITS:
            self.unit_combo.addItem(u)
        self.unit_combo.setFixedWidth(70)
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        unit_row.addWidget(self.unit_combo)
        unit_row.addStretch()
        layout.addLayout(unit_row)

        # Secondary info line: device identifiers and capacity summary.
        self.info_label: QLabel = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.info_label)

        self.tare_btn: QPushButton = QPushButton("Tare")
        self.tare_btn.setFixedHeight(30)
        self.tare_btn.setEnabled(False)
        self.tare_btn.clicked.connect(self._tare)
        layout.addWidget(self.tare_btn)

        return group

    def _build_registers_group(self) -> QGroupBox:
        """
        Build the "Device Registers" group box.

        The ``QTextEdit`` is read-only and populated once on connect (before the
        background polling thread starts) because calling ``Get_Internal_Register``
        concurrently with the polling thread causes the DLL to return ``'Error'``.

        Returns:
            The fully populated QGroupBox widget.
        """
        group: QGroupBox = QGroupBox("Device Registers")
        layout: QVBoxLayout = QVBoxLayout(group)

        # Monospaced, read-only display for decoded register values.
        self.registers_display: QTextEdit = QTextEdit()
        self.registers_display.setReadOnly(True)
        self.registers_display.setFont(QFont("Courier New", 9))
        self.registers_display.setPlaceholderText("Connect to a device to see register values.")
        layout.addWidget(self.registers_display)

        return group

    def _build_plot_widget(self) -> QWidget:
        """
        Build and configure the pyqtgraph live-force plot.

        Sets a white background / black foreground, adds grid lines, and stores
        the single plot curve (``self.plot_curve``) used for all updates.

        Returns:
            The configured ``pg.PlotWidget`` instance.
        """
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        self.plot_widget: pg.PlotWidget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Force", units=next(iter(DISPLAY_UNITS)))
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Single curve updated in-place on every timer tick; avoids allocating
        # new PlotDataItem objects on each refresh.
        self.plot_curve: pg.PlotDataItem = self.plot_widget.plot(
            pen=pg.mkPen("#2196F3", width=2)
        )
        self.plot_widget.setMinimumHeight(180)

        return self.plot_widget

    # ── connection management ─────────────────────────────────────────────────

    def _toggle_connection(self) -> None:
        """
        Toggle between connected and disconnected state.

        Delegates to ``_connect`` when no sensor is active, or to
        ``_disconnect`` when one is.
        """
        if self.sensor is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self) -> None:
        """
        Attempt to open a connection to the FUTEK IPM650.

        Steps:
        1. Read serial number from ``sn_edit``.
        2. Import and instantiate ``ForceSensor.FutekSensor`` (lazy import so
           the GUI starts even if the DLL is missing).
        3. Read device registers *before* starting the background thread to
           avoid concurrent DLL access issues.
        4. Start ``sensor.start_recording()`` and the QTimer.

        On any failure the sensor reference is cleared and an error status is
        shown rather than propagating the exception.
        """
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

        # Register read must happen here — before start_recording() — because
        # the background DLL polling thread makes Get_Internal_Register unsafe.
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
        """
        Stop the timer, close the sensor connection, and reset all UI elements.

        Safe to call when already disconnected (sensor is None).
        """
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
        """
        Perform a software tare on the connected sensor.

        Disables the Tare button while the blocking ``sensor.tare()`` call runs
        (~50 ms) and re-enables it on return. The sensor zero-offset is reset so
        subsequent readings are relative to the current load.
        """
        if self.sensor and self.sensor.is_connected:
            self.tare_btn.setEnabled(False)
            self.tare_btn.setText("Taring …")
            QApplication.processEvents()
            self.sensor.tare()
            self.tare_btn.setText("Tare")
            self.tare_btn.setEnabled(True)

    # ── live data update ──────────────────────────────────────────────────────

    def _update_registers(self) -> None:
        """
        Read and decode FUTEK device registers 1–6 and display them.

        Called once immediately after connection, *before* ``start_recording()``,
        because the FUTEK DLL is not thread-safe: calling ``Get_Internal_Register``
        while the background polling thread is active returns ``'Error'``.

        Register 6 bit-field layout:
        - bits 31–16: decimal_point  → capacity = reg5 × 10^(-dp)
        - bits 15–8 : unit_code      → looked up in FUTEK_UNITS_CODE for name + mN factor
        - bits  7–0 : direction      → non-zero = positive, zero = negative capacity

        Any exception is caught and shown inline so a register read failure does
        not prevent the rest of the connection sequence from completing.
        """
        try:
            from ForceSensor.futek import FUTEK_UNITS_CODE

            s: object   = self.sensor
            dll: object = s.futek_dll
            h: object   = s.device_handle

            reg5_raw: object = dll.Get_Internal_Register(h, 5)
            reg6_raw: object = dll.Get_Internal_Register(h, 6)
            reg5: int = int(reg5_raw)
            reg6: int = int(reg6_raw)

            # Decode register 6 bit-fields.
            dp: int = reg6 >> 16                       # decimal point exponent
            uc: int = (reg6 & 0xFF00) >> 8             # unit code
            dc: int = reg6 & 0xFF                      # direction flag

            unit_name: str   = FUTEK_UNITS_CODE[uc]["unit_name"] if uc in FUTEK_UNITS_CODE else "unknown"
            conv: float      = FUTEK_UNITS_CODE[uc]["conversion_to_mN"] if uc in FUTEK_UNITS_CODE else 1.0
            raw_cap: float   = reg5 * 10 ** (-dp)
            cap_mn: float    = raw_cap * conv * (1 if dc else -1)

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
        """
        Handle a change to the capacity override field or its unit selector.

        Converts the entered value to mN using ``CAPACITY_UNITS_TO_MN`` and
        calls ``sensor.set_sensor_range(capacity_mN)`` so that the FutekSensor
        backend uses the correct full-scale for ADC-count-to-force conversion.

        If the text is not a valid float the field is reset to the sensor's
        current capacity. Does nothing when disconnected.
        """
        text: str = self.capacity_edit.text().strip()
        if not text or self.sensor is None:
            return

        try:
            value: float = float(text)
        except ValueError:
            # Revert to last known valid capacity.
            self.capacity_edit.setText(f"{self.sensor.sensor_capacity:.4g}")
            return

        unit: str        = self.capacity_unit_combo.currentText()
        capacity_mn: float = value * CAPACITY_UNITS_TO_MN[unit]
        self.sensor.set_sensor_range(capacity_mn)
        self._update_capacity_labels()
        self.info_label.setText(
            f"IPM650 S/N: {self.sensor.device_sn}   LRF400 S/N: {self.sensor.sensor_id}"
            f"   Capacity: {value:.4g} {unit}  ({capacity_mn:.1f} mN)"
        )

    def _update_capacity_labels(self) -> None:
        """
        Refresh the ± capacity limit labels flanking the force readout.

        Uses the sensor's current ``sensor_capacity`` (in mN) scaled to the
        active display unit. Shows "—" when disconnected.
        """
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
        """
        Handle a change in the display unit selector.

        Updates the plot y-axis label and the ± capacity limit labels.
        The live force value rescales automatically on the next timer tick.

        Args:
            unit: The newly selected unit string (e.g. ``"mN"``, ``"gf"``).
        """
        self.plot_widget.setLabel("left", "Force", units=unit)
        self._update_capacity_labels()

    def _on_timer(self) -> None:
        """
        Timer callback fired every ``UPDATE_INTERVAL_MS`` milliseconds.

        Reads the latest force sample from the sensor and updates:
        - The large force label (current value, scaled to the display unit).
        - The rolling pyqtgraph plot (last ``PLOT_HISTORY_S`` seconds of data).

        Returns early without touching the UI when the sensor is absent,
        disconnected, or has not yet accumulated any samples.
        """
        if self.sensor is None or not self.sensor.is_connected:
            return

        # Guard against the first timer tick before any sample arrives.
        if self.sensor.sample < 1:
            return

        scale: float = DISPLAY_UNITS[self.unit_combo.currentText()]

        # Current-value display.
        force: float = self.sensor.get_current_force() * scale
        self.force_label.setText(f"{force:+.4f} {self.unit_combo.currentText()}")

        # Rolling plot — slice to the last PLOT_HISTORY_S seconds.
        t_all: np.ndarray
        f_all: np.ndarray
        t_all, f_all = self.sensor.get_buffer()
        if len(t_all) == 0:
            return

        # Convert absolute perf_counter timestamps to seconds since connect.
        t_rel: np.ndarray  = t_all - self._start_time
        t_last: float      = t_rel[-1]
        mask: np.ndarray   = t_rel >= t_last - PLOT_HISTORY_S
        self.plot_curve.setData(t_rel[mask], f_all[mask] * scale)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, error: bool = False) -> None:
        """
        Update the status bar label with colour-coded text.

        Color rules:
        - Red   (``#c0392b``) when ``error=True``.
        - Green (``#27ae60``) when ``msg`` contains the word "Connected".
        - Grey  otherwise (disconnected / neutral states).

        Args:
            msg:   Status string to display.
            error: When True, forces the red error colour regardless of content.
        """
        color: str = "#c0392b" if error else "#27ae60" if "Connected" in msg else "grey"
        self.status_label.setStyleSheet(f"color: {color}; font-style: italic;")
        self.status_label.setText(msg)

    def closeEvent(self, event) -> None:
        """
        Handle window close: disconnect the sensor cleanly before exiting.

        Ensures the background polling thread and DLL connection are torn down
        even when the user closes the window instead of pressing Disconnect.

        Args:
            event: The ``QCloseEvent`` passed by Qt.
        """
        self._disconnect()
        super().closeEvent(event)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    app.setStyle("Fusion")
    window: FutekReaderWindow = FutekReaderWindow()
    window.show()
    sys.exit(app.exec())
