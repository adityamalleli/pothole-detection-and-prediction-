# ============================================================
# 🔱 AI-BASED POTHOLE PREDICTION SYSTEM
# Python AI Model + Flask Server
# Receives sensor data from ESP32 → Predicts risk → Returns result
# ============================================================

# Install required libraries:
# pip install flask scikit-learn numpy pandas joblib

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from flask import Flask, request, jsonify
import joblib
import json
import os
from datetime import datetime
import threading
import time

# ============================================================
# 🧠 STEP 1 — GENERATE TRAINING DATA
# (In real project, this comes from actual sensor readings)
# ============================================================

def generate_training_data(n_samples=2000):
    """
    Generate realistic synthetic sensor data for training.
    In a real deployment, this would be replaced by actual
    historical sensor data collected from buses.
    """
    np.random.seed(42)
    data = []

    for i in range(n_samples):
        # Generate different road condition scenarios
        scenario = np.random.choice(['good', 'warning', 'critical'],
                                     p=[0.5, 0.3, 0.2])

        if scenario == 'good':
            # Good road conditions
            vibration     = np.random.uniform(0.0, 0.5)
            rain_percent  = np.random.uniform(0, 20)
            temperature   = np.random.uniform(20, 35)
            is_raining    = 1 if rain_percent > 10 else 0
            risk_label    = 0  # LOW

        elif scenario == 'warning':
            # Medium risk conditions
            vibration     = np.random.uniform(0.5, 1.5)
            rain_percent  = np.random.uniform(20, 60)
            temperature   = np.random.uniform(35, 42)
            is_raining    = 1 if rain_percent > 30 else 0
            risk_label    = 1  # MEDIUM

        else:
            # High risk conditions
            vibration     = np.random.uniform(1.5, 5.0)
            rain_percent  = np.random.uniform(50, 100)
            temperature   = np.random.uniform(40, 50)
            is_raining    = 1
            risk_label    = 2  # HIGH

        # Add realistic noise to make it authentic
        vibration    += np.random.normal(0, 0.05)
        rain_percent += np.random.normal(0, 2)
        temperature  += np.random.normal(0, 0.5)

        # Clip to valid ranges
        vibration    = max(0, vibration)
        rain_percent = max(0, min(100, rain_percent))
        temperature  = max(-10, min(60, temperature))

        data.append({
            'vibration':    round(vibration, 3),
            'rain_percent': round(rain_percent, 1),
            'temperature':  round(temperature, 1),
            'is_raining':   is_raining,
            'risk_label':   risk_label
        })

    df = pd.DataFrame(data)
    print(f"✅ Generated {n_samples} training samples")
    print(f"   LOW RISK:    {(df['risk_label']==0).sum()} samples")
    print(f"   MEDIUM RISK: {(df['risk_label']==1).sum()} samples")
    print(f"   HIGH RISK:   {(df['risk_label']==2).sum()} samples")
    return df


# ============================================================
# 🤖 STEP 2 — TRAIN THE AI MODEL
# ============================================================

def train_model():
    """Train Random Forest model on sensor data"""
    print("\n🤖 Training AI Model...")
    print("=" * 50)

    # Generate training data
    df = generate_training_data(2000)

    # Features and labels
    feature_cols = ['vibration', 'rain_percent', 'temperature', 'is_raining']
    X = df[feature_cols].values
    y = df['risk_label'].values

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # Train Random Forest (better than single Decision Tree)
    model = RandomForestClassifier(
        n_estimators=100,    # 100 decision trees
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n✅ Model Training Complete!")
    print(f"   Accuracy: {accuracy*100:.1f}%")
    print(f"\n📊 Classification Report:")
    print(classification_report(y_test, y_pred,
          target_names=['LOW', 'MEDIUM', 'HIGH']))

    # Feature importance
    importances = model.feature_importances_
    print("📈 Feature Importance:")
    for feat, imp in zip(feature_cols, importances):
        bar = '█' * int(imp * 30)
        print(f"   {feat:<15} {bar} {imp*100:.1f}%")

    # Save model and scaler
    joblib.dump(model,  'pothole_model.pkl')
    joblib.dump(scaler, 'pothole_scaler.pkl')
    print("\n💾 Model saved as 'pothole_model.pkl'")

    return model, scaler


# ============================================================
# 🔮 STEP 3 — PREDICTION FUNCTION
# ============================================================

def predict_risk(vibration, rain_percent, temperature, is_raining,
                  model, scaler):
    """
    Predict pothole risk from sensor readings.
    Returns: risk_level, risk_probability, advice
    """
    # Prepare input
    features = np.array([[vibration, rain_percent, temperature, is_raining]])
    features_scaled = scaler.transform(features)

    # Predict
    prediction   = model.predict(features_scaled)[0]
    probabilities = model.predict_proba(features_scaled)[0]

    # Map to labels
    risk_labels = ['LOW', 'MEDIUM', 'HIGH']
    risk_colors = ['🟢', '🟡', '🔴']
    risk_level  = risk_labels[prediction]
    risk_prob   = probabilities[prediction] * 100

    # Generate advice
    advice_map = {
        'LOW':    'Road condition is good. Continue monitoring.',
        'MEDIUM': 'Road showing early signs of stress. Schedule inspection within 2 weeks.',
        'HIGH':   '⚠️ URGENT: High pothole risk! Send repair team within 3-5 days!'
    }

    # Days to pothole estimate
    days_map = {
        'LOW':    '30+ days',
        'MEDIUM': '10-20 days',
        'HIGH':   '3-7 days'
    }

    return {
        'risk_level':       risk_level,
        'risk_probability': round(risk_prob, 1),
        'risk_emoji':       risk_colors[prediction],
        'advice':           advice_map[risk_level],
        'days_to_pothole':  days_map[risk_level],
        'probabilities': {
            'LOW':    round(probabilities[0] * 100, 1),
            'MEDIUM': round(probabilities[1] * 100, 1),
            'HIGH':   round(probabilities[2] * 100, 1)
        }
    }


# ============================================================
# 🌐 STEP 4 — FLASK WEB SERVER
# Receives data from ESP32, returns prediction
# ============================================================

app = Flask(__name__)

# Store for dashboard data
sensor_log = []
alert_log  = []

@app.route('/predict', methods=['POST'])
def predict_endpoint():
    """Receive sensor data from ESP32 and return prediction"""
    try:
        data = request.get_json()
        print(f"\n📥 Received from {data.get('vehicle_id', 'UNKNOWN')}: {data}")

        # Extract sensor values
        vibration    = float(data.get('vibration',    0))
        rain_percent = float(data.get('rain_percent', 0))
        temperature  = float(data.get('temperature',  25))
        is_raining   = 1 if data.get('is_raining', False) else 0
        latitude     = float(data.get('latitude',  17.3850))
        longitude    = float(data.get('longitude', 78.4867))
        vehicle_id   = data.get('vehicle_id', 'UNKNOWN')

        # Get AI prediction
        result = predict_risk(
            vibration, rain_percent, temperature, is_raining,
            model, scaler
        )

        # Add metadata
        result['timestamp']  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result['latitude']   = latitude
        result['longitude']  = longitude
        result['vehicle_id'] = vehicle_id
        result['sensors'] = {
            'vibration':    vibration,
            'rain_percent': rain_percent,
            'temperature':  temperature,
            'is_raining':   bool(is_raining)
        }

        # Log reading
        sensor_log.append(result)
        if len(sensor_log) > 100:
            sensor_log.pop(0)

        # Log alerts separately
        if result['risk_level'] in ['MEDIUM', 'HIGH']:
            alert_log.append(result)
            if len(alert_log) > 50:
                alert_log.pop(0)

        # Print result
        emoji = result['risk_emoji']
        print(f"{emoji} PREDICTION: {result['risk_level']} "
              f"({result['risk_probability']}% confidence)")
        print(f"   {result['advice']}")

        return jsonify(result), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/dashboard', methods=['GET'])
def dashboard_data():
    """Return all logged data for dashboard"""
    return jsonify({
        'total_readings': len(sensor_log),
        'total_alerts':   len(alert_log),
        'recent_readings': sensor_log[-20:],
        'recent_alerts':   alert_log[-10:],
        'risk_summary': {
            'LOW':    sum(1 for r in sensor_log if r['risk_level'] == 'LOW'),
            'MEDIUM': sum(1 for r in sensor_log if r['risk_level'] == 'MEDIUM'),
            'HIGH':   sum(1 for r in sensor_log if r['risk_level'] == 'HIGH'),
        }
    })


@app.route('/test', methods=['GET'])
def test_prediction():
    """Test endpoint — simulate different scenarios"""
    scenarios = [
        {'name': 'Good Road',  'vibration': 0.2, 'rain': 5,  'temp': 28, 'rain_bool': 0},
        {'name': 'After Rain', 'vibration': 0.8, 'rain': 60, 'temp': 32, 'rain_bool': 1},
        {'name': 'HIGH RISK',  'vibration': 2.5, 'rain': 85, 'temp': 44, 'rain_bool': 1},
    ]

    results = []
    for s in scenarios:
        r = predict_risk(s['vibration'], s['rain'], s['temp'],
                          s['rain_bool'], model, scaler)
        r['scenario'] = s['name']
        results.append(r)
        print(f"\n🧪 TEST — {s['name']}: {r['risk_level']} "
              f"({r['risk_probability']}%)")

    return jsonify(results)


@app.route('/simulate', methods=['POST'])
def simulate_sensor():
    """Manually simulate sensor input for demo"""
    data = request.get_json()
    vibration    = float(data.get('vibration',    1.0))
    rain_percent = float(data.get('rain_percent', 50))
    temperature  = float(data.get('temperature',  38))
    is_raining   = int(data.get('is_raining',     1))

    result = predict_risk(vibration, rain_percent, temperature,
                           is_raining, model, scaler)
    result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sensor_log.append(result)

    return jsonify(result)


# ============================================================
# 🎬 STEP 5 — DEMO SIMULATOR
# Auto-generates sensor readings for hackathon demo
# ============================================================

def run_demo_simulator():
    """
    Simulates sensor data automatically every 5 seconds.
    Shows progression from LOW → MEDIUM → HIGH risk.
    Perfect for hackathon demo without physical sensors!
    """
    import requests
    time.sleep(3)  # Wait for server to start

    print("\n🎬 Demo Simulator Starting...")
    print("   Simulating road degradation over time...\n")

    demo_scenarios = [
        # (vibration, rain, temp, label)
        (0.1, 5,  27, "🟢 Smooth road — LOW RISK"),
        (0.2, 8,  28, "🟢 Good road — LOW RISK"),
        (0.4, 15, 30, "🟢 Minor bumps — LOW RISK"),
        (0.7, 35, 35, "🟡 After rain — MEDIUM RISK"),
        (1.0, 55, 38, "🟡 Cracks detected — MEDIUM RISK"),
        (1.5, 70, 41, "🟡 Surface degrading — MEDIUM RISK"),
        (2.0, 80, 43, "🔴 Severe cracks — HIGH RISK!"),
        (2.8, 90, 45, "🔴 Pothole imminent — HIGH RISK!"),
        (3.5, 95, 47, "🔴 CRITICAL — Send repair team NOW!"),
    ]

    for vib, rain, temp, label in demo_scenarios:
        try:
            response = requests.post(
                'http://localhost:5000/simulate',
                json={
                    'vibration': vib,
                    'rain_percent': rain,
                    'temperature': temp,
                    'is_raining': 1 if rain > 30 else 0
                },
                timeout=5
            )
            result = response.json()
            print(f"{label}")
            print(f"   Input  → Vib:{vib}G | Rain:{rain}% | Temp:{temp}°C")
            print(f"   Output → {result['risk_level']} "
                  f"({result['risk_probability']}%) | "
                  f"Pothole in: {result['days_to_pothole']}")
            print(f"   Advice → {result['advice']}\n")
        except Exception as e:
            print(f"⚠️  Simulator error: {e}")

        time.sleep(5)

    print("🎬 Demo simulation complete!")


# ============================================================
# 🚀 MAIN — START EVERYTHING
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🔱 AI-BASED POTHOLE PREDICTION SYSTEM")
    print("=" * 60)

    # Train model
    model, scaler = train_model()

    print("\n" + "=" * 60)
    print("🌐 Starting Flask Server...")
    print("   ESP32 sends data to: http://YOUR_IP:5000/predict")
    print("   Dashboard data at:   http://localhost:5000/dashboard")
    print("   Test predictions at: http://localhost:5000/test")
    print("=" * 60)

    # Start demo simulator in background thread
    demo_thread = threading.Thread(target=run_demo_simulator, daemon=True)
    demo_thread.start()

    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)
