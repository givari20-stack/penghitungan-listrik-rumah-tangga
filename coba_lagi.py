import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import requests

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

# ==================== INISIALISASI ESP32 ====================
if 'esp32_connected' not in st.session_state:
    st.session_state.esp32_connected = False
if 'esp32_ip' not in st.session_state:
    st.session_state.esp32_ip = "10.203.15.109"  # IP ESP32 Anda
if 'esp32_port' not in st.session_state:
    st.session_state.esp32_port = 80
if 'esp32_protocol' not in st.session_state:
    st.session_state.esp32_protocol = "HTTP"
if 'esp32_data_interval' not in st.session_state:
    st.session_state.esp32_data_interval = 5

# Inisialisasi status relay
if 'relays' not in st.session_state:
    st.session_state.relays = {
        "relay_1": {"name": "Lampu Utama", "status": False, "pin": "r1"},
        "relay_2": {"name": "Lampu Cadangan", "status": False, "pin": "r2"}
    }

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
        if latest.get("voltage", 220) < 210 or latest.get("voltage", 220) > 230:
            alerts.append({
                "type": "danger",
                "message": f"⚡ Tegangan abnormal terdeteksi: {latest.get('voltage', 220)} V!"
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

# ==================== FUNGSI ESP32 YANG SUDAH DIPERBAIKI ====================

def fetch_sensor_data():
    """Ambil data sensor dari ESP32 - FIXED VERSION"""
    try:
        ip = st.session_state.esp32_ip
        url = f"http://{ip}/data"
        
        response = requests.get(url, timeout=3)  # Timeout lebih pendek
        response.raise_for_status()  # Akan raise exception untuk status code 4xx/5xx
        
        data = response.json()
        return True, data
            
    except requests.exceptions.Timeout:
        return False, "Timeout: ESP32 tidak merespons dalam 3 detik"
    except requests.exceptions.ConnectionError:
        return False, f"Tidak dapat terhubung ke ESP32 di {ip}. Pastikan ESP32 hidup dan dalam jaringan yang sama."
    except requests.exceptions.RequestException as e:
        return False, f"Error koneksi: {str(e)}"
    except ValueError as e:
        return False, f"Error parsing JSON: {str(e)}"
    except Exception as e:
        return False, f"Error tidak terduga: {str(e)}"

def control_relay(relay_pin, status):
    """Fungsi untuk mengontrol relay via ESP32 - FIXED VERSION"""
    try:
        ip = st.session_state.esp32_ip
        
        # Format URL sesuai dengan ESP32 endpoint yang berhasil
        url = f"http://{ip}/relay?{relay_pin}={1 if status else 0}"
        
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        
        action = "MENYALA" if status else "MATI"
        relay_name = next((r["name"] for r in st.session_state.relays.values() if r["pin"] == relay_pin), relay_pin)
        return True, f"✅ {relay_name} {action}"
            
    except requests.exceptions.Timeout:
        return False, "❌ Timeout: ESP32 tidak merespons"
    except requests.exceptions.ConnectionError:
        return False, f"❌ Tidak dapat terhubung ke ESP32 di {ip}"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Error koneksi: {str(e)}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def control_multiple_relays(relay_commands):
    """Kontrol multiple relay sekaligus - FIXED VERSION"""
    try:
        ip = st.session_state.esp32_ip
        
        # Build URL dengan multiple parameters
        params = []
        for relay_pin, status in relay_commands.items():
            params.append(f"{relay_pin}={1 if status else 0}")
        
        url = f"http://{ip}/relay?" + "&".join(params)
        
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        
        return True, "✅ Semua relay berhasil dikontrol"
            
    except requests.exceptions.Timeout:
        return False, "❌ Timeout: ESP32 tidak merespons"
    except requests.exceptions.ConnectionError:
        return False, f"❌ Tidak dapat terhubung ke ESP32 di {ip}"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Error koneksi: {str(e)}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def process_sensor_data(esp32_data):
    """Process data dari ESP32 dan update session state"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Map data dari ESP32 ke format kita
        sensor_entry = {
            "timestamp": timestamp,
            "ldr": esp32_data.get("ldr", 0),
            "statusLDR": esp32_data.get("statusLDR", "Tidak diketahui"),
            "suhu": esp32_data.get("suhu", 0),
            "statusSuhu": esp32_data.get("statusSuhu", "Tidak diketahui"),
            "relay1": esp32_data.get("relay1", 0),
            "relay2": esp32_data.get("relay2", 0),
            # Calculate power based on relay status (asumsi 100W per relay aktif)
            "power": (esp32_data.get("relay1", 0) + esp32_data.get("relay2", 0)) * 100,
            "voltage": 220,  # Asumsi tegangan tetap
            "current": ((esp32_data.get("relay1", 0) + esp32_data.get("relay2", 0)) * 100) / 220,
            "energy": 0  # Akan dihitung berdasarkan waktu
        }
        
        # Update relay status berdasarkan data dari ESP32
        st.session_state.relays["relay_1"]["status"] = bool(esp32_data.get("relay1", 0))
        st.session_state.relays["relay_2"]["status"] = bool(esp32_data.get("relay2", 0))
        
        # Tambah ke sensor data history (keep last 100 entries)
        st.session_state.sensor_data.append(sensor_entry)
        if len(st.session_state.sensor_data) > 100:
            st.session_state.sensor_data = st.session_state.sensor_data[-100:]
            
        return True
            
    except Exception as e:
        st.error(f"Error processing sensor data: {str(e)}")
        return False

# ==================== FUNGSI SMART HOME DASHBOARD YANG SUDAH BERHASIL ====================
def smart_home_dashboard():
    """Dashboard sederhana untuk kontrol cepat - USING WORKING CODE"""
    ESP_IP = st.session_state.esp32_ip
    
    st.title("🏠 Smart Home Dashboard")
    st.markdown("---")
    
    # ================= FETCH DATA =================
    def get_data():
        try:
            url = f"http://{ESP_IP}/data"
            r = requests.get(url, timeout=3)
            return r.json()
        except Exception as e:
            st.error(f"Gagal membaca data: {str(e)}")
            return None

    # ================= SEND RELAY COMMAND =================
    def set_relay(r1=None, r2=None):
        try:
            params = []
            if r1 is not None:
                params.append(f"r1={r1}")
            if r2 is not None:
                params.append(f"r2={r2}")

            query = "&".join(params)
            url = f"http://{ESP_IP}/relay?{query}"

            r = requests.get(url, timeout=3)
            return r.text
        except Exception as e:
            return f"Gagal mengirim perintah: {str(e)}"

    # ================= UI =================
    data = get_data()

    if data is None:
        st.error("❌ Gagal membaca ESP32! Pastikan ESP32 hidup dan dalam 1 jaringan.")
        st.info(f"**IP yang digunakan:** {ESP_IP}")
        st.info("**Endpoint yang dicoba:**")
        st.code(f"http://{ESP_IP}/data")
        st.code(f"http://{ESP_IP}/relay?r1=1&r2=0")
    else:
        st.success("✅ Terhubung ke ESP32!")
        
        # Tampilan sensor dalam cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌡️ Suhu", f"{data.get('suhu', 0)}°C", data.get('statusSuhu', ''))
        
        with col2:
            st.metric("💡 LDR", f"{data.get('ldr', 0)}", data.get('statusLDR', ''))
        
        with col3:
            relay1_status = "ON" if data.get('relay1', 0) else "OFF"
            st.metric("🔌 Relay 1", relay1_status)
        
        with col4:
            relay2_status = "ON" if data.get('relay2', 0) else "OFF"
            st.metric("🔌 Relay 2", relay2_status)

        st.markdown("---")
        st.subheader("📊 Data Sensor Lengkap")
        st.json(data)

        st.markdown("---")
        st.subheader("🎛️ Kontrol Relay Cepat")

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💡 Kontrol Lampu")
            if st.button("🟢 Nyalakan Lampu", key="lampu_on", use_container_width=True):
                result = set_relay(r1=1)
                st.success(f"Lampu: {result}")
                st.rerun()
            
            if st.button("🔴 Matikan Lampu", key="lampu_off", use_container_width=True):
                result = set_relay(r1=0)
                st.info(f"Lampu: {result}")
                st.rerun()
        
        with col2:
            st.markdown("#### 🌬️ Kontrol Kipas")
            if st.button("🟢 Nyalakan Kipas", key="kipas_on", use_container_width=True):
                result = set_relay(r2=1)
                st.success(f"Kipas: {result}")
                st.rerun()
            
            if st.button("🔴 Matikan Kipas", key="kipas_off", use_container_width=True):
                result = set_relay(r2=0)
                st.info(f"Kipas: {result}")
                st.rerun()

        # Kontrol kombinasi
        st.markdown("---")
        st.markdown("#### 🔄 Kontrol Kombinasi")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 Semua ON", key="all_on", use_container_width=True):
                result = set_relay(r1=1, r2=1)
                st.success(f"Semua: {result}")
                st.rerun()
        
        with col2:
            if st.button("🌙 Semua OFF", key="all_off", use_container_width=True):
                result = set_relay(r1=0, r2=0)
                st.info(f"Semua: {result}")
                st.rerun()
        
        with col3:
            if st.button("🔄 Toggle Semua", key="toggle_all", use_container_width=True):
                current_r1 = data.get('relay1', 0)
                current_r2 = data.get('relay2', 0)
                result = set_relay(r1=1-current_r1, r2=1-current_r2)
                st.warning(f"Toggle: {result}")
                st.rerun()

# ... (Fungsi load_sample_data dan bagian lainnya tetap sama)

def load_sample_data():
    """Data sample yang lebih komprehensif"""
    sample_devices = [
        {"name": "AC Ruang Tamu", "power": 800, "hours": 8, "days": 30, "energy": 192, "cost": 288000},
        {"name": "AC Kamar Tidur", "power": 750, "hours": 6, "days": 30, "energy": 135, "cost": 202500},
        # ... (data sample lainnya tetap sama)
    ]
    st.session_state.devices = sample_devices

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

    # ESP32 Connection Test
    st.markdown("---")
    st.subheader("📡 Test ESP32")
    
    if st.button("🔍 Test Connection", use_container_width=True):
        with st.spinner("Testing connection to ESP32..."):
            success, result = fetch_sensor_data()
            if success:
                st.success("✅ ESP32 Connected!")
                st.json(result)
                process_sensor_data(result)
            else:
                st.error(f"❌ {result}")

# ... (Bagian utama aplikasi dan tabs lainnya tetap sama)

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🏠 Dashboard",
    "📊 Devices", 
    "📈 Analytics",
    "🎯 Optimization",
    "📅 Historical",
    "🔧 Manage",
    "📡 ESP32 IoT",
    "🏠 Smart Home"  # Tab baru untuk Smart Home Dashboard
])

# Di Tab 7 (ESP32 IoT), ganti dengan kode yang lebih sederhana dan terpercaya
with tab7:
    st.markdown('<div class="section-title">📡 Koneksi ESP32 Smart Sensor IoT</div>', unsafe_allow_html=True)

    # Configuration Section
    st.markdown("### ⚙️ Konfigurasi Koneksi ESP32")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        esp32_ip = st.text_input(
            "🔗 IP Address ESP32",
            value=st.session_state.esp32_ip,
            placeholder="10.203.15.109",
            help="Masukkan IP address ESP32 di jaringan lokal"
        )
        if esp32_ip != st.session_state.esp32_ip:
            st.session_state.esp32_ip = esp32_ip
    
    with col2:
        st.markdown("### 🔗 Test Connection")
        if st.button("🔄 Test & Connect", use_container_width=True, type="primary"):
            with st.spinner("Menghubungkan ke ESP32..."):
                success, result = fetch_sensor_data()
                if success:
                    st.session_state.esp32_connected = True
                    process_sensor_data(result)
                    st.success(f"✅ Terhubung ke {st.session_state.esp32_ip}!")
                    st.json(result)
                else:
                    st.error(f"❌ Gagal: {result}")

    # Gunakan Smart Home Dashboard yang sudah terbukti bekerja
    st.markdown("---")
    smart_home_dashboard()

with tab8:
    # ==================== SMART HOME DASHBOARD ====================
    smart_home_dashboard()

# ... (CSS dan bagian footer tetap sama)

# ==================== CSS CUSTOM ====================
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #8a2be2 !important;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 900;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 16px 32px;
        background-color: #2d2b55 !important;
        border-radius: 15px;
        font-weight: 800;
        color: #d8c3ff !important;
        border: 2px solid #8a2be2;
    }

    .stTabs [aria-selected="true"] {
        background-color: #8a2be2 !important;
        color: #ffffff !important;
    }
    
    .sensor-card, .cost-card, .energy-card, .success-card {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid;
        text-align: center;
    }
    
    .sensor-card { border-color: #667eea; background: rgba(102, 126, 234, 0.1); }
    .cost-card { border-color: #f093fb; background: rgba(240, 147, 251, 0.1); }
    .energy-card { border-color: #f5576c; background: rgba(245, 87, 108, 0.1); }
    .success-card { border-color: #4ecdc4; background: rgba(78, 205, 196, 0.1); }
</style>
""", unsafe_allow_html=True)

# ==================== AUTO-LOAD & INITIALIZATION ====================
if not st.session_state.devices and not st.session_state.sensor_data:
    load_sample_data()
