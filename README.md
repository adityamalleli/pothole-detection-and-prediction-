# 🔱 AI-Based Pothole Prediction System
## Complete Setup Guide for Hackathon

---

## 📁 FILES IN THIS PROJECT

| File | Purpose |
|------|---------|
| `esp32_pothole_sensor.ino` | Upload to ESP32 hardware |
| `ai_pothole_model.py` | Python AI + Flask server |
| `dashboard.py` | Streamlit live dashboard |
| `README.md` | This setup guide |

---

## 🛒 HARDWARE REQUIRED

| Component | Model | Cost |
|-----------|-------|------|
| Microcontroller | ESP32 Dev Board | ₹350 |
| Accelerometer | MPU-6050 | ₹150 |
| Rain Sensor | FC-37 module | ₹80 |
| Temperature | DS18B20 | ₹80 |
| GPS Module | NEO-6M | ₹300 |
| Green LED | Any 5mm | ₹5 |
| Yellow LED | Any 5mm | ₹5 |
| Red LED | Any 5mm | ₹5 |
| Buzzer | Active buzzer | ₹20 |
| Resistors | 220Ω (×3) | ₹5 |
| Breadboard | Full size | ₹60 |
| Jumper wires | Male-Male pack | ₹40 |
| **TOTAL** | | **~₹1,100** |

---

## 🔌 WIRING CONNECTIONS

### MPU-6050 → ESP32
```
MPU6050 VCC  → ESP32 3.3V
MPU6050 GND  → ESP32 GND
MPU6050 SCL  → ESP32 GPIO 22
MPU6050 SDA  → ESP32 GPIO 21
```

### Rain Sensor → ESP32
```
Rain VCC  → ESP32 3.3V
Rain GND  → ESP32 GND
Rain AO   → ESP32 GPIO 34 (Analog)
Rain DO   → ESP32 GPIO 35 (Digital)
```

### DS18B20 Temperature → ESP32
```
DS18B20 VCC  → ESP32 3.3V
DS18B20 GND  → ESP32 GND
DS18B20 DATA → ESP32 GPIO 4
                (+ 4.7kΩ resistor between DATA and VCC)
```

### GPS NEO-6M → ESP32
```
GPS VCC → ESP32 5V (or 3.3V)
GPS GND → ESP32 GND
GPS TX  → ESP32 GPIO 16 (RX2)
GPS RX  → ESP32 GPIO 17 (TX2)
```

### LEDs → ESP32
```
GREEN  LED → 220Ω → ESP32 GPIO 25
YELLOW LED → 220Ω → ESP32 GPIO 26
RED    LED → 220Ω → ESP32 GPIO 27
BUZZER     →        ESP32 GPIO 14
All GNDs   → ESP32 GND
```

---

## 💻 SOFTWARE SETUP

### Step 1: Install Arduino Libraries
Open Arduino IDE → Tools → Manage Libraries → Search and install:
- `MPU6050` by Electronic Cats
- `TinyGPS++` by Mikal Hart
- `DallasTemperature` by Miles Burton
- `OneWire` by Paul Stoffregen

### Step 2: Install Python Libraries
```bash
pip install flask scikit-learn numpy pandas joblib streamlit plotly requests
```

### Step 3: Setup ESP32 in Arduino IDE
1. File → Preferences → Additional Boards URL:
   `https://dl.espressif.com/dl/package_esp32_index.json`
2. Tools → Board Manager → Search ESP32 → Install
3. Tools → Board → ESP32 Dev Module

### Step 4: Configure WiFi in .ino file
```cpp
const char* ssid     = "YOUR_WIFI_NAME";     // ← Change this
const char* password = "YOUR_WIFI_PASSWORD"; // ← Change this
const char* serverURL = "http://YOUR_LAPTOP_IP:5000/predict"; // ← Change IP
```

### Step 5: Find Your Laptop IP
```bash
# Windows:
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.100)

# Linux/Mac:
ifconfig
# Look for inet address
```

---

## 🚀 HOW TO RUN

### Terminal 1 — Start AI Server:
```bash
python ai_pothole_model.py
```
You should see:
```
✅ Model Training Complete! Accuracy: 94.2%
🌐 Starting Flask Server...
   ESP32 sends data to: http://YOUR_IP:5000/predict
```

### Terminal 2 — Start Dashboard:
```bash
streamlit run dashboard.py
```
Dashboard opens at: `http://localhost:8501`

### Arduino IDE — Upload to ESP32:
1. Open `esp32_pothole_sensor.ino`
2. Select correct COM port
3. Click Upload (→)
4. Open Serial Monitor (115200 baud) to see readings

---

## 🎬 HACKATHON DEMO (WITHOUT HARDWARE)

If you don't have hardware ready, use the dashboard alone:

1. Run: `streamlit run dashboard.py`
2. Click **"▶️ Run Full Demo"** in sidebar
3. Watch the system simulate road degradation:
   - LOW RISK → MEDIUM RISK → HIGH RISK
4. Show judges the live charts and alerts

This is enough to win! Judges want to see the CONCEPT clearly.

---

## 📊 DEMO FLOW FOR JUDGES (5 minutes)

```
Minute 1: Shown the problem
  "Roads fail suddenly → accidents → huge cost"
  Show pothole images, statistics

Minute 2: Show solution concept
  Draw/show the 4-layer architecture diagram
  "We PREDICT before damage, not react after"

Minute 3: Live demo — dashboard
  Run the demo simulator
  Show LOW → MEDIUM → HIGH risk transition
  Point out vibration trend chart

Minute 4: Technical explanation
  Show ESP32 + sensors (physical hardware)
  Explain MPU-6050 detects vibration signature
  Explain GPS filters speed breakers

Minute 5: Scalability pitch
  "Phase 1: Fixed sensors on junctions"
  "Phase 2: City buses as moving sensors"
  "Phase 3: Smartphone crowdsourcing"
  "NISAR satellite data for rural roads"
  "Total cost: ₹1,200 per node vs ₹50L road repair"
```

---

