"""QR code scanner driven by a PIR motion detector and Pi Camera."""

import logging
from collections.abc import Callable
from threading import Lock, Thread, Timer
from time import sleep

import lgpio
from picamera2 import Picamera2  # type: ignore
from pyzbar.pyzbar import decode

from frozen_hero import config

logger = logging.getLogger(__name__)


class QRCodeScanner:
    """Scan for QR codes triggered by a PIR motion detector.

    When motion is detected the camera starts and scans frames continuously.
    On a successful QR code read the provided callback is invoked with the
    integer id encoded in the code. A timeout stops the scanner automatically
    if no code is found within ``config.SCAN_TIMEOUT_SECONDS``.
    """

    def __init__(self, callback: Callable[[int], None]) -> None:
        self._lock = Lock()
        self._callback = callback
        self._active: bool = False
        self._scan_thread: Thread | None = None
        self._timeout_timer: Timer | None = None

        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_alert(self._chip, config.PIN_MOTION_DETECTOR, lgpio.RISING_EDGE)
        lgpio.gpio_set_debounce_micros(self._chip, config.PIN_MOTION_DETECTOR, config.PIN_MOTION_DEBOUNCE_US)
        self._motion_cb = lgpio.callback(
            self._chip, config.PIN_MOTION_DETECTOR, lgpio.RISING_EDGE, self._on_motion
        )
        lgpio.gpio_claim_output(self._chip, config.PIN_BUZZER, 0)
        lgpio.gpio_claim_output(self._chip, config.PIN_LED, 0)

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
        self._motion_cb.cancel()
        lgpio.gpiochip_close(self._chip)
        self._camera.close()

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _on_motion(self, _chip: int, _gpio: int, _level: int, _tick: int) -> None:
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
