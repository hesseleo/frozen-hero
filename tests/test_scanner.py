"""Tests for QRCodeScanner (all hardware mocked)."""

import sys
import time
from unittest.mock import ANY, MagicMock, patch

import pytest

from frozen_hero import config
from frozen_hero.scanner import QRCodeScanner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_barcode(data: str, barcode_type: str = "QRCODE") -> MagicMock:
    """Return a mock object that looks like a pyzbar decoded barcode."""
    b = MagicMock()
    b.data = data.encode()
    b.type = barcode_type
    return b


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def gpio():
    mock = sys.modules["RPi.GPIO"]
    mock.reset_mock()
    return mock


@pytest.fixture()
def scanner(gpio):
    return QRCodeScanner(callback=MagicMock())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInit:
    def test_gpio_pins_configured(self, gpio):
        QRCodeScanner(callback=MagicMock())
        gpio.setmode.assert_called_once()
        # setup called for motion, buzzer and LED pins
        setup_pins = {c[0][0] for c in gpio.setup.call_args_list}
        assert config.PIN_MOTION_DETECTOR in setup_pins
        assert config.PIN_BUZZER in setup_pins
        assert config.PIN_LED in setup_pins

    def test_motion_interrupt_registered(self, gpio):
        QRCodeScanner(callback=MagicMock())
        gpio.add_event_detect.assert_called_once_with(
            config.PIN_MOTION_DETECTOR, gpio.RISING, callback=ANY
        )


class TestStartStop:
    def test_start_scan_opens_and_starts_camera(self, scanner):
        with (
            patch("frozen_hero.scanner.Picamera2") as MockCam,
            patch("frozen_hero.scanner.decode", return_value=[]),
        ):
            scanner.start_scan()
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        MockCam.assert_called_once()
        MockCam.return_value.start.assert_called_once()

    def test_second_start_while_active_is_ignored(self, scanner):
        with (
            patch("frozen_hero.scanner.Picamera2") as MockCam,
            patch("frozen_hero.scanner.decode", return_value=[]),
        ):
            scanner.start_scan()
            scanner.start_scan()  # must be a no-op
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        assert MockCam.call_count == 1

    def test_camera_stopped_and_closed_after_stop(self, scanner):
        with (
            patch("frozen_hero.scanner.Picamera2") as MockCam,
            patch("frozen_hero.scanner.decode", return_value=[]),
        ):
            scanner.start_scan()
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        MockCam.return_value.stop.assert_called_once()
        MockCam.return_value.close.assert_called_once()

    def test_led_turned_off_after_stop(self, scanner, gpio):
        with (
            patch("frozen_hero.scanner.Picamera2"),
            patch("frozen_hero.scanner.decode", return_value=[]),
        ):
            scanner.start_scan()
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        gpio.output.assert_any_call(config.PIN_LED, gpio.LOW)


class TestQRDetection:
    def test_valid_qr_code_triggers_callback(self, scanner):
        barcode = _make_barcode("42")
        with (
            patch("frozen_hero.scanner.Picamera2"),
            patch("frozen_hero.scanner.decode", return_value=[barcode]),
        ):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._callback.assert_called_once_with(42)

    def test_callback_called_only_once_per_scan(self, scanner):
        """Even if multiple frames contain a QR code, callback fires once."""
        barcode = _make_barcode("7")
        with (
            patch("frozen_hero.scanner.Picamera2"),
            patch("frozen_hero.scanner.decode", return_value=[barcode]),
        ):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        assert scanner._callback.call_count == 1

    def test_non_integer_qr_data_does_not_trigger_callback(self, scanner):
        bad_barcode = _make_barcode("not-an-integer")
        call_count = [0]

        def decode_fn(_frame):
            call_count[0] += 1
            return [bad_barcode] if call_count[0] == 1 else []

        with (
            patch("frozen_hero.scanner.Picamera2"),
            patch("frozen_hero.scanner.decode", side_effect=decode_fn),
        ):
            scanner.start_scan()
            time.sleep(0.1)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._callback.assert_not_called()

    def test_non_qr_barcode_type_ignored(self, scanner):
        ean_barcode = _make_barcode("12345", barcode_type="EAN13")
        call_count = [0]

        def decode_fn(_frame):
            call_count[0] += 1
            return [ean_barcode] if call_count[0] == 1 else []

        with (
            patch("frozen_hero.scanner.Picamera2"),
            patch("frozen_hero.scanner.decode", side_effect=decode_fn),
        ):
            scanner.start_scan()
            time.sleep(0.1)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._callback.assert_not_called()


class TestErrorHandling:
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_camera_cleaned_up_when_decode_raises(self, scanner):
        with (
            patch("frozen_hero.scanner.Picamera2") as MockCam,
            patch("frozen_hero.scanner.decode", side_effect=RuntimeError("camera error")),
        ):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        MockCam.return_value.stop.assert_called_once()
        MockCam.return_value.close.assert_called_once()

    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_led_turned_off_when_decode_raises(self, scanner, gpio):
        with (
            patch("frozen_hero.scanner.Picamera2"),
            patch("frozen_hero.scanner.decode", side_effect=RuntimeError("err")),
        ):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        gpio.output.assert_any_call(config.PIN_LED, gpio.LOW)


class TestMotion:
    def test_motion_callback_calls_start_scan(self, scanner):
        with patch.object(scanner, "start_scan") as mock_start:
            scanner._on_motion(config.PIN_MOTION_DETECTOR)
        mock_start.assert_called_once()
