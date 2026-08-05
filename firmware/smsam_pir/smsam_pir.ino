#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────
// WIFI CONFIG
// ─────────────────────────────────────────────
const char* WIFI_SSID = "Hacking";
const char* WIFI_PASSWORD = "rhemaonly";
const char* FLASK_BASE_URL = "http://10.69.9.26:5000";


// ─────────────────────────────────────────────
// PIR SENSOR PIN
// ─────────────────────────────────────────────
const int pirPin = 27;

// ─────────────────────────────────────────────
// TIMING
// ─────────────────────────────────────────────
unsigned long lastSend = 0;
const unsigned long SEND_INTERVAL = 500;

// ─────────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(pirPin, INPUT);

  connectWiFi();

  Serial.println("[SYSTEM] PIR Sensor Ready");
}

// ─────────────────────────────────────────────
// LOOP
// ─────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  int motion = digitalRead(pirPin);

  if (motion == HIGH) {
    Serial.println("Motion detected!");
  } else {
    Serial.println("No motion");
  }

  // send to Flask every interval
  if (now - lastSend >= SEND_INTERVAL) {
    lastSend = now;
    sendToFlask(motion);
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Reconnecting...");
    connectWiFi();
  }

  delay(1000);
}

// ─────────────────────────────────────────────
// SEND DATA TO FLASK
// ─────────────────────────────────────────────
void sendToFlask(int motion) {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] No WiFi");
    return;
  }

  HTTPClient http;

  String url = String(FLASK_BASE_URL) + "/api/sensor/motion";

  Serial.print("POST URL: ");
  Serial.println(url);

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<128> doc;
  doc["motion_detected"] = (motion == HIGH);

  String body;
  serializeJson(doc, body);

  int code = http.POST(body);

  if (code == 200) {
    Serial.println("[HTTP] Sent OK (200)");
  } else {
    Serial.printf("[HTTP] Failed (%d)\n", code);
    Serial.println(http.getString());
  }

  http.end();
}
// ─────────────────────────────────────────────
// WIFI CONNECT
// ─────────────────────────────────────────────
void connectWiFi() {
  Serial.printf("\n[WiFi] Connecting to %s", WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Failed. Restarting...");
    ESP.restart();
  }
}