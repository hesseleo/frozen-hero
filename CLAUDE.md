# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

frozen-hero is a Raspberry Pi-based freezer inventory management system. Items are added via a web UI, which prints a QR-code label (using a Brother QL printer). A PIR motion detector triggers the Pi camera to scan for QR codes; when one is detected, the item is automatically removed from the database. The web interface runs at `http://<hostname>:5000`.

**Hardware:** Raspberry Pi 3, Pi Camera (OV5647), PIR motion detector (GPIO 18), buzzer (GPIO 23), LED (GPIO 24), Brother QL-580N label printer.

**Stack:** Python, Flask, SQLite, picamera2, pyzbar, brother_ql, waitress (production server), ImageMagick + qrencode (label generation).

## Setup

```bash
# System dependencies (on the Pi)
sudo apt install libzbar0t64 swig liblgpio-dev qrencode imagemagick libcap-dev python3-libcamera python3-picamera2

# Python environment (must use --system-site-packages for picamera2)
python -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -e .

# Permissions: camera, GPIO, printer at /dev/usb/lp0
sudo usermod -aG video,gpio,lp $USER
```

## Running the Application

```bash
# Production (runs Flask via waitress on port 5000 + starts QR code reader)
python -m frozen_hero

# Web debug mode (Flask dev server, no waitress)
python -m frozen_hero --web-debug

# Enable debug logging
python -m frozen_hero --debug
```

**Do not run as root** — the app explicitly blocks this check.

## Database

SQLite database at `database/frozen-hero.db` (excluded from git via `.gitignore`).

Schema:
```sql
CREATE TABLE freezer(id INTEGER PRIMARY KEY AUTOINCREMENT, row_one TEXT, row_two TEXT, category TEXT, date DATE);
```

## Architecture

```
frozen-hero/
├── pyproject.toml
├── src/
│   └── frozen_hero/
│       ├── __init__.py      # package marker + __version__
│       ├── __main__.py      # entry point (argparse, logging, signal handling)
│       ├── config.py        # all constants (paths, pins, printer, label layout)
│       ├── app.py           # Flask factory + routes
│       ├── db.py            # SQLite data-access layer (parameterised queries)
│       ├── scanner.py       # QRCodeScanner (GPIO + picamera2)
│       └── label.py         # label generation + printing
├── templates/index.html
├── database/                # gitignored
├── images/
└── tmp/{TxtImg,QRcode,Label}/
```

### `src/frozen_hero/__main__.py`
- `argparse`: `--debug`, `--web-debug`
- Root-user check via `"SUDO_UID" in os.environ`
- Starts waitress in daemon thread (or Flask dev server)
- Instantiates `QRCodeScanner`; SIGINT calls `stop_scan()` + `GPIO.cleanup()`

### `src/frozen_hero/config.py`
Single source of truth for all constants. `PROJECT_ROOT` is derived from `__file__` so the app works regardless of the working directory.

### `src/frozen_hero/db.py`
All queries use `?` parameterised placeholders — no SQL injection possible.
- `get_all_entries() -> list[dict]`
- `add_entry(row_one, row_two, category, date) -> int`
- `delete_entry(entry_id) -> bool`

### `src/frozen_hero/label.py`
Public functions: `generate_label(...) -> Path`, `print_label(label_path) -> None`
- All subprocess calls use `subprocess.run(list, shell=False)` — no shell injection.
- User text is escaped with `xml.sax.saxutils.escape()` before Pango markup embedding.
- `_APP_VERSION` is set at import time from `__version__` and printed in the label footer.
- Label layout (bottom to top): footer strip (`Frozen HeRo` + version), separator, best-before date, subtitle, title.

### `src/frozen_hero/scanner.py` — `QRCodeScanner`
- GPIO-driven: PIR sensor interrupt → `start_scan()`
- Camera scans frames; on QR code detection → callback → `stop_scan()`
- 5-second timeout auto-stops scanning
- Thread-safe via `Lock`

### Flask API (`src/frozen_hero/app.py`)
| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves `templates/index.html` |
| `/getData` | GET | Returns all freezer entries as JSON array |
| `/add2freezer` | POST | Inserts entry, triggers label print |
| `/delEntry` | POST | Deletes entry by `id` |

### `templates/index.html`
Single-page app (vanilla JS, no framework). Two tabs: "Neues Label" (add item + print) and "Liste anzeigen" (inventory table). Swipe left/right on a row to delete it. Uses relative API URLs.

## Systemd Service

The service file template is in the README. Deploy to `/etc/systemd/system/frozen-hero.service` with `User` adjusted, then:

```bash
sudo systemctl enable --now frozen-hero
```

The `autostart/` and `backup/` directories are gitignored (contain instance-specific configs).

## Label Size Configuration

Label dimensions are controlled by `QR_CODE_SIZE` in `src/frozen_hero/config.py`. Printable pixel width is fixed at 696px for the 62mm tape. The QR code encodes only the database row `id` (integer).

## Tooling

```bash
# Lint
ruff check src/

# Type-check
mypy src/

# Smoke-test Flask routes without hardware (desktop)
flask --app "frozen_hero.app:create_app" run
```
