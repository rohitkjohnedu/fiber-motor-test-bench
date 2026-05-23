"""
Unit tests: both force sensors are tared before the HV signal is applied
in StaticMode.force_vs_position().

Serial numbers are read from IPM650_sl.json so the test stays in sync with
the hardware configuration.  No real hardware or QApplication is required.
"""

import json
import os
import sys
import threading
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from PowerSupply.ps_modes.static_characterization.static import StaticMode


def _load_sns():
    with open(os.path.join(ROOT, "IPM650_sl.json")) as f:
        d = json.load(f)
    return str(d["sensor_1"]), str(d["sensor_2"])


SN1, SN2 = _load_sns()

SLEEP_PATH = "PowerSupply.ps_modes.static_characterization.static.time.sleep"


def _make_sensor(sn: str) -> MagicMock:
    s = MagicMock()
    s.serial_number = sn
    s.buffer_length = 10_000_000
    s.sample = 0
    return s


def _make_obj(with_sensor2: bool = True) -> MagicMock:
    """Minimal stand-in for a StaticMode instance."""
    obj = MagicMock()

    obj.force_sensor  = _make_sensor(SN1)
    obj.force_sensor2 = _make_sensor(SN2) if with_sensor2 else None
    obj.stop_event    = threading.Event()

    # Actuator — single step at position 0
    obj.actuator.get_position.return_value = 0.0
    obj.actuator.max_speed      = 4.0
    obj.actuator.buffer_length  = 10_000_000
    obj.actuator.sample         = 0
    obj.actuator_control.home_chckbox.isChecked.return_value = False
    obj.actuator_control.start_pos_edit.text.return_value    = "0.0"
    obj.actuator_control.end_pos_edit.text.return_value      = "0.0"
    obj.actuator_control.step_size_edit.text.return_value    = "1.0"
    obj.actuator_control.speed_edit.text.return_value        = "1.0"

    # Power supply — non-modulated A-B-C sequence
    obj.power_supply.buffer_length = 10_000_000
    obj.power_supply.sample        = 0
    obj.power_supply_control.modulation_opt.isChecked.return_value        = False
    obj.power_supply_control.control_sequence.currentText.return_value    = "A-B-C"

    return obj


class TestTaring(unittest.TestCase):

    @patch(SLEEP_PATH)
    def test_sensor1_is_tared(self, _):
        obj = _make_obj()
        StaticMode.force_vs_position(obj)
        self.assertGreater(
            obj.force_sensor.tare.call_count, 0,
            f"Sensor 1 (S/N {SN1}) was never tared",
        )

    @patch(SLEEP_PATH)
    def test_sensor2_is_tared(self, _):
        obj = _make_obj()
        StaticMode.force_vs_position(obj)
        self.assertGreater(
            obj.force_sensor2.tare.call_count, 0,
            f"Sensor 2 (S/N {SN2}) was never tared",
        )

    @patch(SLEEP_PATH)
    def test_both_tared_equal_number_of_times(self, _):
        obj = _make_obj()
        StaticMode.force_vs_position(obj)
        n1 = obj.force_sensor.tare.call_count
        n2 = obj.force_sensor2.tare.call_count
        self.assertEqual(
            n1, n2,
            f"Sensor 1 (S/N {SN1}) tared {n1}× but sensor 2 (S/N {SN2}) tared {n2}×",
        )

    @patch(SLEEP_PATH)
    def test_tare_before_hv_for_every_state(self, _):
        """Both sensors must be tared between the previous set_pressed and
        the current one — i.e. directly before each HV activation."""
        obj = _make_obj()

        call_order = []

        def record(name):
            def _se(*args, **kwargs):
                call_order.append(name)
            return _se

        obj.force_sensor.tare.side_effect              = record("tare1")
        obj.force_sensor2.tare.side_effect             = record("tare2")
        obj.power_supply_control.set_pressed.side_effect = record("set_pressed")

        StaticMode.force_vs_position(obj)

        set_pressed_indices = [i for i, e in enumerate(call_order) if e == "set_pressed"]
        self.assertTrue(set_pressed_indices, "set_pressed was never called — test setup issue")

        for idx in set_pressed_indices:
            prev = next(
                (j for j in range(idx - 1, -1, -1) if call_order[j] == "set_pressed"),
                -1,
            )
            window = call_order[prev + 1 : idx]
            self.assertIn(
                "tare1", window,
                f"Sensor 1 (S/N {SN1}) not tared before set_pressed at call-order index {idx}",
            )
            self.assertIn(
                "tare2", window,
                f"Sensor 2 (S/N {SN2}) not tared before set_pressed at call-order index {idx}",
            )

    @patch(SLEEP_PATH)
    def test_no_crash_without_sensor2(self, _):
        """force_vs_position must complete normally when sensor 2 is absent."""
        obj = _make_obj(with_sensor2=False)
        try:
            StaticMode.force_vs_position(obj)
        except Exception as exc:
            self.fail(f"force_vs_position raised {exc!r} with force_sensor2=None")
        self.assertGreater(
            obj.force_sensor.tare.call_count, 0,
            f"Sensor 1 (S/N {SN1}) was not tared when sensor 2 is absent",
        )


    @patch(SLEEP_PATH)
    def test_late_connect_sensor2_is_tared(self, _):
        """
        Regression: sensor 2 connected via Apply *after* StaticMode was
        constructed (force_sensor2 starts as None, then is set later).
        This mirrors the bug where _apply_futek_sn2 forgot to update
        static.force_sensor2, leaving it None during the experiment.
        """
        obj = _make_obj(with_sensor2=False)   # StaticMode started with None
        obj.force_sensor2 = _make_sensor(SN2) # sensor 2 connected later

        StaticMode.force_vs_position(obj)

        self.assertGreater(
            obj.force_sensor2.tare.call_count, 0,
            f"Sensor 2 (S/N {SN2}) not tared after late connect — "
            "static.force_sensor2 was probably never updated by _apply_futek_sn2",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
