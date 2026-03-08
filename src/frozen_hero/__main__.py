"""Entry point for frozen-hero.

Run with:
    python -m frozen_hero [--debug] [--web-debug] [--no-hardware]
"""

import argparse
import logging
import os
import signal
import sys
from threading import Thread

from frozen_hero import config, db
from frozen_hero.app import create_app

logger = logging.getLogger(__name__)

# Set in main() when hardware is enabled; used by _signal_handler.
_scanner = None


def _configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _signal_handler(sig: int, frame: object) -> None:
    print("\rfrozen-hero stopped by user. Goodbye!")
    if _scanner is not None:
        _scanner.stop_scan()
        _scanner.cleanup()
    sys.exit(0)


def main() -> None:
    global _scanner  # noqa: PLW0603

    parser = argparse.ArgumentParser(description="frozen-hero freezer management system")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--web-debug", action="store_true", help="Start Flask dev server instead of waitress"
    )
    parser.add_argument(
        "--no-hardware",
        action="store_true",
        help="Skip GPIO / camera initialisation (for desktop development)",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Template mode: generate label preview only, skip DB and printer",
    )
    args = parser.parse_args()

    _configure_logging(args.debug)

    if "SUDO_UID" in os.environ:
        sys.exit("Running this program with root permission is not allowed.")

    signal.signal(signal.SIGINT, _signal_handler)

    app = create_app(template_mode=args.template)

    if not args.no_hardware:
        from frozen_hero.scanner import QRCodeScanner

        def on_qr_detected(entry_id: int) -> None:
            removed = db.delete_entry(entry_id)
            if removed:
                logger.info("QR code detected — deleted entry %d", entry_id)
            else:
                logger.warning("QR code detected but entry %d not found", entry_id)

        _scanner = QRCodeScanner(callback=on_qr_detected)
        logger.info("QR code scanner ready")
    else:
        logger.info("Hardware disabled — scanner not started")

    if args.web_debug:
        logger.info("Starting Flask development server")
        app.run(debug=True, use_reloader=False, host=config.SERVER_HOST, port=config.SERVER_PORT)
    else:
        from waitress import serve

        logger.info("Starting waitress on %s:%d", config.SERVER_HOST, config.SERVER_PORT)
        Thread(
            target=lambda: serve(app, host=config.SERVER_HOST, port=config.SERVER_PORT),
            daemon=True,
        ).start()

        signal.pause()


if __name__ == "__main__":
    main()
