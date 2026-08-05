// ============================================================
//  SMSAM — ESP32 Ultrasonic Sensor + Buzzer
//  Sketch  : smsam_ultrasonic.ino
//  Hardware: ESP32 Dev Board
//            HC-SR04 Ultrasonic Sensor
//            Active/Passive Buzzer
//
//  Board   : ESP32 Dev Module (Arduino IDE)
//  Libraries required (install via Library Manager):
//            - WiFi          (built-in with ESP32 core)
//            - HTTPClient    (built-in with ESP32 core)
//            - ArduinoJson   (Benoit Blanchon, v6.x)
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────────────────────
//  USER CONFIGURATION  — edit these before uploading
// ─────────────────────────────────────────────────────────────
const char* WIFI_SSID     = "Hacking";
const char* WIFI_PASSWORD = "rhemaonly";
const char* FLASK_BASE_URL = "http://10.69.9.26:5000";

// ─────────────────────────────────────────────────────────────
//  PIN DEFINITIONS
// ─────────────────────────────────────────────────────────────
// HC-SR04
const int PIN_TRIG = 12;    // GPIO12  → HC-SR04 TRIG
const int PIN_ECHO = 13;   // GPIO13 → HC-SR04 ECHO

// Buzzer
const int PIN_BUZZER = 19; // GPIO19 → Buzzer positive leg (GND → GND)

// ─────────────────────────────────────────────────────────────
//  BUZZER / TIMING CONSTANTS
// ─────────────────────────────────────────────────────────────
const float THRESHOLD_SLOW   = 20.0;  // cm — below this: slow beep
const float THRESHOLD_RAPID  =  5.0;  // cm — below this: rapid beep

const int BEEP_FREQ_HZ       = 2000;  // PWM frequency for buzzer tone

// How long each beep lasts (milliseconds)
const int BEEP_DURATION_SLOW  = 150;
const int BEEP_DURATION_RAPID = 60;

// Silence gap between beeps
const int GAP_SLOW  = 600;
const int GAP_RAPID = 80;

// How often to read sensor + send to Flask (milliseconds)
const unsigned long SEND_INTERVAL_MS = 3000;

// ─────────────────────────────────────────────────────────────
//  LEDC (ESP32 PWM) CHANNEL FOR BUZZER
// ─────────────────────────────────────────────────────────────
const int LEDC_CHANNEL    = 0;
const int LEDC_RESOLUTION = 8;   // 8-bit = 0–255 duty

// ─────────────────────────────────────────────────────────────
//  GLOBALS
// ─────────────────────────────────────────────────────────────
float            g_distanceCm      = 0.0;
unsigned long    g_lastSendTime    = 0;
unsigned long    g_lastBeepTime    = 0;
bool             g_buzzerOn        = false;

// ─────────────────────────────────────────────────────────────
//  SETUP
// ─────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  // NEW ESP32 LEDC API
  ledcAttach(PIN_BUZZER, BEEP_FREQ_HZ, LEDC_RESOLUTION);

  ledcWrite(PIN_BUZZER, 0); // OFF at start

  connectWiFi();
}

// ─────────────────────────────────────────────────────────────
//  MAIN LOOP
// ─────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  // ── Read sensor + POST to Flask on interval ─────────────────
  if (now - g_lastSendTime >= SEND_INTERVAL_MS) {
    g_lastSendTime = now;

    g_distanceCm = readUltrasonic();

    if (g_distanceCm > 0) {
      Serial.printf("[SENSOR] Distance: %.1f cm\n", g_distanceCm);
      sendToFlask(g_distanceCm);
    } else {
      Serial.println("[SENSOR] Out-of-range reading — skipped.");
    }

    // Reconnect WiFi if it dropped
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[WiFi] Connection lost. Reconnecting...");
      connectWiFi();
    }
  }

  // ── Buzzer logic (non-blocking) ──────────────────────────────
  updateBuzzer(g_distanceCm, now);
}

// ─────────────────────────────────────────────────────────────
//  FUNCTION: readUltrasonic
//  Returns distance in cm, or -1 on out-of-range / error.
// ─────────────────────────────────────────────────────────────
float readUltrasonic() {
  // Send a 10 µs trigger pulse
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // Measure echo pulse duration (timeout = 30 ms → ~510 cm max)
  long duration = pulseIn(PIN_ECHO, HIGH, 30000);

  Serial.print("Duration: ");
  Serial.println(duration);

  if (duration == 0) {
    return -1;   // Timeout — no object detected
  }

  // Speed of sound: 343 m/s → 0.0343 cm/µs
  // Divide by 2 for round-trip
  float distance = (duration * 0.0343f) / 2.0f;

  // HC-SR04 reliable range: 2 – 400 cm
  if (distance < 2.0f || distance > 400.0f) {
    return -1;
  }

  return distance;
}

// ─────────────────────────────────────────────────────────────
//  FUNCTION: sendToFlask
//  HTTP POST to Flask /api/sensor/ultrasonic
// ─────────────────────────────────────────────────────────────
void sendToFlask(float distanceCm) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi not connected — skipping POST.");
    return;
  }

  String url = String(FLASK_BASE_URL) + "/api/sensor/ultrasonic";

  // Build JSON payload with ArduinoJson
  StaticJsonDocument<128> doc;
  doc["distance_cm"] = distanceCm;

  String jsonBody;
  serializeJson(doc, jsonBody);

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);   // 5-second timeout

  int httpCode = http.POST(jsonBody);

  if (httpCode == 200) {
    String response = http.getString();
    Serial.printf("[HTTP] POST OK (200): %s\n", response.c_str());
  } else if (httpCode > 0) {
    Serial.printf("[HTTP] POST returned %d\n", httpCode);
  } else {
    Serial.printf("[HTTP] POST failed: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();
}

// ─────────────────────────────────────────────────────────────
//  FUNCTION: updateBuzzer
//  Non-blocking buzzer state machine.
//  Runs every loop() iteration — no delay() calls.
//
//  > 20 cm   → silent
//  ≤ 20 cm   → slow beep  (150 ms on / 600 ms off)
//  ≤  5 cm   → rapid beep (60 ms on / 80 ms off)
// ─────────────────────────────────────────────────────────────
void updateBuzzer(float distance, unsigned long now) {
  // Distance ≤ 0 means invalid reading — silence
  if (distance <= 0 || distance > THRESHOLD_SLOW) {
    // Always OFF when out of alert range
    if (g_buzzerOn) {
      ledcWrite(LEDC_CHANNEL, 0);
      g_buzzerOn = false;
    }
    return;
  }

  // Determine timings based on distance zone
  int beepDuration = (distance <= THRESHOLD_RAPID) ? BEEP_DURATION_RAPID : BEEP_DURATION_SLOW;
  int gapDuration  = (distance <= THRESHOLD_RAPID) ? GAP_RAPID           : GAP_SLOW;
  int totalCycle   = beepDuration + gapDuration;

  unsigned long elapsed = now - g_lastBeepTime;

  if (!g_buzzerOn) {
    // We are in the GAP phase — wait until gap expires, then start beep
    if (elapsed >= (unsigned long)gapDuration) {
      ledcWrite(LEDC_CHANNEL, 128);  // 50% duty → audible tone
      g_buzzerOn    = true;
      g_lastBeepTime = now;
    }
  } else {
    // We are in the BEEP phase — wait until beep expires, then silence
    if (elapsed >= (unsigned long)beepDuration) {
      ledcWrite(LEDC_CHANNEL, 0);   // buzzer OFF
      g_buzzerOn    = false;
      g_lastBeepTime = now;
    }
  }
}

// ─────────────────────────────────────────────────────────────
//  FUNCTION: connectWiFi
//  Blocks until connected (or 20 attempts fail → restart).
// ─────────────────────────────────────────────────────────────
void connectWiFi() {
  Serial.println("\n[WiFi] Starting connection...");
  
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);   // important reset
  delay(1000);

  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");

    Serial.print(" Status: ");
    Serial.println(WiFi.status());  // 👈 IMPORTANT DEBUG LINE

    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] CONNECTED!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] FAILED. Final status code:");
    Serial.println(WiFi.status());

    /*
      Common codes:
      1 = NO SSID FOUND
      4 = WRONG PASSWORD
      6 = DISCONNECTED / AUTH FAIL
    */

    delay(3000);
    ESP.restart();
  }
}
