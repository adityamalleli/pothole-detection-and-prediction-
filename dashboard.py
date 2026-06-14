# ============================================================
# 🔱 AI-BASED POTHOLE PREDICTION SYSTEM
# Streamlit Live Dashboard
# Run: streamlit run dashboard.py
# ============================================================

# Install: pip install streamlit requests plotly pandas

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
from datetime import datetime
import random

# ============================================================
# 🎨 PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🔱 Pothole Prediction System",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .risk-low    { background: #1a4a1a; border-left: 5px solid #00ff00;
                   padding: 15px; border-radius: 8px; margin: 5px 0; }
    .risk-medium { background: #4a3a00; border-left: 5px solid #ffaa00;
                   padding: 15px; border-radius: 8px; margin: 5px 0; }
    .risk-high   { background: #4a0000; border-left: 5px solid #ff0000;
                   padding: 15px; border-radius: 8px; margin: 5px 0; }
    .metric-box  { background: #1e2130; padding: 20px; border-radius: 10px;
                   text-align: center; }
    .big-number  { font-size: 48px; font-weight: bold; }
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 📊 SESSION STATE — Store sensor readings
# ============================================================
if 'readings' not in st.session_state:
    st.session_state.readings = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

# ============================================================
# 🎛️ SIDEBAR — Controls
# ============================================================
with st.sidebar:
    st.title("🔱 Control Panel")
    st.markdown("---")

    # Manual sensor input for demo
    st.subheader("📳 Manual Sensor Input")
    st.caption("Use this to simulate sensor readings for demo")

    vibration    = st.slider("Vibration (G-force)",  0.0, 5.0, 0.5, 0.1)
    rain_percent = st.slider("Rain Level (%)",        0,   100, 20)
    temperature  = st.slider("Temperature (°C)",      15,  50,  30)
    is_raining   = st.checkbox("Is Raining?", value=rain_percent > 30)

    if st.button("🔮 PREDICT RISK", type="primary"):
        st.session_state.trigger_prediction = True

    st.markdown("---")
    st.subheader("🎬 Demo Mode")
    if st.button("▶️ Run Full Demo"):
        st.session_state.run_demo = True

    st.markdown("---")
    st.subheader("🔄 Auto Refresh")
    auto = st.toggle("Live Updates (from ESP32)", value=False)
    if auto:
        server_url = st.text_input("Server URL",
                                    value="http://localhost:5000")

    st.markdown("---")
    st.caption("🔱 AI Pothole Prediction System v1.0")
    st.caption("Built for Smart City Hackathon 2026")

# ============================================================
# 🧠 LOCAL PREDICTION (No server needed for demo)
# ============================================================
def local_predict(vibration, rain_percent, temperature, is_raining):
    """Rule-based prediction for standalone dashboard demo"""
    score = 0

    # Vibration scoring
    if vibration > 2.0:   score += 40
    elif vibration > 1.0: score += 20
    elif vibration > 0.5: score += 10

    # Rain scoring
    if rain_percent > 70:   score += 30
    elif rain_percent > 40: score += 15
    elif rain_percent > 20: score += 5

    # Temperature scoring
    if temperature > 42:   score += 20
    elif temperature > 38: score += 10

    # Combined effect
    if vibration > 1.0 and rain_percent > 40: score += 10

    if score >= 60:
        return {
            'risk_level': 'HIGH',
            'risk_probability': min(95, score),
            'days_to_pothole': '3-7 days',
            'advice': '🚨 URGENT: Send repair team immediately!',
            'probabilities': {'LOW': 5, 'MEDIUM': 15, 'HIGH': 80}
        }
    elif score >= 30:
        return {
            'risk_level': 'MEDIUM',
            'risk_probability': min(75, score + 10),
            'days_to_pothole': '10-20 days',
            'advice': '⚠️ Schedule road inspection within 2 weeks.',
            'probabilities': {'LOW': 20, 'MEDIUM': 60, 'HIGH': 20}
        }
    else:
        return {
            'risk_level': 'LOW',
            'risk_probability': max(60, 90 - score),
            'days_to_pothole': '30+ days',
            'advice': '✅ Road condition is good. Continue monitoring.',
            'probabilities': {'LOW': 80, 'MEDIUM': 15, 'HIGH': 5}
        }

# ============================================================
# 🎬 DEMO SCENARIOS
# ============================================================
demo_scenarios = [
    (0.1, 5,  27, False, "Smooth Highway Road"),
    (0.3, 10, 29, False, "City Road Normal"),
    (0.6, 30, 33, True,  "Road After Light Rain"),
    (1.0, 55, 37, True,  "Damaged Road + Rain"),
    (1.5, 70, 41, True,  "Heavy Rain + Cracks"),
    (2.2, 85, 44, True,  "Severe Road Damage"),
    (3.0, 92, 46, True,  "CRITICAL — Pothole Imminent"),
]

# ============================================================
# 🏠 MAIN DASHBOARD
# ============================================================
st.title("🛣️ AI-Based Pothole Prediction System")
st.caption(f"Smart City Infrastructure Monitoring | "
           f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ============================================================
# 📊 TOP METRICS ROW
# ============================================================
col1, col2, col3, col4 = st.columns(4)

total = len(st.session_state.readings)
low_count    = sum(1 for r in st.session_state.readings
                    if r['risk_level'] == 'LOW')
medium_count = sum(1 for r in st.session_state.readings
                    if r['risk_level'] == 'MEDIUM')
high_count   = sum(1 for r in st.session_state.readings
                    if r['risk_level'] == 'HIGH')

with col1:
    st.metric("📊 Total Readings", total, delta=None)
with col2:
    st.metric("🟢 Low Risk",    low_count)
with col3:
    st.metric("🟡 Medium Risk", medium_count)
with col4:
    st.metric("🔴 High Risk",   high_count,
              delta=f"+{high_count}" if high_count > 0 else None,
              delta_color="inverse")

st.markdown("---")

# ============================================================
# 🔮 PREDICTION PANEL
# ============================================================
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📳 Live Sensor Readings")

    # Sensor gauges
    c1, c2 = st.columns(2)
    with c1:
        vib_color = "🔴" if vibration > 2 else "🟡" if vibration > 1 else "🟢"
        st.metric(f"{vib_color} Vibration", f"{vibration:.1f} G")
        st.metric("🌡️ Temperature", f"{temperature}°C")
    with c2:
        rain_color = "🔴" if rain_percent > 70 else "🟡" if rain_percent > 40 else "🟢"
        st.metric(f"{rain_color} Rain Level", f"{rain_percent}%")
        st.metric("🌧️ Raining", "YES ☔" if is_raining else "NO ☀️")

    # Vibration bar
    st.markdown("**Vibration Intensity:**")
    vib_normalized = min(vibration / 5.0, 1.0)
    bar_color = "#ff4444" if vibration > 2 else "#ffaa00" if vibration > 1 else "#44ff44"
    st.markdown(f"""
    <div style="background:#333; border-radius:10px; height:20px;">
        <div style="background:{bar_color}; width:{vib_normalized*100:.0f}%;
                    height:20px; border-radius:10px; transition:width 0.5s;">
        </div>
    </div>
    <small>{vibration:.2f}G / 5.0G max</small>
    """, unsafe_allow_html=True)

with col_right:
    st.subheader("🤖 AI Prediction Result")

    # Trigger prediction
    trigger = getattr(st.session_state, 'trigger_prediction', False)

    if trigger or total == 0:
        result = local_predict(vibration, rain_percent, temperature,
                                int(is_raining))
        result.update({
            'vibration':    vibration,
            'rain_percent': rain_percent,
            'temperature':  temperature,
            'timestamp':    datetime.now().strftime('%H:%M:%S')
        })
        st.session_state.readings.append(result)
        if result['risk_level'] in ['MEDIUM', 'HIGH']:
            st.session_state.alerts.append(result)
        st.session_state.trigger_prediction = False
    else:
        result = st.session_state.readings[-1] if st.session_state.readings else \
                 local_predict(0.2, 10, 28, 0)

    # Display result
    risk = result['risk_level']
    risk_class = f"risk-{risk.lower()}"
    emoji = "🟢" if risk == "LOW" else "🟡" if risk == "MEDIUM" else "🔴"

    st.markdown(f"""
    <div class="{risk_class}">
        <h2 style="margin:0">{emoji} {risk} RISK</h2>
        <h3 style="margin:5px 0">Confidence: {result['risk_probability']:.0f}%</h3>
        <p style="margin:5px 0">⏰ Pothole in: <b>{result['days_to_pothole']}</b></p>
        <p style="margin:5px 0">{result['advice']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Probability bars
    st.markdown("**Risk Probability Breakdown:**")
    probs = result.get('probabilities', {'LOW': 80, 'MEDIUM': 15, 'HIGH': 5})
    for level, prob in probs.items():
        color = {"LOW": "#44ff44", "MEDIUM": "#ffaa00", "HIGH": "#ff4444"}[level]
        icon  = {"LOW": "🟢",      "MEDIUM": "🟡",      "HIGH": "🔴"}[level]
        st.markdown(f"""
        <div style="display:flex; align-items:center; margin:3px 0;">
            <span style="width:80px">{icon} {level}</span>
            <div style="flex:1; background:#333; border-radius:5px; height:15px; margin:0 10px;">
                <div style="background:{color}; width:{prob}%; height:15px;
                            border-radius:5px;"></div>
            </div>
            <span>{prob:.0f}%</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# 📈 CHARTS ROW
# ============================================================
if len(st.session_state.readings) > 1:
    col_chart1, col_chart2 = st.columns(2)

    df = pd.DataFrame(st.session_state.readings)

    with col_chart1:
        st.subheader("📈 Vibration Trend Over Time")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=df['vibration'],
            mode='lines+markers',
            name='Vibration (G)',
            line=dict(color='#00aaff', width=2),
            marker=dict(size=6)
        ))
        fig.add_hline(y=1.5, line_dash="dash", line_color="orange",
                       annotation_text="Medium Risk Threshold")
        fig.add_hline(y=2.5, line_dash="dash", line_color="red",
                       annotation_text="High Risk Threshold")
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis_title="Vibration (G-force)",
            xaxis_title="Reading #",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        st.subheader("🥧 Risk Distribution")
        risk_counts = df['risk_level'].value_counts()
        fig2 = go.Figure(go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            marker_colors=['#44ff44', '#ffaa00', '#ff4444'],
            hole=0.4
        ))
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ============================================================
# 🗺️ DEMO SCENARIO RUNNER
# ============================================================
if getattr(st.session_state, 'run_demo', False):
    st.subheader("🎬 Running Demo — Road Degradation Simulation")
    progress_bar = st.progress(0)
    status_text  = st.empty()
    result_area  = st.empty()

    for i, (vib, rain, temp, rain_bool, label) in enumerate(demo_scenarios):
        progress_bar.progress((i + 1) / len(demo_scenarios))
        status_text.text(f"Simulating: {label}...")

        result = local_predict(vib, rain, temp, int(rain_bool))
        result.update({
            'vibration':    vib,
            'rain_percent': rain,
            'temperature':  temp,
            'timestamp':    datetime.now().strftime('%H:%M:%S'),
            'location':     label
        })
        st.session_state.readings.append(result)
        if result['risk_level'] in ['MEDIUM', 'HIGH']:
            st.session_state.alerts.append(result)

        emoji = "🟢" if result['risk_level']=="LOW" else \
                "🟡" if result['risk_level']=="MEDIUM" else "🔴"
        result_area.markdown(f"""
        **{emoji} {label}**
        - Vibration: `{vib}G` | Rain: `{rain}%` | Temp: `{temp}°C`
        - Risk: **{result['risk_level']}** ({result['risk_probability']:.0f}%)
        - {result['advice']}
        """)
        time.sleep(1)

    st.session_state.run_demo = False
    st.success("✅ Demo complete! See charts above for full analysis.")
    st.rerun()

# ============================================================
# 🚨 ALERTS LOG
# ============================================================
if st.session_state.alerts:
    st.subheader("🚨 Active Alerts")
    for alert in reversed(st.session_state.alerts[-5:]):
        risk = alert['risk_level']
        emoji = "🟡" if risk == "MEDIUM" else "🔴"
        risk_class = f"risk-{risk.lower()}"
        loc = alert.get('location', 'Unknown Location')
        st.markdown(f"""
        <div class="{risk_class}">
            {emoji} <b>{risk} RISK</b> — {loc} |
            Vibration: {alert['vibration']:.1f}G |
            Rain: {alert['rain_percent']:.0f}% |
            {alert['advice']}
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 📋 RAW DATA TABLE
# ============================================================
if st.session_state.readings and st.checkbox("📋 Show Raw Data Table"):
    df_display = pd.DataFrame(st.session_state.readings)[
        ['timestamp', 'risk_level', 'risk_probability',
         'vibration', 'rain_percent', 'temperature', 'days_to_pothole']
    ]
    st.dataframe(df_display, use_container_width=True)

# ============================================================
# 🔄 CLEAR DATA BUTTON
# ============================================================
col_clear1, col_clear2 = st.columns([4, 1])
with col_clear2:
    if st.button("🗑️ Clear Data"):
        st.session_state.readings = []
        st.session_state.alerts   = []
        st.rerun()
