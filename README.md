# frozen-hero

A Raspberry Pi-based freezer inventory system. Add items via a web UI — a QR-code label is printed automatically. When you take something out, hold the label in front of the camera: the motion sensor triggers a scan, the QR code is detected, and the item is removed from the inventory.

## How it works

1. Open the web UI and fill in the item details.
2. A label is printed on the Brother QL printer with a QR code linked to the database entry.
3. Stick the label on the item and put it in the freezer.
4. When taking the item out, wave the label in front of the camera.
5. The PIR sensor triggers the camera, the QR code is scanned, and the item is deleted from the inventory.

## Hardware

| Component | Model |
|---|---|
| Single-board computer | Raspberry Pi 3 |
| Camera | Pi Camera (OV5647) |
| Motion sensor | PIR on GPIO 18 |
| Label printer | Brother QL-580N (62 mm tape) |
| Feedback | Buzzer on GPIO 23, LED on GPIO 24 |

## Software stack

Python · Flask · SQLite · picamera2 · pyzbar · brother_ql · waitress · ImageMagick · qrencode

## Setup

### System dependencies

```bash
sudo apt install libzbar0 swig liblgpio-dev qrencode imagemagick libcap-dev \
                 python3-libcamera python3-picamera2
sudo apt install ./utils/ql600pdrv-3.1.5-0.armhf.deb
```

### Python environment

picamera2 is only available as a system package, so the venv must include system site-packages:

```bash
python -m venv venv --system-site-packages
source venv/bin/activate
pip install -e .
```

### Permissions

```bash
# Camera access
sudo usermod -aG video hero

# USB printer access — create /etc/udev/rules.d/99-brother.rules:
# SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", ATTRS{idProduct}=="20c0", MODE="0666"
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Autostart

```bash
sudo cp autostart/frozen-hero.service /etc/systemd/system/
sudo systemctl enable --now frozen-hero
```

### Database backup (optional)

Copies the SQLite database to a NAS share daily at 18:00:

```bash
sudo cp backup/frozen-hero-db-backup.service backup/frozen-hero-db-backup.timer /etc/systemd/system/
sudo systemctl enable --now frozen-hero-db-backup.timer
```

## Running

```bash
# Production (waitress + QR scanner)
python -m frozen_hero

# Flask dev server only (no waitress, no hardware needed)
python -m frozen_hero --web-debug

# Verbose logging
python -m frozen_hero --debug
```

The web UI is available at `http://hero-pi.hero.home:5000`.

Do not run as root.

## Project structure

```
frozen-hero/
├── src/frozen_hero/
│   ├── __main__.py   # entry point (argparse, signal handling)
│   ├── config.py     # all constants (paths, GPIO pins, printer settings)
│   ├── app.py        # Flask app + routes
│   ├── db.py         # SQLite data-access layer
│   ├── scanner.py    # PIR + camera QR scanner
│   └── label.py      # label generation and printing
├── templates/
│   └── index.html    # single-page web UI
├── autostart/        # systemd service
└── backup/           # backup service and timer
```

## Development

```bash
# Lint
ruff check src/

# Type-check
mypy src/

# Smoke-test Flask routes without hardware
flask --app "frozen_hero.app:create_app" run
```
