# ESP32 client

Arduino sketch for an ESP32 board that fetches BMP images from the
FastAPI backend and displays them on an ST7789 TFT.

## Setup

1. Copy `config.example.h` to `config.h` and fill in:
   - Wi‑Fi SSID and password
   - Backend base URL (e.g. `http://192.168.1.10:8000`)
   - Display id path (e.g. `/display/example.bmp`)
2. Install the ESP32 board support package in the Arduino IDE or PlatformIO.
3. Install and configure the TFT_eSPI library for your ST7789 wiring.
4. Open `esp32-mta-display.ino` and upload to the board.

Display refresh interval and drawing logic are left as TODOs.
