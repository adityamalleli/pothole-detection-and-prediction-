// ============================================================
// 🔱 AI-BASED POTHOLE PREDICTION SYSTEM
// ESP32 Sensor Code
// Sensors: MPU6050 + Rain Sensor + Temperature + GPS
// Sends data to Python AI via Serial / WiFi
// ============================================================

#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <MPU6050.h>
#include <TinyGPS++.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <HardwareSerial.h>

// ============================================================
// 📶 WiFi Credentials — Change these!
// ============================================================
const char* ssid     = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// ============================================================
// 🌐 Server URL — where Python AI is running
// ============================================================
const char* serverURL = "http://192.168.1.100:5000/predict";
// Change IP to your laptop's IP address on same WiFi

// ============================================================
// 📌 PIN DEFINITIONS
// ============================================================
#define RAIN_SENSOR_PIN     34   // Analog pin for rain sensor
#define RAIN_DIGITAL_PIN    35   // Digital pin for rain sensor
#define TEMP_SENSOR_PIN     4    // DS18B20 temperature sensor
#define GPS_RX_PIN          16   // GPS module RX
#define GPS_TX_PIN          17   // GPS module TX
#define LED_GREEN           25   // Green LED = LOW RISK
#define LED_YELLOW          26   // Yellow LED = MEDIUM RISK
#define LED_RED             27   // Red LED = HIGH RISK
#define BUZZER_PIN          14   // Buzzer for HIGH RISK alert

// ============================================================
// 🔧 SENSOR OBJECTS
// ============================================================
MPU6050 mpu;                          // Accelerometer + Gyroscope
OneWire oneWire(TEMP_SENSOR_PIN);
DallasTemperature tempSensor(&oneWire);
HardwareSerial gpsSerial(2);          // GPS on Serial2
TinyGPSPlus gps;

// ============================================================
// 📊 DATA VARIABLES
// ============================================================
float accelX, accelY, accelZ;         // Acceleration values
float gyroX, gyroY, gyroZ;            // Gyroscope values
float vibrationMagnitude = 0;         // Combined vibration
float maxVibration = 0;               // Peak vibration in window
int rainAnalog = 0;                   // Rain sensor analog (0-4095)
int rainPercent = 0;                  // Rain percentage (0-100)
bool isRaining = false;               // Digital rain status
float temperature = 0;               // Road temperature °C
double latitude = 0;                  // GPS latitude
double longitude = 0;                 // GPS longitude
String riskLevel = "LOW";             // AI prediction result
float riskPercent = 0;                // Risk percentage

// ============================================================
// ⏱️ TIMING
// ============================================================
unsigned long lastSendTime = 0;
const long SEND_INTERVAL = 10000;     // Send data every 10 seconds
unsigned long windowStart = 0;
const long WINDOW_SIZE = 5000;        // 5 second vibration window

// Vibration history for trend detection
float vibrationHistory[10] = {0};
int historyIndex = 0;

// ============================================================
// 🚀 SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.println("🔱 Pothole Prediction System Starting...");

  // Initialize pins
  pinMode(RAIN_DIGITAL_PIN, INPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Startup LED test
  blinkAllLEDs();

  // Initialize I2C for MPU6050
  Wire.begin(21, 22);  // SDA=21, SCL=22

  // Initialize MPU6050
  Serial.println("Initializing MPU6050...");
  mpu.initialize();
  if (mpu.testConnection()) {
    Serial.println("✅ MPU6050 Connected!");
    // Set sensitivity: ±8G range for road sensing
    mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_8);
    mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
    // Set DLPF for noise filtering
    mpu.setDLPFMode(MPU6050_DLPF_BW_42);
  } else {
    Serial.println("❌ MPU6050 NOT found! Check wiring.");
  }

  // Initialize Temperature Sensor
  Serial.println("Initializing Temperature Sensor...");
  tempSensor.begin();
  Serial.println("✅ Temperature Sensor Ready!");

  // Initialize GPS
  Serial.println("Initializing GPS...");
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("✅ GPS Serial Started!");

  // Connect to WiFi
  connectWiFi();

  Serial.println("🚀 System Ready! Starting data collection...");
  Serial.println("================================================");

  windowStart = millis();
}

// ============================================================
// 🔄 MAIN LOOP
// ============================================================
void loop() {
  // 1. Read all sensors continuously
  readAccelerometer();
  readRainSensor();
  readGPS();

  // 2. Every SEND_INTERVAL — read temp, calculate, send data
  unsigned long currentTime = millis();
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    readTemperature();
    calculateVibrationTrend();
    printSensorData();
    sendDataToAI();
    resetWindow();
    lastSendTime = currentTime;
  }

  delay(10);  // 100Hz sampling rate
}

// ============================================================
// 📳 READ ACCELEROMETER (MPU6050)
// ============================================================
void readAccelerometer() {
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Convert raw values to G-force (±8G range → divide by 4096)
  accelX = ax / 4096.0;
  accelY = ay / 4096.0;
  accelZ = az / 4096.0;

  // Convert gyro raw to degrees/sec (±500 range → divide by 65.5)
  gyroX = gx / 65.5;
  gyroY = gy / 65.5;
  gyroZ = gz / 65.5;

  // Calculate vibration magnitude (3D vector)
  // Remove gravity component from Z (subtract 1G baseline)
  float zCorrected = accelZ - 1.0;
  vibrationMagnitude = sqrt(
    (accelX * accelX) +
    (accelY * accelY) +
    (zCorrected * zCorrected)
  );

  // Track peak vibration in current window
  if (vibrationMagnitude > maxVibration) {
    maxVibration = vibrationMagnitude;
  }

  // Detect sudden spike (pothole signature)
  if (vibrationMagnitude > 1.5) {  // Threshold for significant event
    Serial.printf("⚠️  VIBRATION SPIKE DETECTED: %.2fG at [%.4f, %.4f]\n",
                  vibrationMagnitude, latitude, longitude);
  }
}

// ============================================================
// 🌧️ READ RAIN SENSOR
// ============================================================
void readRainSensor() {
  rainAnalog = analogRead(RAIN_SENSOR_PIN);  // 0-4095
  isRaining = !digitalRead(RAIN_DIGITAL_PIN); // Active LOW

  // Convert to percentage (4095=dry=0%, 0=soaked=100%)
  rainPercent = map(rainAnalog, 4095, 0, 0, 100);
  rainPercent = constrain(rainPercent, 0, 100);
}

// ============================================================
// 🌡️ READ TEMPERATURE
// ============================================================
void readTemperature() {
  tempSensor.requestTemperatures();
  temperature = tempSensor.getTempCByIndex(0);

  if (temperature == DEVICE_DISCONNECTED_C) {
    temperature = 25.0;  // Default if sensor disconnected
    Serial.println("⚠️  Temperature sensor disconnected, using default");
  }
}

// ============================================================
// 📡 READ GPS
// ============================================================
void readGPS() {
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      if (gps.location.isValid()) {
        latitude  = gps.location.lat();
        longitude = gps.location.lng();
      }
    }
  }

  // Use default Hyderabad location if no GPS fix yet
  if (latitude == 0 && longitude == 0) {
    latitude  = 17.3850;
    longitude = 78.4867;
  }
}

// ============================================================
// 📈 CALCULATE VIBRATION TREND
// ============================================================
void calculateVibrationTrend() {
  // Store current max vibration in history array
  vibrationHistory[historyIndex] = maxVibration;
  historyIndex = (historyIndex + 1) % 10;

  // Calculate trend: is vibration increasing over time?
  float oldAvg = 0, newAvg = 0;
  for (int i = 0; i < 5; i++) {
    oldAvg += vibrationHistory[i];
    newAvg += vibrationHistory[i + 5];
  }
  oldAvg /= 5;
  newAvg /= 5;

  float trend = newAvg - oldAvg;
  if (trend > 0.1) {
    Serial.printf("📈 TREND WARNING: Vibration increasing! Trend=%.2f\n", trend);
  }
}

// ============================================================
// 📤 SEND DATA TO AI MODEL (Python Server)
// ============================================================
void sendDataToAI() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️  WiFi disconnected. Reconnecting...");
    connectWiFi();
    return;
  }

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  // Build JSON payload
  String jsonData = "{";
  jsonData += "\"vibration\":" + String(maxVibration, 3) + ",";
  jsonData += "\"accel_x\":" + String(accelX, 3) + ",";
  jsonData += "\"accel_y\":" + String(accelY, 3) + ",";
  jsonData += "\"accel_z\":" + String(accelZ, 3) + ",";
  jsonData += "\"rain_percent\":" + String(rainPercent) + ",";
  jsonData += "\"is_raining\":" + String(isRaining ? "true" : "false") + ",";
  jsonData += "\"temperature\":" + String(temperature, 1) + ",";
  jsonData += "\"latitude\":" + String(latitude, 6) + ",";
  jsonData += "\"longitude\":" + String(longitude, 6) + ",";
  jsonData += "\"vehicle_id\":\"BUS_001\"";
  jsonData += "}";

  Serial.println("📤 Sending to AI: " + jsonData);

  int httpCode = http.POST(jsonData);

  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("🤖 AI Response: " + response);

    // Parse simple response
    if (response.indexOf("HIGH") >= 0) {
      riskLevel = "HIGH";
      triggerHighRiskAlert();
    } else if (response.indexOf("MEDIUM") >= 0) {
      riskLevel = "MEDIUM";
      setLED("YELLOW");
    } else {
      riskLevel = "LOW";
      setLED("GREEN");
    }
  } else {
    Serial.printf("❌ HTTP Error: %d\n", httpCode);
    // Fallback: local rule-based prediction
    localRulePrediction();
  }

  http.end();
}

// ============================================================
// 🧠 LOCAL RULE-BASED PREDICTION (Fallback without WiFi)
// ============================================================
void localRulePrediction() {
  Serial.println("🧠 Running local rule-based prediction...");

  int riskScore = 0;

  // Rule 1: High vibration
  if (maxVibration > 2.0)      riskScore += 40;
  else if (maxVibration > 1.0) riskScore += 20;
  else if (maxVibration > 0.5) riskScore += 10;

  // Rule 2: Rain/moisture
  if (rainPercent > 70)      riskScore += 30;
  else if (rainPercent > 40) riskScore += 15;
  else if (rainPercent > 20) riskScore += 5;

  // Rule 3: Temperature extremes (thermal stress)
  if (temperature > 42 || temperature < 5) riskScore += 20;
  else if (temperature > 38)               riskScore += 10;

  // Rule 4: Combined vibration + rain = extra risk
  if (maxVibration > 1.0 && rainPercent > 40) riskScore += 10;

  // Determine risk level
  Serial.printf("📊 Local Risk Score: %d/100\n", riskScore);

  if (riskScore >= 60) {
    riskLevel = "HIGH";
    Serial.println("🚨 LOCAL PREDICTION: HIGH RISK!");
    triggerHighRiskAlert();
  } else if (riskScore >= 30) {
    riskLevel = "MEDIUM";
    Serial.println("⚠️  LOCAL PREDICTION: MEDIUM RISK");
    setLED("YELLOW");
  } else {
    riskLevel = "LOW";
    Serial.println("✅ LOCAL PREDICTION: LOW RISK");
    setLED("GREEN");
  }
}

// ============================================================
// 🚨 HIGH RISK ALERT
// ============================================================
void triggerHighRiskAlert() {
  setLED("RED");

  // Sound buzzer 3 times
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
    delay(200);
  }

  Serial.println("🚨 HIGH RISK ALERT TRIGGERED!");
  Serial.printf("   📍 Location: %.6f, %.6f\n", latitude, longitude);
  Serial.printf("   📳 Vibration: %.2fG\n", maxVibration);
  Serial.printf("   🌧️  Rain: %d%%\n", rainPercent);
  Serial.printf("   🌡️  Temp: %.1f°C\n", temperature);
}

// ============================================================
// 💡 LED CONTROL
// ============================================================
void setLED(String color) {
  digitalWrite(LED_GREEN,  LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_RED,    LOW);

  if (color == "GREEN")  digitalWrite(LED_GREEN,  HIGH);
  if (color == "YELLOW") digitalWrite(LED_YELLOW, HIGH);
  if (color == "RED")    digitalWrite(LED_RED,    HIGH);
}

void blinkAllLEDs() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_GREEN,  HIGH);
    digitalWrite(LED_YELLOW, HIGH);
    digitalWrite(LED_RED,    HIGH);
    delay(300);
    digitalWrite(LED_GREEN,  LOW);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED,    LOW);
    delay(300);
  }
}

// ============================================================
// 📋 PRINT SENSOR DATA TO SERIAL MONITOR
// ============================================================
void printSensorData() {
  Serial.println("================================================");
  Serial.println("📊 SENSOR READINGS SNAPSHOT");
  Serial.println("================================================");
  Serial.printf("📳 Vibration (Peak):  %.3f G\n", maxVibration);
  Serial.printf("   AccelX: %.3f G\n", accelX);
  Serial.printf("   AccelY: %.3f G\n", accelY);
  Serial.printf("   AccelZ: %.3f G\n", accelZ);
  Serial.printf("🌧️  Rain Level:        %d%%\n", rainPercent);
  Serial.printf("   Is Raining:        %s\n", isRaining ? "YES" : "NO");
  Serial.printf("🌡️  Temperature:       %.1f °C\n", temperature);
  Serial.printf("📡 GPS Location:      %.6f, %.6f\n", latitude, longitude);
  Serial.printf("⚠️  Risk Level:        %s\n", riskLevel.c_str());
  Serial.println("================================================");
}

// ============================================================
// 🔄 RESET WINDOW FOR NEXT READING
// ============================================================
void resetWindow() {
  maxVibration = 0;
  windowStart = millis();
}

// ============================================================
// 📶 CONNECT TO WIFI
// ============================================================
void connectWiFi() {
  Serial.printf("Connecting to WiFi: %s\n", ssid);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.printf("   IP Address: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n⚠️  WiFi failed. Running in offline mode.");
    Serial.println("   Using local rule-based prediction.");
  }
}
