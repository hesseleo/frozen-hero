# frozen-hero

A freezer inventory system. Add items via a web UI and a QR-code label is printed automatically. When you take something out, hold the label in front of the camera: the motion sensor triggers a scan, the QR code is detected, and the item is removed from the inventory.

## How it works

1. Open the web UI and fill in the item details.
2. A label is printed on the Brother QL printer with a QR code linked to the database entry.
3. Stick the label on the item and put it in the freezer.
4. When taking the item out, wave the label in front of the camera.
5. The PIR sensor triggers the camera, the QR code is scanned, and the item is deleted from the inventory.

## Hardware

| Component | Model | URL |
|---|---|---|
| Single-board computer | Raspberry Pi 3 | [raspberrypi.com][1]
| Camera | Pi Camera (RPI-CAM-A) | [berrybase.de][2]
| Motion sensor | PIR on GPIO 18 | [roboter-bausatz.de][3]
| Label printer | Brother QL-600 (62 mm tape) | [brother.de][4]
| Feedback | Buzzer on GPIO 23, LED on GPIO 24 | [roboter-bausatz.de][5]

[1]: https://www.raspberrypi.com/products/raspberry-pi-3-model-a-plus/
[2]: https://www.berrybase.de/en/detail/019234a47da57169b9528f4494a79d4c
[3]: https://www.roboter-bausatz.de/p/ir-infrarot-sensor-hinderniserkennung-abstandssensor?sPartner=8&gad_source=1&gad_campaignid=12461217733&gbraid=0AAAAADKFiCD4XXSAgRBpw0zhqrclMnJXt&gclid=CjwKCAiAh5XNBhAAEiwA_Bu8FTuyFZUF0pXnI1LooVUNZXRqBCvG0g2XD8kBqjvOrPQ9rhLXEw8TThoCADMQAvD_BwE
[4]: https://store.brother.de/geraete/etikettendrucker/ql/ql600g?srsltid=AfmBOorjSMEOkkumK52NTRb9omN5WG3jgbD0q1TNCIWYdhDHQmGC4MSd
[5]: https://www.roboter-bausatz.de/p/10-stueck-aktiver-buzzer-3-3v-5v?sPartner=8&gad_source=1&gad_campaignid=12461217733&gclid=CjwKCAiAh5XNBhAAEiwA_Bu8FcOTPd0QJVJWvRRFX2prPKh9OBtapMEYlnr5ULDYgHG_L2zlHQq_XxoCrgYQAvD_BwE

## Software stack

Python · Flask · SQLite · picamera2 · pyzbar · brother_ql · waitress · ImageMagick · qrencode

## Setup

### System dependencies

```bash
sudo apt install libzbar0 swig liblgpio-dev qrencode imagemagick libcap-dev python3-libcamera python3-picamera2
```

```bash
sudo apt install ./utils/ql600pdrv-3.1.5-0.armhf.deb
```

### Clone this repository into your home directory
```bash
git clone https://github.com/hesseleo/frozen-hero.git ~/frozen-hero
```

### Python environment

picamera2 is only available as a system package, so the venv must include system site-packages:

```bash
cd ~/frozen-hero
python -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -e .
```

### Permissions

```bash
sudo usermod -aG video,lp $USER
```

### Autostart

Create `/etc/systemd/system/frozen-hero.service` and adjust `User`.

```ini
[Unit]
Description=frozen-hero Freezer Management System
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=%h/frozen-hero
Environment="PATH=%h/frozen-hero/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=%h/frozen-hero/.venv/bin/python -m frozen_hero
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now frozen-hero
```

## Running

```bash
python -m frozen_hero
```

The web UI is available at `http://<HOSTNAME>:5000`.

## Releasing

Releases are automated via GitHub Actions. The workflow bumps the version in `pyproject.toml`,
commits, tags, builds the package, and publishes to PyPI — all from a single manual trigger.

### Triggering a release

1. Go to **GitHub → Actions → Release → Run workflow**
2. Enter the new version (e.g. `0.2.0`) and click **Run workflow**
3. The workflow will commit `chore: bump version to v0.2.0`, push the tag `v0.2.0`, and publish to PyPI
