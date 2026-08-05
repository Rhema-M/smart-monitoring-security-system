// ============================================================
//  SMSAM — ESP32 DHT22 Temperature + Humidity Sensor
//  Sketch  : smsam_dht22.ino
//
//  Hardware:
//    ESP32 Dev Board
//    DHT22 (AM2302) sensor
//    Wiring:
//      DHT22 Pin 1 (VCC) → 3.3V
//      DHT22 Pin 2 (DATA) → GPIO4  +  10kΩ pull-up to 3.3V
//      DHT22 Pin 3 (NC)   → (not connected)
//      DHT22 Pin 4 (GND)  → GND
//
//  Libraries (install via Library Manager):
//    - DHT sensor library by Adafruit
//    - Adafruit Unified Sensor by Adafruit  (dependency)
//    - ArduinoJson by Benoit Blanchon v6.x
//    WiFi + HTTPClient are built into the ESP32 core
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ─────────────────────────────────────────────────────────────
//  USER CONFIGURATION
// ─────────────────────────────────────────────────────────────
const char* WIFI_SSID      = "Hacking";
const char* WIFI_PASSWORD  = "rhemaonly";
const char* FLASK_BASE_URL = "http://10.69.9.26:5000";  // LAN IP of Flask server

// ─────────────────────────────────────────────────────────────
//  PIN & SENSOR CONFIG
// ─────────────────────────────────────────────────────────────
const int  PIN_DHT                = 4;       // GPIO4 — DHT22 data line
const int  DHT_TYPE               = DHT22;   // Use DHT11 here if you have a DHT11

// DHT22 minimum sampling rate: 0.5 Hz (read no faster than every 2 s)
// We use 5 s to stay well within spec and reduce network traffic.
const unsigned long READ_INTERVAL = 2000;    // ms between sensor reads + POSTs

// ─────────────────────────────────────────────────────────────
//  SENSOR OBJECT
// ─────────────────────────────────────────────────────────────
DHT dht(PIN_DHT, DHT_TYPE);

// ─────────────────────────────────────────────────────────────
//  GLOBALS
// ─────────────────────────────────────────────────────────────
unsigned long g_lastRead       = 0;
int           g_consecutiveFail = 0;   // track repeated read failures
const int     MAX_FAILS        = 5;    // restart after 5 consecutive bad reads

// ─────────────────────────────────────────────────────────────
//  SETUP
// ─────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.println("\n[SMSAM-DHT22] Temperature & humidity node starting...");

    dht.begin();
    connectWiFi();
}

// ─────────────────────────────────────────────────────────────
//  LOOP
// ─────────────────────────────────────────────────────────────
void loop() {
    unsigned long now = millis();

    if (now - g_lastRead >= READ_INTERVAL) {
        g_lastRead = now;
        readAndSend();
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Lost — reconnecting...");
        connectWiFi();
    }
}

// ─────────────────────────────────────────────────────────────
//  READ DHT22 AND SEND TO FLASK
// ─────────────────────────────────────────────────────────────
void readAndSend() {
    // DHT library returns NaN on read failure
    float temperature = dht.readTemperature();   // Celsius
    float humidity    = dht.readHumidity();

    // Validate — isnan() catches DHT read errors
    if (isnan(temperature) || isnan(humidity)) {
        g_consecutiveFail++;
        Serial.printf("[DHT22] Read failed (%d/%d). Check wiring.\n",
                      g_consecutiveFail, MAX_FAILS);

        if (g_consecutiveFail >= MAX_FAILS) {
            Serial.println("[DHT22] Too many failures. Restarting ESP32...");
            delay(1000);
            ESP.restart();
        }
        return;   // skip this cycle — do not POST garbage data
    }

    // Successful read
    g_consecutiveFail = 0;
    Serial.printf("[DHT22] Temp: %.1f°C  |  Humidity: %.1f%%\n", temperature, humidity);

    sendToFlask(temperature, humidity);
}

// ─────────────────────────────────────────────────────────────
//  POST BOTH VALUES TO FLASK /api/sensor/dht22
// ─────────────────────────────────────────────────────────────
void sendToFlask(float temperature, float humidity) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[HTTP] WiFi unavailable — skip.");
        return;
    }

    String url = String(FLASK_BASE_URL) + "/api/sensor/dht22";

    Serial.print("POST URL: ");
    Serial.println(url);

    // Single JSON payload carries both values
    StaticJsonDocument<128> doc;
    doc["temperature"] = temperature;
    doc["humidity"]    = humidity;

    String body;
    serializeJson(doc, body);

    HTTPClient http;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);
    http.setReuse(false);

    int code = http.POST(body);

    if (code != 200) {
        delay(500);
        code = http.POST(body);
    }

    if (code == 200) {
        Serial.printf("[HTTP] OK → %s\n", http.getString().c_str());
    } else {
        Serial.printf("[HTTP] Code %d | %s\n", code, http.errorToString(code).c_str());
    }

    http.end();
}

// ─────────────────────────────────────────────────────────────
//  WIFI CONNECT
// ─────────────────────────────────────────────────────────────
void connectWiFi() {
    Serial.printf("[WiFi] Connecting to '%s'", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int tries = 0;
    while (WiFi.status() != WL_CONNECTED && tries < 40) {
        delay(500);
        Serial.print(".");
        tries++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WiFi] Failed. Restarting...");
        delay(1000);
        ESP.restart();
    }
}
