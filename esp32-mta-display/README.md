# esp32-mta-display

Monorepo containing:
- A Python FastAPI backend that renders BMP snapshots of upcoming MTA + PATH arrivals.
- An ESP32 Arduino client that fetches those BMP images over Wi‑Fi and displays them on an ST7789 TFT.

## Folder structure

```text
esp32-mta-display/
├── backend/
│   ├── pyproject.toml
│   └── src/
│       └── esp32_mta_display/
│           ├── __init__.py
│           ├── main.py
│           ├── routers/
│           │   └── display.py
│           ├── services/
│           │   ├── mta.py
│           │   ├── path.py
│           │   ├── renderer.py
│           │   └── config_loader.py
│           ├── models/
│           │   └── arrivals.py
│           ├── utils/
│           │   └── time.py
│           ├── config/
│           │   └── displays/
│           │       └── example.yml
│           └── static/
│               └── fonts/
├── esp32_client/
│   ├── esp32-mta-display.ino
│   ├── README.md
│   ├── config.example.h
│   └── lib/
├── .gitignore
└── LICENSE
```

## Backend (FastAPI)

- Python 3.11+
- FastAPI app in `backend/src/esp32_mta_display/main.py`
- Display endpoint in `backend/src/esp32_mta_display/routers/display.py`
- GTFS-RT integration placeholders in `backend/src/esp32_mta_display/services/`
- YAML display configuration examples in `backend/src/esp32_mta_display/config/displays/`

To run in development after installing dependencies:

```bash
cd backend
pip install -e .
uvicorn esp32_mta_display.main:app --reload
```

## ESP32 client

Arduino sketch and helper stubs live in `esp32_client/`.

1. Copy `config.example.h` to `config.h` and fill in Wi‑Fi + backend URL.
2. Open `esp32-mta-display.ino` in the Arduino IDE or PlatformIO.
3. Flash to an ESP32 with an ST7789 TFT wired up.

Display + HTTP/BMP handling is left as TODOs to be implemented.
