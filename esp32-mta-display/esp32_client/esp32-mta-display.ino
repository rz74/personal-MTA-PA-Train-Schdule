#include <WiFi.h>
#include <HTTPClient.h>

#include "config.h"  // Copy from config.example.h and customize

// TODO: include TFT_eSPI and configure pins in User_Setup.h
// #include <TFT_eSPI.h>

// TODO: instantiate display object
// TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("[esp32-mta-display] Booting...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected, IP address: ");
  Serial.println(WiFi.localIP());

  // TODO: initialize TFT_eSPI display and clear screen
  // tft.init();
  // tft.setRotation(1); // adjust as needed
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String url = String(BACKEND_BASE_URL) + String(DISPLAY_ENDPOINT_PATH);
    Serial.print("Fetching BMP from: ");
    Serial.println(url);

    if (http.begin(url)) {
      int httpCode = http.GET();
      if (httpCode == HTTP_CODE_OK) {
        // NOTE: For real use, stream response directly to display to avoid
        // large RAM usage. This is left as a TODO.
        WiFiClient *stream = http.getStreamPtr();

        // TODO: parse BMP header from stream and push pixel data to ST7789
        // using TFT_eSPI or equivalent library.
      } else {
        Serial.print("HTTP error: ");
        Serial.println(httpCode);
      }

      http.end();
    } else {
      Serial.println("Failed to begin HTTP connection");
    }
  } else {
    Serial.println("WiFi not connected");
  }

  // Sleep for a while before fetching the next frame
  delay(REFRESH_INTERVAL_SECONDS * 1000);
}
