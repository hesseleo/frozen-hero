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
def lgpio_mock():
    mock = sys.modules["lgpio"]
    mock.reset_mock()
    mock.gpiochip_open.return_value = 0
    mock.callback.return_value = MagicMock()
    return mock


@pytest.fixture()
def picamera2_mock():
    mock = sys.modules["picamera2"]
    mock.reset_mock()
    return mock


@pytest.fixture()
def scanner(lgpio_mock, picamera2_mock):
    return QRCodeScanner(callback=MagicMock())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInit:
    def test_gpio_pins_configured(self, lgpio_mock):
        QRCodeScanner(callback=MagicMock())
        lgpio_mock.gpiochip_open.assert_called_with(0)
        lgpio_mock.gpio_claim_alert.assert_called_with(ANY, config.PIN_MOTION_DETECTOR, lgpio_mock.RISING_EDGE)
        lgpio_mock.gpio_set_debounce_micros.assert_called_with(
            ANY, config.PIN_MOTION_DETECTOR, config.PIN_MOTION_DEBOUNCE_US
        )
        output_pins = {c[0][1] for c in lgpio_mock.gpio_claim_output.call_args_list}
        assert config.PIN_BUZZER in output_pins
        assert config.PIN_LED in output_pins

    def test_motion_interrupt_registered(self, lgpio_mock):
        QRCodeScanner(callback=MagicMock())
        lgpio_mock.callback.assert_called_with(
            ANY, config.PIN_MOTION_DETECTOR, lgpio_mock.RISING_EDGE, ANY
        )

    def test_cleanup_closes_camera(self, scanner):
        scanner.cleanup()
        scanner._camera.close.assert_called_once()


class TestStartStop:
    def test_start_scan_opens_and_starts_camera(self, scanner):
        with patch("frozen_hero.scanner.decode", return_value=[]):
            scanner.start_scan()
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._camera.start.assert_called_once()

    def test_second_start_while_active_is_ignored(self, scanner):
        with patch("frozen_hero.scanner.decode", return_value=[]):
            scanner.start_scan()
            scanner.start_scan()  # must be a no-op
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        assert scanner._camera.start.call_count == 1

    def test_camera_stopped_and_closed_after_stop(self, scanner):
        with patch("frozen_hero.scanner.decode", return_value=[]):
            scanner.start_scan()
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._camera.stop.assert_called_once()

    def test_led_turned_off_after_stop(self, scanner, lgpio_mock):
        with patch("frozen_hero.scanner.decode", return_value=[]):
            scanner.start_scan()
            time.sleep(0.05)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        lgpio_mock.gpio_write.assert_any_call(ANY, config.PIN_LED, 0)


class TestQRDetection:
    def test_valid_qr_code_triggers_callback(self, scanner):
        barcode = _make_barcode("42")
        with patch("frozen_hero.scanner.decode", return_value=[barcode]):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._callback.assert_called_once_with(42)

    def test_callback_called_only_once_per_scan(self, scanner):
        """Even if multiple frames contain a QR code, callback fires once."""
        barcode = _make_barcode("7")
        with patch("frozen_hero.scanner.decode", return_value=[barcode]):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        assert scanner._callback.call_count == 1

    def test_non_integer_qr_data_does_not_trigger_callback(self, scanner):
        bad_barcode = _make_barcode("not-an-integer")
        call_count = [0]

        def decode_fn(_frame):
            call_count[0] += 1
            return [bad_barcode] if call_count[0] == 1 else []

        with patch("frozen_hero.scanner.decode", side_effect=decode_fn):
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

        with patch("frozen_hero.scanner.decode", side_effect=decode_fn):
            scanner.start_scan()
            time.sleep(0.1)
            scanner.stop_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._callback.assert_not_called()


class TestErrorHandling:
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_camera_cleaned_up_when_decode_raises(self, scanner):
        with patch("frozen_hero.scanner.decode", side_effect=RuntimeError("camera error")):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        scanner._camera.stop.assert_called_once()

    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_led_turned_off_when_decode_raises(self, scanner, lgpio_mock):
        with patch("frozen_hero.scanner.decode", side_effect=RuntimeError("err")):
            scanner.start_scan()
            scanner._scan_thread.join(timeout=2)

        lgpio_mock.gpio_write.assert_any_call(ANY, config.PIN_LED, 0)


class TestMotion:
    def test_motion_callback_calls_start_scan(self, scanner):
        with patch.object(scanner, "start_scan") as mock_start:
            scanner._on_motion(0, config.PIN_MOTION_DETECTOR, 1, 0)
        mock_start.assert_called_once()
