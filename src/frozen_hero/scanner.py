"""QR code scanner driven by a motion sensor and Pi Camera."""

import logging
from collections.abc import Callable
from threading import Lock, Thread, Timer
from time import sleep
from typing import Protocol

import lgpio
from picamera2 import Picamera2  # type: ignore
from pyzbar.pyzbar import decode

from frozen_hero import config

logger = logging.getLogger(__name__)


class _MotionSensor(Protocol):
    def cleanup(self) -> None: ...


class _PIRSensor:
    def __init__(self, chip: int, on_motion: Callable[[], None]) -> None:
        lgpio.gpio_claim_alert(chip, config.PIN_PIR, lgpio.RISING_EDGE)
        lgpio.gpio_set_debounce_micros(chip, config.PIN_PIR, config.PIN_MOTION_DEBOUNCE_US)
        self._cb = lgpio.callback(
            chip, config.PIN_PIR, lgpio.RISING_EDGE, lambda *_: on_motion()
        )

    def cleanup(self) -> None:
        self._cb.cancel()


class _APDS9960Sensor:
    def __init__(self, chip: int, on_motion: Callable[[], None]) -> None:
        import smbus2  # type: ignore
        from apds9960 import APDS9960

        self._apds = APDS9960(smbus2.SMBus(1))
        self._apds.setLEDDrive(config.APDS9960_LED_DRIVE)
        self._apds.setProximityGain(config.APDS9960_PROXIMITY_GAIN)
        self._apds.setProxIntHighThresh(config.APDS9960_PROXIMITY_THRESHOLD)
        self._apds.setProximityIntEnable(True)
        self._apds.enableProximitySensor()
        self._on_motion = on_motion
        lgpio.gpio_claim_alert(chip, config.PIN_APDS9960_INT, lgpio.FALLING_EDGE)
        self._cb = lgpio.callback(
            chip, config.PIN_APDS9960_INT, lgpio.FALLING_EDGE, lambda *_: self._on_interrupt()
        )

    def _on_interrupt(self) -> None:
        logger.debug("APDS-9960 proximity interrupt (proximity=%d)", self._apds.readProximity())
        self._apds.clearProximityInt()
        self._on_motion()

    def cleanup(self) -> None:
        self._cb.cancel()


def _make_sensor(chip: int, on_motion: Callable[[], None]) -> _MotionSensor:
    sensor_type = config.MOTION_SENSOR
    if sensor_type == "apds9960":
        return _APDS9960Sensor(chip, on_motion)
    if sensor_type == "pir":
        return _PIRSensor(chip, on_motion)
    raise ValueError(f"Unknown MOTION_SENSOR value: {sensor_type!r} (expected 'pir' or 'apds9960')")


class QRCodeScanner:
    """Scan for QR codes triggered by a motion sensor and Pi Camera.

    When motion is detected the camera starts and scans frames continuously.
    On a successful QR code read the provided callback is invoked with the
    integer id encoded in the code. A timeout stops the scanner automatically
    if no code is found within ``config.SCAN_TIMEOUT_SECONDS``.
    """

    def __init__(
        self, callback: Callable[[int], None], sensor_type: str = "pir"
    ) -> None:
        self._lock = Lock()
        self._callback = callback
        self._active: bool = False
        self._scan_thread: Thread | None = None
        self._timeout_timer: Timer | None = None

        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._chip, config.PIN_BUZZER, 0)
        lgpio.gpio_claim_output(self._chip, config.PIN_LED, 0)

        if sensor_type == "apds9960":
            self._motion_sensor: _MotionSensor = _APDS9960Sensor(self._chip, self._on_motion)
        elif sensor_type == "pir":
            self._motion_sensor = _PIRSensor(self._chip, self._on_motion)
        else:
            raise ValueError(
                f"Unknown sensor_type: {sensor_type!r} (expected 'pir' or 'apds9960')"
            )

        self._camera = Picamera2()
        self._camera.configure(
            self._camera.create_preview_configuration(main={"size": config.CAMERA_RESOLUTION})
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def start_scan(self) -> None:
        """Start the camera and begin scanning for QR codes."""
        with self._lock:
            if self._active:
                return
            if self._scan_thread is not None:
                self._scan_thread.join()
            self._active = True
            self._camera.start()
            self._scan_thread = Thread(target=self._run_scan, daemon=True)
            self._scan_thread.start()

    def stop_scan(self) -> None:
        """Signal the scan loop to stop."""
        with self._lock:
            if self._active:
                logger.debug("Stopping scan")
                self._active = False

    def cleanup(self) -> None:
        """Release GPIO and camera resources."""
        self._motion_sensor.cleanup()
        lgpio.gpiochip_close(self._chip)
        self._camera.close()

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _on_motion(self) -> None:
        logger.debug("Motion detected")
        self.start_scan()

    def _run_scan(self) -> None:
        logger.debug("Scan thread started")
        self._timeout_timer = Timer(config.SCAN_TIMEOUT_SECONDS, self.stop_scan)
        self._timeout_timer.daemon = True
        self._timeout_timer.start()
        self._set_led(True)

        try:
            while self._active:
                frame = self._camera.capture_array()
                barcodes = decode(frame)
                for barcode in barcodes:
                    raw = bytes(barcode.data).decode("utf-8")
                    logger.debug("Found barcode: %s (%s)", raw, barcode.type)
                    if barcode.type == "QRCODE":
                        if self._timeout_timer is not None:
                            self._timeout_timer.cancel()
                        try:
                            entry_id = int(raw)
                        except ValueError:
                            logger.warning("QR code data is not an integer: %r", raw)
                            continue
                        Thread(
                            target=self._beep, args=(config.BUZZER_BEEP_SECONDS,), daemon=True
                        ).start()
                        self._callback(entry_id)
                        self.stop_scan()
                        break
        finally:
            self._camera.stop()
            self._set_led(False)
            logger.debug("Scan thread exiting")

    def _beep(self, seconds: float) -> None:
        """Beep the buzzer synchronously (already running in the scan thread)."""
        lgpio.gpio_write(self._chip, config.PIN_BUZZER, 1)
        sleep(seconds)
        lgpio.gpio_write(self._chip, config.PIN_BUZZER, 0)

    def _set_led(self, enable: bool) -> None:
        lgpio.gpio_write(self._chip, config.PIN_LED, 1 if enable else 0)
