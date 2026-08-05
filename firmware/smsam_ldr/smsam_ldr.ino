// ============================================================
//  SMSAM — ESP32 LDR Light Sensor
//  Sketch  : smsam_ldr.ino
//
//  Hardware:
//    ESP32 Dev Board
//    LDR + 10kΩ resistor (voltage divider)
//    Wiring:
//      3.3V ──── LDR ──── GPIO34 ──── 10kΩ ──── GND
//
//  Libraries (install via Library Manager):
//    - ArduinoJson by Benoit Blanchon v6.x
//    WiFi + HTTPClient are built into the ESP32 core
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────────────────────
//  USER CONFIGURATION
// ─────────────────────────────────────────────────────────────
const char* WIFI_SSID      = "Hacking";
const char* WIFI_PASSWORD  = "rhemaonly";
const char* FLASK_BASE_URL = "http://10.69.9.26:5000";  // LAN IP of Flask server

// ─────────────────────────────────────────────────────────────
//  PIN & CONSTANTS
// ─────────────────────────────────────────────────────────────
const int PIN_LDR                   = 34;      // GPIO34 — ADC1 input-only pin
const int ADC_MAX                   = 4095;    // ESP32 12-bit ADC
const unsigned long SEND_INTERVAL   = 5000;    // ms between POSTs

// ─────────────────────────────────────────────────────────────
//  GLOBALS
// ─────────────────────────────────────────────────────────────
unsigned long g_lastSend = 0;

// ─────────────────────────────────────────────────────────────
//  SETUP
// ─────────────────────────────────────────────────────────────
void setup() {
    analogReadResolution(12); // Ensure 0–4095
    analogSetAttenuation(ADC_11db); // Allow full voltage range (0–3.3V)

    Serial.begin(115200);
    delay(200);

    pinMode(26, OUTPUT);

    Serial.println("\n[SMSAM-LDR] Light sensor node starting...");
    connectWiFi();
}

// ─────────────────────────────────────────────────────────────
//  LOOP
// ─────────────────────────────────────────────────────────────
void loop() {
    unsigned long now = millis();

    if (now - g_lastSend >= SEND_INTERVAL) {
        g_lastSend = now;

        int raw = analogRead(PIN_LDR);
        Serial.print("[RAW LDR] ");
        Serial.println(raw);

        float pct = readLdrPercent();
        Serial.printf("[LDR] Light level: %.1f%%\n", pct);

        // LED control
        if (pct < 20) {
            digitalWrite(26, HIGH);
        } else {
            digitalWrite(26, LOW);
        }

        sendToFlask(pct);

        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("[WiFi] Lost connection — reconnecting...");
            connectWiFi();
        }
    }
}

// ─────────────────────────────────────────────────────────────
//  READ LDR — returns 0.0–100.0%
//  Higher value = brighter light.
//  Averages 5 ADC samples to reduce noise.
// ─────────────────────────────────────────────────────────────
float readLdrPercent() {
    long sum = 0;

    for (int i = 0; i < 5; i++) {
        sum += analogRead(PIN_LDR);
        delay(2);
    }

    float avg = sum / 5.0;   // FORCE float division
    float pct = (avg / 4095.0) * 100.0;

    return constrain(pct, 0.0, 100.0);
}


// ─────────────────────────────────────────────────────────────
//  POST TO FLASK
// ─────────────────────────────────────────────────────────────
void sendToFlask(float lightPct) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[HTTP] WiFi unavailable — skip.");
        return;
    }

    String url = String(FLASK_BASE_URL) + "/api/sensor/ldr";

    StaticJsonDocument<128> doc;
    doc["light_level"] = lightPct;

    String body;
    serializeJson(doc, body);

    HTTPClient http;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000);
    http.setReuse(false);

    int code = http.POST(body);

    // retry once if failed
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
//  WIFI CONNECT — restarts ESP32 if unreachable after 20 s
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
