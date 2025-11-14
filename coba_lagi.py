import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# Try to import plotly, if not available use matplotlib
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly tidak terinstall. Menggunakan matplotlib sebagai alternatif.")

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="Smart Energy Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOM ====================
st.markdown("""
<style>
    /* ===== GLOBAL STYLES ===== */
    .main {
        background-color: #1a1a1a;
    }
    
    .stApp {
        background: linear-gradient(135deg, #2c1810 0%, #3a2619 100%);
    }
    
    /* ===== HEADER STYLES ===== */
    .main-header {
        font-size: 3rem;
        color: #ff9a3c !important;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 900;
        text-shadow: 0 4px 8px rgba(255, 154, 60, 0.4);
        letter-spacing: 2px;
        background: none !important;
        -webkit-text-fill-color: #ff9a3c !important;
    }
    
    /* ===== TAB STYLES ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%);
        padding: 20px;
        border-radius: 25px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(255, 154, 60, 0.2);
        border: 2px solid #ff9a3c;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 16px 32px;
        background-color: #5a3826 !important;
        border-radius: 15px;
        font-weight: 800;
        color: #ffd8b8 !important;
        border: 2px solid #ff9a3c;
        transition: all 0.3s ease;
        font-size: 1.1rem;
        letter-spacing: 1px;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #7a4c32 !important;
        border-color: #ffb366;
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(255, 179, 102, 0.4);
    }

    .stTabs [aria-selected="true"] {
        background-color: #ff9a3c !important;
        color: #3a2619 !important;
        border-color: #ff9a3c;
        box-shadow: 0 8px 25px rgba(255, 154, 60, 0.6);
        transform: translateY(-2px);
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding: 0px;
    }
    
    /* ===== CARD STYLES ===== */
    .metric-card {
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 2px solid #ff9a3c;
        box-shadow: 0 8px 32px rgba(255, 154, 60, 0.15);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(255, 154, 60, 0.25);
        border-color: #ffb366;
    }

    .sensor-card {
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%);
        color: #ffd8b8;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 154, 60, 0.2);
        border: 2px solid #ff9a3c;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .sensor-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #ff9a3c 0%, #ff6b35 100%);
    }
    
    .sensor-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(255, 154, 60, 0.3);
        border-color: #ffb366;
    }

    .energy-card {
        background: linear-gradient(135deg, #3a1f19 0%, #5a2f26 100%);
        color: #ffd8b8;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 107, 53, 0.2);
        border: 2px solid #ff6b35;
        transition: all 0.3s ease;
    }
    
    .energy-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(255, 107, 53, 0.3);
        border-color: #ff8c66;
    }

    .cost-card {
        background: linear-gradient(135deg, #193a2f 0%, #265a46 100%);
        color: #d8ffeb;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(83, 255, 170, 0.2);
        border: 2px solid #53ffaa;
        transition: all 0.3s ease;
    }
    
    .cost-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(83, 255, 170, 0.3);
        border-color: #85ffc4;
    }

    .success-card {
        background: linear-gradient(135deg, #2f3a19 0%, #465a26 100%);
        color: #f8ffd8;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(170, 255, 83, 0.2);
        border: 2px solid #aaff53;
        transition: all 0.3s ease;
    }
    
    .success-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(170, 255, 83, 0.3);
        border-color: #c4ff85;
    }

    /* ===== SECTION STYLES ===== */
    .section-title {
        font-size: 2.2rem;
        color: #ff9a3c !important;
        margin: 2.5rem 0 1.5rem 0;
        border-bottom: 3px solid #ff9a3c;
        padding-bottom: 0.8rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: 1px;
        background: none !important;
        -webkit-text-fill-color: #ff9a3c !important;
        text-shadow: 0 2px 4px rgba(255, 154, 60, 0.3);
    }

    /* ===== ALERT STYLES ===== */
    .alert-box {
        background: linear-gradient(135deg, #3a2f19 0%, #5a4626 100%);
        border-left: 6px solid #ffb366;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(255, 179, 102, 0.2);
        border: 1px solid #ffb366;
        color: #ffd8b8;
    }
    
    .stAlert {
        border-radius: 15px;
        padding: 1.2rem 1.8rem;
        border: 2px solid;
        color: #ffd8b8 !important;
    }

    /* ===== COMPARISON CARD STYLES ===== */
    .comparison-card {
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #ff9a3c;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(255, 154, 60, 0.1);
        transition: all 0.3s ease;
        color: #ffd8b8;
    }
    
    .comparison-card:hover {
        border-color: #ffb366;
        box-shadow: 0 8px 25px rgba(255, 179, 102, 0.2);
        transform: translateX(5px);
    }

    /* ===== BUTTON STYLES ===== */
    .stButton button {
        background: linear-gradient(135deg, #5a3826 0%, #7a4c32 100%);
        color: #ffd8b8 !important;
        border: 2px solid #ff9a3c;
        padding: 0.8rem 2rem;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 154, 60, 0.2);
    }
    
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 154, 60, 0.4);
        border-color: #ffb366;
        background: linear-gradient(135deg, #7a4c32 0%, #5a3826 100%);
    }
    
    .stButton button:active {
        transform: translateY(0);
    }

    /* ===== SIDEBAR STYLES ===== */
    .css-1d391kg {
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%);
        border-right: 2px solid #ff9a3c;
    }
    
    .css-1lcbmhc {
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%);
        border-right: 2px solid #ff9a3c;
    }

    /* ===== PROGRESS BAR STYLES ===== */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #ff9a3c 0%, #ff6b35 100%);
        border-radius: 10px;
        border: 1px solid #ffb366;
    }

    /* ===== METRIC STYLES ===== */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #ff9a3c !important;
        text-shadow: 0 2px 4px rgba(255, 154, 60, 0.3);
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 700 !important;
        color: #ffd8b8 !important;
        font-size: 1rem !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    /* ===== DATA FRAME STYLES ===== */
    .dataframe {
        border-radius: 15px !important;
        overflow: hidden;
        box-shadow: 0 6px 20px rgba(255, 154, 60, 0.1) !important;
        border: 2px solid #ff9a3c !important;
        background-color: #3a2619 !important;
    }
    
    .dataframe thead th {
        background: linear-gradient(135deg, #5a3826 0%, #7a4c32 100%) !important;
        color: #ffd8b8 !important;
        font-weight: 800 !important;
        border: 1px solid #ff9a3c !important;
        font-size: 1rem !important;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #3a2619 !important;
    }
    
    .dataframe tbody tr:nth-child(odd) {
        background-color: #2c1810 !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: #5a3826 !important;
        transform: scale(1.01);
        transition: all 0.2s ease;
    }
    
    .dataframe tbody td {
        color: #ffd8b8 !important;
        border: 1px solid #5a3826 !important;
        font-weight: 600 !important;
    }

    /* ===== EXPANDER STYLES ===== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%) !important;
        border-radius: 12px !important;
        border: 2px solid #ff9a3c !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        color: #ffd8b8 !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #ffb366 !important;
        background: linear-gradient(135deg, #5a3826 0%, #7a4c32 100%) !important;
        transform: translateY(-2px);
    }

    /* ===== NUMBER INPUT STYLES ===== */
    .stNumberInput input {
        border-radius: 12px !important;
        border: 2px solid #ff9a3c !important;
        padding: 0.8rem 1.2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        background-color: #3a2619 !important;
        color: #ffd8b8 !important;
    }
    
    .stNumberInput input:focus {
        border-color: #ffb366 !important;
        box-shadow: 0 0 0 3px rgba(255, 179, 102, 0.2) !important;
    }

    /* ===== SLIDER STYLES ===== */
    .stSlider [data-baseweb="slider"] {
        color: #ff9a3c !important;
    }
    
    .stSlider [data-baseweb="thumb"] {
        background: linear-gradient(135deg, #ff9a3c 0%, #ff6b35 100%) !important;
        border: 3px solid #ffd8b8 !important;
        box-shadow: 0 3px 10px rgba(255, 154, 60, 0.4) !important;
    }
    
    .stSlider [data-baseweb="track"] {
        background-color: #5a3826 !important;
        border: 1px solid #ff9a3c !important;
    }

    /* ===== SELECT BOX STYLES ===== */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 12px !important;
        border: 2px solid #ff9a3c !important;
        transition: all 0.3s ease !important;
        background-color: #3a2619 !important;
    }
    
    .stSelectbox [data-baseweb="select"]:hover {
        border-color: #ffb366 !important;
    }
    
    .stSelectbox [data-baseweb="select"] input {
        color: #ffd8b8 !important;
    }

    /* ===== TEXT INPUT STYLES ===== */
    .stTextInput input {
        border-radius: 12px !important;
        border: 2px solid #ff9a3c !important;
        padding: 0.8rem 1.2rem !important;
        transition: all 0.3s ease !important;
        background-color: #3a2619 !important;
        color: #ffd8b8 !important;
        font-weight: 600 !important;
    }
    
    .stTextInput input:focus {
        border-color: #ffb366 !important;
        box-shadow: 0 0 0 3px rgba(255, 179, 102, 0.2) !important;
    }

    /* ===== DOWNLOAD BUTTON STYLES ===== */
    .stDownloadButton button {
        background: linear-gradient(135deg, #3a2619 0%, #5a3826 100%) !important;
        color: #ffd8b8 !important;
        border: 2px solid #53ffaa !important;
        padding: 0.8rem 2rem !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(83, 255, 170, 0.2) !important;
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(83, 255, 170, 0.3) !important;
        border-color: #85ffc4 !important;
        background: linear-gradient(135deg, #5a3826 0%, #3a2619 100%) !important;
    }

    /* ===== MESSAGE STYLES ===== */
    .stSuccess {
        background: linear-gradient(135deg, #2f3a19 0%, #465a26 100%) !important;
        border: 2px solid #aaff53 !important;
        border-radius: 15px !important;
        padding: 1.2rem 1.8rem !important;
        color: #f8ffd8 !important;
    }

    .stError {
        background: linear-gradient(135deg, #3a1f19 0%, #5a2f26 100%) !important;
        border: 2px solid #ff6b35 !important;
        border-radius: 15px !important;
        padding: 1.2rem 1.8rem !important;
        color: #ffd8b8 !important;
    }

    .stInfo {
        background: linear-gradient(135deg, #193a2f 0%, #265a46 100%) !important;
        border: 2px solid #53ffaa !important;
        border-radius: 15px !important;
        padding: 1.2rem 1.8rem !important;
        color: #d8ffeb !important;
    }

    .stWarning {
        background: linear-gradient(135deg, #3a2f19 0%, #5a4626 100%) !important;
        border: 2px solid #ffb366 !important;
        border-radius: 15px !important;
        padding: 1.2rem 1.8rem !important;
        color: #ffd8b8 !important;
    }

    /* ===== TEXT COLOR OVERRIDES ===== */
    .stMarkdown {
        color: #ffd8b8 !important;
    }
    
    p, div, span, label {
        color: #ffd8b8 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffd8b8 !important;
    }
    
    /* Tab text color fix */
    .stTabs [data-baseweb="tab"] * {
        color: inherit !important;
    }

    /* ===== CUSTOM SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #3a2619;
        border-radius: 8px;
        border: 1px solid #ff9a3c;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #ff9a3c 0%, #ff6b35 100%);
        border-radius: 8px;
        border: 1px solid #ffb366;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #ff6b35 0%, #ff9a3c 100%);
    }

    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.2rem;
        }
        
        .section-title {
            font-size: 1.8rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 12px 20px;
            font-size: 0.9rem;
        }
        
        .metric-card, .sensor-card, .energy-card, .cost-card, .success-card {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==================== INISIALISASI DATA ====================
if 'devices' not in st.session_state:
    st.session_state.devices = []
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = []
if 'energy_rate' not in st.session_state:
    st.session_state.energy_rate = 1500
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'energy_target' not in st.session_state:
    st.session_state.energy_target = 300
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []
if 'device_schedule' not in st.session_state:
    st.session_state.device_schedule = {}

# ==================== FUNGSI UTILITAS ====================
def calculate_energy_cost(power_w, hours_per_day, days_per_month, rate_per_kwh):
    energy_kwh = (power_w * hours_per_day * days_per_month) / 1000
    cost = energy_kwh * rate_per_kwh
    return energy_kwh, cost

def calculate_carbon_footprint(energy_kwh):
    """Hitung jejak karbon (kg CO2) - Asumsi: 0.85 kg CO2/kWh"""
    return energy_kwh * 0.85

def check_energy_alerts():
    """Cek dan generate alerts untuk konsumsi tinggi"""
    alerts = []
    total_energy = sum(device["energy"] for device in st.session_state.devices)

    # Alert jika melebihi target
    if total_energy > st.session_state.energy_target:
        alerts.append({
            "type": "warning",
            "message": f"⚠️ Konsumsi energi ({total_energy:.1f} kWh) melebihi target ({st.session_state.energy_target} kWh)!"
        })

    # Alert untuk perangkat high consumption
    for device in st.session_state.devices:
        if device["energy"] > 100:
            alerts.append({
                "type": "info",
                "message": f"💡 {device['name']} memiliki konsumsi tinggi ({device['energy']:.1f} kWh). Pertimbangkan optimasi."
            })

    # Alert untuk sensor anomali
    if st.session_state.sensor_data:
        latest = st.session_state.sensor_data[-1]
        if latest["voltage"] < 210 or latest["voltage"] > 230:
            alerts.append({
                "type": "danger",
                "message": f"⚡ Tegangan abnormal terdeteksi: {latest['voltage']} V!"
            })

    st.session_state.alerts = alerts

def generate_recommendations():
    """Generate rekomendasi penghematan energi"""
    recommendations = []

    if not st.session_state.devices:
        return ["📝 Tambahkan perangkat untuk mendapatkan rekomendasi"]

    # Analisis device dengan konsumsi tertinggi
    sorted_devices = sorted(st.session_state.devices, key=lambda x: x["energy"], reverse=True)

    if sorted_devices:
        top_device = sorted_devices[0]
        recommendations.append(
            f"🎯 **{top_device['name']}** adalah konsumen energi terbesar ({top_device['energy']:.1f} kWh). "
            f"Mengurangi penggunaan 2 jam/hari dapat menghemat Rp {(top_device['cost'] * 0.25):,.0f}/bulan"
        )

    # Rekomendasi umum
    total_energy = sum(device["energy"] for device in st.session_state.devices)

    if total_energy > 200:
        recommendations.append("💡 Pertimbangkan upgrade ke perangkat hemat energi (label A++)")
        recommendations.append("🌙 Manfaatkan tarif listrik off-peak untuk perangkat besar")

    recommendations.append("🔌 Cabut charger dan perangkat standby untuk hemat 5-10% energi")
    recommendations.append("☀️ Maksimalkan pencahayaan alami di siang hari")
    recommendations.append("❄️ Set AC pada suhu 24-25°C untuk efisiensi optimal")

    return recommendations

def create_bar_chart_matplotlib(data, title, x_label, y_label):
    """Create bar chart using matplotlib"""
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(data['name'], data['energy'], 
                 color=plt.cm.viridis(np.linspace(0, 1, len(data))))
    
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)
    ax.set_title(title)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    # Tambahkan nilai di atas bar
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
               f'{height:.1f}', ha='center', va='bottom')
    
    plt.tight_layout()
    return fig

def create_line_chart_matplotlib(data, x_col, y_col, title, x_label, y_label, color='#FF6B6B'):
    """Create line chart using matplotlib"""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data[x_col], data[y_col], 
           color=color, linewidth=3, marker='o')
    
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)
    ax.set_title(title)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def load_sample_data():
    """Data sample yang lebih komprehensif"""
    sample_devices = [
        {"name": "AC Ruang Tamu", "power": 800, "hours": 8, "days": 30, "energy": 192, "cost": 288000},
        {"name": "AC Kamar Tidur", "power": 750, "hours": 6, "days": 30, "energy": 135, "cost": 202500},
        {"name": "Kulkas 2 Pintu", "power": 150, "hours": 24, "days": 30, "energy": 108, "cost": 162000},
        {"name": "LED TV 55 inch", "power": 120, "hours": 6, "days": 30, "energy": 21.6, "cost": 32400},
        {"name": "Water Heater", "power": 350, "hours": 2, "days": 30, "energy": 21, "cost": 31500},
        {"name": "Mesin Cuci", "power": 400, "hours": 1.5, "days": 20, "energy": 12, "cost": 18000},
        {"name": "Lampu LED (10 unit)", "power": 100, "hours": 8, "days": 30, "energy": 24, "cost": 36000},
        {"name": "Rice Cooker", "power": 400, "hours": 2, "days": 30, "energy": 24, "cost": 36000},
        {"name": "Laptop + Charger", "power": 65, "hours": 10, "days": 30, "energy": 19.5, "cost": 29250},
        {"name": "Router WiFi", "power": 10, "hours": 24, "days": 30, "energy": 7.2, "cost": 10800}
    ]

    st.session_state.devices = sample_devices

    # Generate sensor data untuk 24 jam terakhir
    base_time = datetime.now() - timedelta(hours=24)
    sample_sensor = []

    for i in range(48):  # Data setiap 30 menit
        timestamp = base_time + timedelta(minutes=30*i)
        hour = timestamp.hour

        # Simulasi pola konsumsi realistis
        if 6 <= hour < 9:  # Pagi
            power_base = 800
        elif 9 <= hour < 17:  # Siang
            power_base = 500
        elif 17 <= hour < 22:  # Sore-Malam
            power_base = 1200
        else:  # Malam
            power_base = 300

        power = power_base + np.random.randint(-100, 100)
        voltage = 220 + np.random.uniform(-2, 2)
        current = power / voltage
        energy = power * 0.5 / 1000  # kWh untuk 30 menit

        sample_sensor.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M"),
            "voltage": round(voltage, 1),
            "current": round(current, 2),
            "power": power,
            "energy": round(energy, 3),
            "temp": round(26 + np.random.uniform(-2, 4), 1),
            "humidity": round(60 + np.random.uniform(-10, 10), 0)
        })

    st.session_state.sensor_data = sample_sensor

    # Generate historical data (6 bulan terakhir)
    historical = []
    for i in range(6, 0, -1):
        month_ago = datetime.now() - timedelta(days=30*i)
        total_energy = sum(d["energy"] for d in sample_devices) + np.random.uniform(-30, 30)
        historical.append({
            "month": month_ago.strftime("%b %Y"),
            "energy": round(total_energy, 1),
            "cost": round(total_energy * st.session_state.energy_rate, 0)
        })

    st.session_state.historical_data = historical

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3096/3096976.png", width=80)
    st.title("⚡ Smart Energy")
    st.markdown("---")

    st.subheader("🔧 Pengaturan")

    st.session_state.energy_rate = st.number_input(
        "Tarif Listrik (Rp/kWh)",
        min_value=500,
        max_value=5000,
        value=st.session_state.energy_rate,
        step=100,
        help="Tarif listrik PLN per kWh"
    )

    st.session_state.energy_target = st.number_input(
        "Target Konsumsi (kWh/bulan)",
        min_value=50,
        max_value=1000,
        value=st.session_state.energy_target,
        step=50,
        help="Target maksimal konsumsi energi bulanan"
    )

    st.markdown("---")
    st.subheader("🚀 Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Load Demo", use_container_width=True):
            load_sample_data()
            st.success("✅ Data loaded!")
            st.rerun()

    with col2:
        if st.button("🔄 Reset", use_container_width=True, type="secondary"):
            st.session_state.devices = []
            st.session_state.sensor_data = []
            st.session_state.historical_data = []
            st.success("✅ Reset!")
            st.rerun()

    # Download Reports
    st.markdown("---")
    st.subheader("📥 Export Data")

    if st.session_state.devices:
        # Export devices data
        df_devices = pd.DataFrame(st.session_state.devices)
        csv_devices = df_devices.to_csv(index=False)
        st.download_button(
            "📄 Device Report",
            csv_devices,
            "device_report.csv",
            "text/csv",
            use_container_width=True
        )

    if st.session_state.sensor_data:
        # Export sensor data
        df_sensor = pd.DataFrame(st.session_state.sensor_data)
        csv_sensor = df_sensor.to_csv(index=False)
        st.download_button(
            "📡 Sensor Data",
            csv_sensor,
            "sensor_data.csv",
            "text/csv",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; font-size: 0.9em;'>
    <strong>👨‍💻 Developers</strong><br>
    <b>M. Givari R. Kagira</b><br>
    NIM: 241734018<br><br>
    <b>Hanif Nur Hakim</b><br>
    NIM: 241734008<br><br>
    <em>D4-Teknik Konservasi Energi</em>
    </div>
    """, unsafe_allow_html=True)

# ==================== HEADER ====================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h1 class="main-header">⚡ SMART ENERGY MONITOR </h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1em;'><strong>Sistem Monitoring & Optimasi Konsumsi Energi Pintar</strong></p>", unsafe_allow_html=True)

# Check alerts
check_energy_alerts()

# Display alerts if any
if st.session_state.alerts:
    for alert in st.session_state.alerts[:3]:  # Show max 3 alerts
        if alert["type"] == "warning":
            st.warning(alert["message"])
        elif alert["type"] == "info":
            st.info(alert["message"])
        elif alert["type"] == "danger":
            st.error(alert["message"])

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Dashboard",
    "📊 Devices", 
    "📈 Analytics",
    "🎯 Optimization",
    "📅 Historical",
    "🔧 Manage",
    "📡 ESP32 IoT"
])

with tab1:
    # ==================== DASHBOARD UTAMA ====================
    st.markdown('<div class="section-title">📊 Overview Konsumsi Energi Real-time</div>', unsafe_allow_html=True)

    total_energy = sum(device["energy"] for device in st.session_state.devices)
    total_cost = sum(device["cost"] for device in st.session_state.devices)
    device_count = len(st.session_state.devices)
    carbon_footprint = calculate_carbon_footprint(total_energy)

    if st.session_state.sensor_data:
        current_power = st.session_state.sensor_data[-1]["power"]
        current_temp = st.session_state.sensor_data[-1]["temp"]
        current_voltage = st.session_state.sensor_data[-1]["voltage"]
        current_current = st.session_state.sensor_data[-1]["current"]
    else:
        current_power = 0
        current_temp = 25
        current_voltage = 220
        current_current = 0

    # KPI Cards Row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="sensor-card">
            <h3>🔋 Total Energi</h3>
            <h2>{total_energy:.1f} kWh</h2>
            <p>Bulanan • {device_count} Devices</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="cost-card">
            <h3>💰 Biaya Total</h3>
            <h2>Rp {total_cost:,.0f}</h2>
            <p>Per Bulan</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="energy-card">
            <h3>⚡ Daya Real-time</h3>
            <h2>{current_power} W</h2>
            <p>{current_voltage} V • {current_current:.1f} A</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="success-card">
            <h3>🌱 Carbon</h3>
            <h2>{carbon_footprint:.1f} kg</h2>
            <p>CO₂ per bulan</p>
        </div>
        """, unsafe_allow_html=True)

    # Progress to Target
    st.markdown("---")
    progress_pct = min((total_energy / st.session_state.energy_target) * 100, 100)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🎯 Progress ke Target Bulanan")
        st.progress(progress_pct / 100)
    with col2:
        st.metric("Target Status", f"{progress_pct:.0f}%",
                 f"{total_energy - st.session_state.energy_target:.0f} kWh")

    # Charts Row
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Konsumsi Energi per Device")
        if st.session_state.devices:
            df_devices = pd.DataFrame(st.session_state.devices)
            
            if PLOTLY_AVAILABLE:
                # Gunakan Plotly jika tersedia
                fig = px.bar(df_devices,
                            x='name',
                            y='energy',
                            color='energy',
                            color_continuous_scale='Viridis',
                            labels={'energy': 'Energi (kWh)', 'name': 'Perangkat'})
                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback ke matplotlib
                fig = create_bar_chart_matplotlib(
                    df_devices, 
                    'Konsumsi Energi per Device',
                    'Perangkat', 
                    'Energi (kWh)'
                )
                st.pyplot(fig)

    with col2:
        st.markdown("#### ⚡ Real-time Power Consumption")
        if st.session_state.sensor_data and len(st.session_state.sensor_data) > 1:
            df_sensor = pd.DataFrame(st.session_state.sensor_data[-20:])  # Last 20 readings
            
            if PLOTLY_AVAILABLE:
                # Gunakan Plotly jika tersedia
                fig = px.line(df_sensor,
                             x='timestamp',
                             y='power',
                             markers=True,
                             labels={'power': 'Daya (W)', 'timestamp': 'Waktu'})
                fig.update_traces(line_color='#FF6B6B', line_width=3)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback ke matplotlib
                fig = create_line_chart_matplotlib(
                    df_sensor,
                    'timestamp',
                    'power',
                    'Real-time Power Consumption',
                    'Waktu',
                    'Daya (W)',
                    color='#FF6B6B'
                )
                st.pyplot(fig)
        else:
            st.info("📡 Waiting for sensor data...")

    # Cost breakdown
    st.markdown("---")
    st.markdown("#### 💰 Breakdown Biaya Detail")

    col1, col2, col3 = st.columns(3)

    with col1:
        daily_cost = total_cost / 30
        st.metric("Biaya Harian", f"Rp {daily_cost:,.0f}")

    with col2:
        weekly_cost = total_cost / 4
        st.metric("Biaya Mingguan", f"Rp {weekly_cost:,.0f}")

    with col3:
        yearly_cost = total_cost * 12
        st.metric("Proyeksi Tahunan", f"Rp {yearly_cost:,.0f}")

    # Peak hours analysis
    st.markdown("---")
    st.markdown("#### 🕐 Analisis Peak Hours")

    col1, col2 = st.columns([2, 1])

    with col1:
        peak_info = """
        **Kategori Waktu Penggunaan:**
        - 🌅 **Off-Peak** (22:00 - 06:00): Tarif rendah, ideal untuk charging & perangkat besar
        - ☀️ **Mid-Peak** (06:00 - 17:00): Tarif normal
        - 🌆 **Peak** (17:00 - 22:00): Tarif tertinggi, konsumsi maksimal

        **Rekomendasi:**
        - Gunakan mesin cuci & water heater di jam off-peak
        - Hindari AC bersamaan dengan perangkat besar di peak hours
        """
        st.info(peak_info)

    with col2:
        st.markdown("**Potensi Hemat:**")
        potential_savings = total_cost * 0.20
        st.success(f"Rp {potential_savings:,.0f}/bulan")
        st.caption("Dengan optimasi jadwal penggunaan")

with tab2:
    # ==================== DEVICES ====================
    st.markdown('<div class="section-title">📊 Detail Perangkat Elektronik</div>', unsafe_allow_html=True)
    
    if st.session_state.devices:
        # Summary statistics
        total_devices = len(st.session_state.devices)
        total_power = sum(device["power"] for device in st.session_state.devices)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Perangkat", total_devices)
        with col2:
            st.metric("Total Daya", f"{total_power} W")
        with col3:
            st.metric("Energi Total", f"{total_energy:.1f} kWh")
        with col4:
            st.metric("Biaya Total", f"Rp {total_cost:,.0f}")
        
        # Device table
        st.markdown("### 📋 Daftar Perangkat")
        df_devices = pd.DataFrame(st.session_state.devices)
        st.dataframe(df_devices, use_container_width=True)
        
        # Device categories
        st.markdown("### 🗂️ Kategori Perangkat")
        if 'category' in df_devices.columns:
            category_summary = df_devices.groupby('category').agg({
                'energy': 'sum',
                'cost': 'sum',
                'name': 'count'
            }).rename(columns={'name': 'jumlah'})
            st.dataframe(category_summary, use_container_width=True)
    else:
        st.info("📝 Belum ada perangkat yang ditambahkan. Gunakan tab 'Manage' untuk menambah perangkat atau klik 'Load Demo' di sidebar.")

with tab3:
    # ==================== ANALYTICS ====================
    st.markdown('<div class="section-title">📈 Analisis Lanjutan</div>', unsafe_allow_html=True)
    
    if st.session_state.devices:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Distribusi Konsumsi")
            if st.session_state.devices:
                df_devices = pd.DataFrame(st.session_state.devices)
                
                if PLOTLY_AVAILABLE:
                    fig = px.pie(df_devices, values='energy', names='name', 
                                title='Distribusi Konsumsi Energi per Perangkat')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig, ax = plt.subplots(figsize=(8, 8))
                    ax.pie(df_devices['energy'], labels=df_devices['name'], autopct='%1.1f%%')
                    ax.set_title('Distribusi Konsumsi Energi per Perangkat')
                    st.pyplot(fig)
        
        with col2:
            st.markdown("### 🔍 Perbandingan Biaya")
            if st.session_state.devices:
                df_devices = pd.DataFrame(st.session_state.devices)
                
                if PLOTLY_AVAILABLE:
                    fig = px.bar(df_devices, x='name', y='cost',
                                title='Biaya per Perangkat',
                                color='cost',
                                color_continuous_scale='Blues')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(df_devices['name'], df_devices['cost'])
                    ax.set_ylabel('Biaya (Rp)')
                    ax.set_xlabel('Perangkat')
                    ax.set_title('Biaya per Perangkat')
                    ax.tick_params(axis='x', rotation=45)
                    
                    # Format y-axis
                    ax.get_yaxis().set_major_formatter(
                        plt.FuncFormatter(lambda x, p: f'{x:,.0f}')
                    )
                    st.pyplot(fig)
        
        # Efficiency analysis
        st.markdown("### ⚡ Analisis Efisiensi")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_power = sum(device["power"] for device in st.session_state.devices) / len(st.session_state.devices)
            st.metric("Rata-rata Daya", f"{avg_power:.0f} W")
        
        with col2:
            avg_hours = sum(device["hours"] for device in st.session_state.devices) / len(st.session_state.devices)
            st.metric("Rata-rata Jam Pakai", f"{avg_hours:.1f} jam/hari")
        
        with col3:
            efficiency_score = total_energy / (total_power * 0.01)  # Simple efficiency metric
            st.metric("Skor Efisiensi", f"{efficiency_score:.1f}")
    
    else:
        st.info("📊 Tambahkan perangkat untuk melihat analisis")

with tab4:
    # ==================== OPTIMIZATION ====================
    st.markdown('<div class="section-title">🎯 Rekomendasi Optimasi Energi</div>', unsafe_allow_html=True)

    if st.session_state.devices:
        # AI-powered recommendations
        recommendations = generate_recommendations()

        st.markdown("### 🤖 Smart Recommendations")

        for i, rec in enumerate(recommendations, 1):
            with st.container():
                st.markdown(f"""
                <div class="comparison-card">
                    <strong>{i}.</strong> {rec}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Savings calculator
        st.markdown("### 💡 Kalkulator Penghematan")

        col1, col2 = st.columns(2)

        with col1:
            device_to_optimize = st.selectbox(
                "Pilih Perangkat",
                [d["name"] for d in st.session_state.devices]
            )

            current_device = next(d for d in st.session_state.devices if d["name"] == device_to_optimize)

            st.info(f"""
            **Konsumsi Saat Ini:**
            - Jam penggunaan: {current_device['hours']} jam/hari
            - Energi: {current_device['energy']:.1f} kWh/bulan
            - Biaya: Rp {current_device['cost']:,.0f}/bulan
            """)

        with col2:
            st.markdown("**Optimasi:**")

            new_hours = st.slider(
                "Kurangi jam penggunaan",
                0.0,
                float(current_device['hours']),
                float(current_device['hours']) * 0.8,
                0.5
            )

            new_energy, new_cost = calculate_energy_cost(
                current_device['power'],
                new_hours,
                current_device['days'],
                st.session_state.energy_rate
            )

            energy_saved = current_device['energy'] - new_energy
            cost_saved = current_device['cost'] - new_cost

            st.success(f"""
            **Hasil Optimasi:**
            - Energi baru: {new_energy:.1f} kWh/bulan
            - Biaya baru: Rp {new_cost:,.0f}/bulan

            **💰 Penghematan:**
            - Energi: {energy_saved:.1f} kWh ({(energy_saved/current_device['energy']*100):.0f}%)
            - Biaya: Rp {cost_saved:,.0f} ({(cost_saved/current_device['cost']*100):.0f}%)
            - Per tahun: Rp {cost_saved*12:,.0f}
            """)

        # Carbon footprint reduction
        st.markdown("---")
        st.markdown("### 🌱 Dampak Lingkungan")

        col1, col2, col3 = st.columns(3)

        current_carbon = calculate_carbon_footprint(total_energy)
        optimized_carbon = current_carbon * 0.80  # Asumsi 20% reduction
        carbon_saved = current_carbon - optimized_carbon

        with col1:
            st.metric("Current CO₂", f"{current_carbon:.1f} kg/bulan")

        with col2:
            st.metric("Optimized CO₂", f"{optimized_carbon:.1f} kg/bulan",
                     f"-{carbon_saved:.1f} kg")

        with col3:
            trees_equivalent = carbon_saved / 20  # 1 pohon = ~20kg CO2/bulan
            st.metric("Setara dengan", f"{trees_equivalent:.1f} pohon")

        st.info("""
        🌍 **Fun Fact:** Dengan mengoptimalkan konsumsi energi, Anda berkontribusi mengurangi
        emisi karbon setara dengan menanam pohon setiap bulannya!
        """)

    else:
        st.info("🎯 Tambahkan perangkat untuk mendapatkan rekomendasi optimasi")

with tab5:
    # ==================== HISTORICAL DATA ====================
    st.markdown('<div class="section-title">📅 Data Historis & Trend</div>', unsafe_allow_html=True)

    if st.session_state.historical_data:
        df_hist = pd.DataFrame(st.session_state.historical_data)

        # Trend charts dengan matplotlib
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📈 Trend Konsumsi Energi")
            if PLOTLY_AVAILABLE:
                fig = px.line(df_hist, x='month', y='energy',
                             markers=True,
                             labels={'energy': 'Energi (kWh)', 'month': 'Bulan'})
                fig.update_traces(line_color='#667eea', line_width=3, marker_size=10)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(df_hist['month'], df_hist['energy'], 
                       marker='o', linewidth=3, color='#667eea', markersize=8)
                ax.set_ylabel('Energi (kWh)')
                ax.set_xlabel('Bulan')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                st.pyplot(fig)

        with col2:
            st.markdown("#### 💰 Trend Biaya")
            if PLOTLY_AVAILABLE:
                fig = px.bar(df_hist, x='month', y='cost',
                            labels={'cost': 'Biaya (Rp)', 'month': 'Bulan'},
                            color='cost',
                            color_continuous_scale='Blues')
                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar(df_hist['month'], df_hist['cost'], 
                             color=plt.cm.Blues(np.linspace(0.4, 1, len(df_hist))))
                ax.set_ylabel('Biaya (Rp)')
                ax.set_xlabel('Bulan')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(axis='y', alpha=0.3)
                
                # Format y-axis dengan separator ribuan
                ax.get_yaxis().set_major_formatter(
                    plt.FuncFormatter(lambda x, p: f'{x:,.0f}')
                )
                plt.tight_layout()
                st.pyplot(fig)

        # Statistics
        st.markdown("---")
        st.markdown("### 📊 Statistik 6 Bulan Terakhir")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_energy = df_hist['energy'].mean()
            st.metric("Rata-rata Energi", f"{avg_energy:.0f} kWh")

        with col2:
            avg_cost = df_hist['cost'].mean()
            st.metric("Rata-rata Biaya", f"Rp {avg_cost:,.0f}")

        with col3:
            max_energy = df_hist['energy'].max()
            max_month = df_hist.loc[df_hist['energy'].idxmax(), 'month']
            st.metric("Peak Consumption", f"{max_energy:.0f} kWh", max_month)

        with col4:
            min_energy = df_hist['energy'].min()
            min_month = df_hist.loc[df_hist['energy'].idxmin(), 'month']
            st.metric("Lowest Consumption", f"{min_energy:.0f} kWh", min_month)

        # Detailed table
        st.markdown("---")
        st.markdown("### 📋 Data Detail")
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

    else:
        st.info("""
        ## 📅 Belum Ada Data Historis

        Data historis akan terakumulasi seiring waktu penggunaan sistem.
        Klik **"Load Demo"** di sidebar untuk melihat contoh data historis.
        """)

with tab6:
    # ==================== MANAGE DATA ====================
    st.markdown('<div class="section-title">🔧 Kelola Data Perangkat</div>', unsafe_allow_html=True)

    # Add new device
    with st.form("tambah_perangkat_form"):
        st.markdown("### ➕ Tambah Perangkat Baru")

        col1, col2 = st.columns(2)

        with col1:
            device_name = st.text_input("Nama Perangkat", placeholder="AC, Kulkas, TV, dll.")

            device_category = st.selectbox(
                "Kategori",
                ["AC & Pendingin", "Elektronik", "Penerangan", "Dapur", "Lainnya"]
            )

            power_watt = st.number_input("Daya (Watt)", min_value=1, max_value=5000, value=100)

        with col2:
            hours_per_day = st.slider(
                "Jam Penggunaan per Hari",
                0.0, 24.0, 8.0, 0.5,
                help="Berapa lama perangkat digunakan per hari"
            )

            days_per_month = st.number_input(
                "Hari Penggunaan per Bulan",
                min_value=1, max_value=31, value=30,
                help="Berapa hari dalam sebulan perangkat digunakan"
            )

            # Preview calculation
            preview_energy, preview_cost = calculate_energy_cost(
                power_watt, hours_per_day, days_per_month, st.session_state.energy_rate
            )

            st.info(f"""
            **Preview Konsumsi:**
            - Energi: {preview_energy:.1f} kWh/bulan
            - Biaya: Rp {preview_cost:,.0f}/bulan
            """)

        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("💾 Simpan Perangkat", use_container_width=True, type="primary")

        with col2:
            clear = st.form_submit_button("🔄 Clear Form", use_container_width=True)

        if submitted:
            if device_name.strip():
                energy, cost = calculate_energy_cost(
                    power_watt,
                    hours_per_day,
                    days_per_month,
                    st.session_state.energy_rate
                )

                new_device = {
                    "name": device_name,
                    "category": device_category,
                    "power": power_watt,
                    "hours": hours_per_day,
                    "days": days_per_month,
                    "energy": energy,
                    "cost": cost
                }

                st.session_state.devices.append(new_device)
                st.success(f"✅ **{device_name}** berhasil ditambahkan!")
                st.rerun()
            else:
                st.error("❌ Nama perangkat tidak boleh kosong!")

    # Manage existing devices
    if st.session_state.devices:
        st.markdown("---")
        st.markdown("### 📋 Daftar Perangkat Terdaftar")

        for i, device in enumerate(st.session_state.devices):
            with st.expander(f"🔌 {device['name']} - {device['power']}W"):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Kategori:** {device.get('category', 'N/A')}")
                    st.write(f"**Daya:** {device['power']} Watt")
                    st.write(f"**Penggunaan:** {device['hours']} jam/hari × {device['days']} hari/bulan")

                with col2:
                    st.write(f"**Konsumsi:** {device['energy']:.1f} kWh/bulan")
                    st.write(f"**Biaya:** Rp {device['cost']:,.0f}/bulan")

                    # Calculate percentage of total
                    if total_energy > 0:
                        pct = (device['energy'] / total_energy) * 100
                        st.write(f"**Kontribusi:** {pct:.1f}% dari total")

                with col3:
                    if st.button("🗑️ Hapus", key=f"delete_{i}", use_container_width=True):
                        st.session_state.devices.pop(i)
                        st.success("✅ Perangkat dihapus!")
                        st.rerun()

                    if st.button("✏️ Edit", key=f"edit_{i}", use_container_width=True):
                        st.info("Fitur edit akan segera hadir!")

        # Bulk actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Hapus Semua", use_container_width=True, type="secondary"):
                st.session_state.devices = []
                st.success("✅ Semua perangkat dihapus!")
                st.rerun()

        with col2:
            if st.button("📊 Export to CSV", use_container_width=True):
                df = pd.DataFrame(st.session_state.devices)
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "devices_export.csv",
                    "text/csv",
                    use_container_width=True
                )

        with col3:
            if st.button("🔄 Reload Demo", use_container_width=True):
                load_sample_data()
                st.success("✅ Demo data reloaded!")
                st.rerun()

with tab7:
    # ==================== ESP32 IOT ====================
    st.markdown('<div class="section-title">📡 Koneksi ESP32 Smart Sensor IoT</div>', unsafe_allow_html=True)

    # Connection status
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("### 🔗 Status Koneksi Real-time")

        connection_status = st.selectbox(
            "Status Sensor ESP32",
            ["🟢 Connected - Active", "🟡 Connecting...", "🔴 Disconnected"],
            index=0
        )

        if "Connected" in connection_status:
            st.success("✅ ESP32 berhasil terhubung dan streaming data!")

            # Connection details
            st.info("""
            **Connection Info:**
            - IP Address: 192.168.1.100
            - Port: 8080
            - Protocol: HTTP/WebSocket
            - Update Rate: 2 seconds
            - Uptime: 2h 34m 12s
            """)
        elif "Connecting" in connection_status:
            with st.spinner("🔄 Menghubungkan ke ESP32..."):
                st.warning("Mohon tunggu, sedang menghubungkan...")
        else:
            st.error("❌ ESP32 tidak terhubung. Periksa koneksi WiFi dan power supply.")

    with col2:
        st.markdown("### ⚙️ Quick Actions")
        if st.button("🔄 Refresh", use_container_width=True):
            st.success("✅ Connection refreshed!")
            st.rerun()

        if st.button("📡 Scan", use_container_width=True):
            with st.spinner("Scanning..."):
                st.info("ESP32 devices found: 1")

    with col3:
        st.markdown("### 🎛️ Controls")
        if st.button("⏸️ Pause", use_container_width=True):
            st.info("Data streaming paused")

        if st.button("🔴 Stop", use_container_width=True):
            st.warning("Monitoring stopped")

    # Real-time sensor data
    st.markdown("---")
    st.markdown("### 📊 Live Sensor Data")

    if st.session_state.sensor_data:
        latest_data = st.session_state.sensor_data[-1]

        # Sensor metrics grid
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(f"""
            <div class="sensor-card">
                <h3>⚡ Tegangan</h3>
                <h2>{latest_data['voltage']} V</h2>
                <p>AC Power</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="energy-card">
                <h3>🔌 Arus</h3>
                <h2>{latest_data['current']} A</h2>
                <p>Current Flow</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="cost-card">
                <h3>💡 Daya</h3>
                <h2>{latest_data['power']} W</h2>
                <p>Power Usage</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="success-card">
                <h3>🌡️ Suhu</h3>
                <h2>{latest_data['temp']}°C</h2>
                <p>Temperature</p>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <h3>💧 Humidity</h3>
                <h2>{latest_data['humidity']}%</h2>
                <p>Kelembapan</p>
            </div>
            """, unsafe_allow_html=True)

        # Data log table
        st.markdown("---")
        st.markdown("### 📝 Recent Data Log (Last 10 Readings)")

        log_data = []
        for data in st.session_state.sensor_data[-10:][::-1]:  # Last 10, reversed
            log_data.append({
                "Timestamp": data["timestamp"],
                "Voltage": f"{data['voltage']} V",
                "Current": f"{data['current']} A",
                "Power": f"{data['power']} W",
                "Energy": f"{data['energy']:.3f} kWh",
                "Temp": f"{data['temp']}°C",
                "Humidity": f"{data['humidity']}%"
            })

        df_log = pd.DataFrame(log_data)
        st.dataframe(df_log, use_container_width=True, hide_index=True)

        # Download options
        col1, col2 = st.columns(2)

        with col1:
            csv_data = pd.DataFrame(st.session_state.sensor_data).to_csv(index=False)
            st.download_button(
                "📥 Download All Data (CSV)",
                csv_data,
                "esp32_sensor_data_full.csv",
                "text/csv",
                use_container_width=True
            )

        with col2:
            # Download last hour data
            recent_data = st.session_state.sensor_data[-60:]  # Assuming 1min intervals
            csv_recent = pd.DataFrame(recent_data).to_csv(index=False)
            st.download_button(
                "📥 Download Last Hour (CSV)",
                csv_recent,
                "esp32_recent_data.csv",
                "text/csv",
                use_container_width=True
            )

    else:
        st.info("""
        ## 📡 Menunggu Data dari ESP32...

        **Sensor yang akan dimonitor:**
        - ⚡ Tegangan (Voltage)
        - 🔌 Arus (Current)
        - 💡 Daya (Power)
        - 🔋 Energi (Energy)
        - 🌡️ Suhu (Temperature)
        - 💧 Kelembapan (Humidity)

        Pastikan ESP32 sudah terhubung dan mengirim data.
        """)

# ==================== FOOTER ====================
st.markdown("---")

# Footer dengan styling yang benar
st.markdown(
    """
    <div style='
        text-align: center; 
        padding: 2rem; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        border-radius: 15px; 
        color: white;
        margin-top: 2rem;
    '>
        <h2>🎓 Smart Energy Monitor </h2>
        <p style='font-size: 1.1em;'><strong>Project Tugas Akhir - D4 Teknik Konservasi Energi</strong></p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Developer Cards menggunakan columns
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div style='
            background: white; 
            color: #333; 
            padding: 1.5rem; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
        '>
            <h3 style="color: #667eea; margin-bottom: 0.5rem;">Muhammad Givari Ramadhan Kagira</h3>
            <p style="font-size: 1.1em; margin: 0.5rem 0;"><strong>NIM:</strong> 241734018</p>
            <p style="margin: 0;">Full Stack Developer & IoT Specialist</p>
            <p style="font-size: 0.9em; color: #666;">Software Architecture, Frontend, Backend, IoT Integration</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div style='
            background: white; 
            color: #333; 
            padding: 1.5rem; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
        '>
            <h3 style="color: #764ba2; margin-bottom: 0.5rem;">Hanif Nur Hakim</h3>
            <p style="font-size: 1.1em; margin: 0.5rem 0;"><strong>NIM:</strong> 241734008</p>
            <p style="margin: 0;">Hardware Engineer & System Integrator</p>
            <p style="font-size: 0.9em; color: #666;">ESP32 Development, Sensor Integration, Circuit Design</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Info tambahan
st.markdown(
    """
    <div style='
        text-align: center; 
        padding: 1.5rem; 
        background: rgba(255,255,255,0.1); 
        border-radius: 10px; 
        color: white;
        margin-top: 1rem;
    '>
        <p style="font-size: 1em; margin-bottom: 0.5rem;"><strong>📚 Mata Kuliah:</strong> Dasar Pemrograman</p>
        <p style="font-size: 1em; margin-bottom: 0.5rem;"><strong>🏫 Institusi:</strong> Politeknik Negeri Bandung</p>
        <p style="font-size: 1em; margin-bottom: 1rem;"><strong>📅 Tahun:</strong> 2025</p>
        
    </div>
    """, 
    unsafe_allow_html=True
)

# ==================== AUTO-LOAD & INITIALIZATION ====================
if not st.session_state.devices and not st.session_state.sensor_data:
    load_sample_data()
