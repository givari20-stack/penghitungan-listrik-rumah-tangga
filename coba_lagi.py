import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="ESP32 Smart Controller",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== INISIALISASI ====================
if 'esp_ip' not in st.session_state:
    st.session_state.esp_ip = "10.203.15.109"  # Default IP
if 'sensor_history' not in st.session_state:
    st.session_state.sensor_history = []
if 'relay_history' not in st.session_state:
    st.session_state.relay_history = []
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "disconnected"
if 'last_data' not in st.session_state:
    st.session_state.last_data = None

# ==================== FUNGSI UTAMA ====================
def test_connection(ip_address):
    """Test koneksi ke ESP32"""
    try:
        url = f"http://{ip_address}/data"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, "✅ Terhubung ke ESP32!", response.json()
        else:
            return False, f"❌ ESP32 merespons tapi error: HTTP {response.status_code}", None
    except requests.exceptions.Timeout:
        return False, "❌ Timeout: ESP32 tidak merespons dalam 5 detik", None
    except requests.exceptions.ConnectionError:
        return False, f"❌ Tidak dapat terhubung ke {ip_address}", None
    except Exception as e:
        return False, f"❌ Error: {str(e)}", None

def get_sensor_data(ip_address):
    """Ambil data sensor dari ESP32"""
    try:
        url = f"http://{ip_address}/data"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Tambah timestamp
            data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['datetime'] = datetime.now()
            
            # Simpan ke history (maksimal 50 data)
            st.session_state.sensor_history.append(data)
            if len(st.session_state.sensor_history) > 50:
                st.session_state.sensor_history = st.session_state.sensor_history[-50:]
            
            st.session_state.last_data = data
            st.session_state.connection_status = "connected"
            return True, data
        else:
            st.session_state.connection_status = "error"
            return False, f"HTTP Error: {response.status_code}"
    except Exception as e:
        st.session_state.connection_status = "error"
        return False, f"Error: {str(e)}"

def control_relay(ip_address, r1=None, r2=None):
    """Kontrol relay ESP32"""
    try:
        params = []
        if r1 is not None:
            params.append(f"r1={r1}")
        if r2 is not None:
            params.append(f"r2={r2}")

        query = "&".join(params)
        url = f"http://{ip_address}/relay?{query}"

        response = requests.get(url, timeout=5)
        
        # Catat aksi relay
        action = {
            'timestamp': datetime.now(),
            'r1': r1,
            'r2': r2,
            'response': response.text,
            'ip_address': ip_address
        }
        st.session_state.relay_history.append(action)
        if len(st.session_state.relay_history) > 20:
            st.session_state.relay_history = st.session_state.relay_history[-20:]
            
        return True, response.text
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_status_color(status):
    """Warna berdasarkan status"""
    if status == "Normal":
        return "🟢"
    elif status == "Gelap":
        return "🔵"
    elif status == "Terang":
        return "🟡"
    else:
        return "⚪"

def create_gauge_chart(value, title, min_val, max_val):
    """Buat gauge chart untuk sensor"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_val, min_val + (max_val-min_val)*0.33], 'color': "lightgray"},
                {'range': [min_val + (max_val-min_val)*0.33, min_val + (max_val-min_val)*0.66], 'color': "gray"},
                {'range': [min_val + (max_val-min_val)*0.66, max_val], 'color': "darkgray"}
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("🏠 ESP32 Controller")
    st.markdown("---")
    
    # Konfigurasi ESP32
    st.subheader("⚙️ Konfigurasi IP ESP32")
    
    # Pilihan IP yang umum
    ip_options = {
        "Campus IP": "10.203.15.109",
        "Home Network": "192.168.1.100", 
        "Hotspot": "192.168.4.1",
        "Localhost": "127.0.0.1",
        "Custom": "custom"
    }
    
    selected_ip_type = st.selectbox("Pilih Tipe Koneksi:", list(ip_options.keys()))
    
    if selected_ip_type == "Custom":
        custom_ip = st.text_input("Masukkan IP Custom:", value="192.168.1.100")
        current_ip = custom_ip
    else:
        current_ip = ip_options[selected_ip_type]
        st.info(f"IP: {current_ip}")
    
    # Update IP jika berubah
    if current_ip != st.session_state.esp_ip:
        st.session_state.esp_ip = current_ip
        st.session_state.connection_status = "disconnected"
        st.success(f"IP diubah ke: {current_ip}")
    
    # Test Koneksi
    st.markdown("---")
    st.subheader("🔗 Test Koneksi")
    
    if st.button("🧪 Test Connection", use_container_width=True, type="primary"):
        with st.spinner(f"Testing koneksi ke {current_ip}..."):
            success, message, data = test_connection(current_ip)
            if success:
                st.success(message)
                st.session_state.connection_status = "connected"
                st.session_state.last_data = data
            else:
                st.error(message)
                st.session_state.connection_status = "error"
    
    # Status Koneksi
    st.markdown("---")
    st.subheader("📊 Status System")
    
    status_color = {
        "connected": "🟢",
        "disconnected": "🔴", 
        "error": "🟡"
    }[st.session_state.connection_status]
    
    st.write(f"Status: {status_color} {st.session_state.connection_status.upper()}")
    st.write(f"IP Active: {st.session_state.esp_ip}")
    st.write(f"Data Points: {len(st.session_state.sensor_history)}")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.sensor_history = []
            st.session_state.relay_history = []
            st.success("History cleared!")
            st.rerun()

# ==================== HEADER ====================
st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 2rem;">
    <h1 style="color: white; margin: 0;">🏠 ESP32 Smart Home Controller</h1>
    <p style="color: rgba(255,255,255,0.8); font-size: 1.2rem; margin: 0.5rem 0 0 0;">
        Real-time Monitoring & Control System
    </p>
</div>
""", unsafe_allow_html=True)

# ==================== TAB UTAMA ====================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🎛️ Control Panel", "📈 Analytics", "🔧 Connection Guide"])

with tab1:
    # ==================== DASHBOARD ====================
    st.subheader("📊 Real-time Sensor Dashboard")
    
    # Status Connection
    col_status, col_refresh = st.columns([3, 1])
    with col_status:
        if st.session_state.connection_status == "connected":
            st.success(f"✅ Terhubung ke ESP32: {st.session_state.esp_ip}")
        elif st.session_state.connection_status == "error":
            st.error(f"❌ Gagal terhubung ke: {st.session_state.esp_ip}")
        else:
            st.warning("⚠️ Belum terhubung ke ESP32")
    
    with col_refresh:
        if st.button("🔄 Refresh Data", key="dashboard_refresh"):
            st.rerun()
    
    # Ambil data jika terhubung
    if st.session_state.connection_status == "connected":
        success, data = get_sensor_data(st.session_state.esp_ip)
        
        if success:
            # Row 1: Sensor Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #ff6b6b, #ee5a52); padding: 1.5rem; border-radius: 15px; text-align: center; color: white;">
                    <h3 style="margin: 0; font-size: 1rem;">🌡️ SUHU</h3>
                    <h1 style="margin: 0.5rem 0; font-size: 2.5rem;">{data['suhu']}°C</h1>
                    <p style="margin: 0; font-size: 0.9rem;">{get_status_color(data['statusSuhu'])} {data['statusSuhu']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4ecdc4, #44a08d); padding: 1.5rem; border-radius: 15px; text-align: center; color: white;">
                    <h3 style="margin: 0; font-size: 1rem;">💡 LDR SENSOR</h3>
                    <h1 style="margin: 0.5rem 0; font-size: 2.5rem;">{data['ldr']}</h1>
                    <p style="margin: 0; font-size: 0.9rem;">{get_status_color(data['statusLDR'])} {data['statusLDR']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                relay1_status = "ON" if data['relay1'] else "OFF"
                relay1_color = "linear-gradient(135deg, #a8e6cf, #56ab91)" if data['relay1'] else "linear-gradient(135deg, #ffd3b6, #ffaaa5)"
                st.markdown(f"""
                <div style="background: {relay1_color}; padding: 1.5rem; border-radius: 15px; text-align: center; color: white;">
                    <h3 style="margin: 0; font-size: 1rem;">🔌 RELAY 1</h3>
                    <h1 style="margin: 0.5rem 0; font-size: 2.5rem;">{relay1_status}</h1>
                    <p style="margin: 0; font-size: 0.9rem;">Lampu Utama</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                relay2_status = "ON" if data['relay2'] else "OFF"
                relay2_color = "linear-gradient(135deg, #a8e6cf, #56ab91)" if data['relay2'] else "linear-gradient(135deg, #ffd3b6, #ffaaa5)"
                st.markdown(f"""
                <div style="background: {relay2_color}; padding: 1.5rem; border-radius: 15px; text-align: center; color: white;">
                    <h3 style="margin: 0; font-size: 1rem;">🔌 RELAY 2</h3>
                    <h1 style="margin: 0.5rem 0; font-size: 2.5rem;">{relay2_status}</h1>
                    <p style="margin: 0; font-size: 0.9rem;">Lampu Cadangan</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Row 2: Charts
            st.markdown("---")
            st.subheader("📊 Live Charts")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(create_gauge_chart(
                    data['suhu'], "Temperature (°C)", 20, 40
                ), use_container_width=True)
            
            with col2:
                st.plotly_chart(create_gauge_chart(
                    data['ldr'], "LDR Sensor Value", 0, 4000
                ), use_container_width=True)
            
            # Row 3: Raw Data
            st.markdown("---")
            st.subheader("📋 Raw Sensor Data")
            st.json(data)
            
        else:
            st.error(f"❌ Gagal mengambil data: {data}")
    else:
        st.warning("""
        ## 🔌 ESP32 Belum Terhubung
        
        **Silakan lakukan:**
        1. Pilih IP ESP32 yang benar di sidebar
        2. Klik **"Test Connection"** untuk mengecek koneksi
        3. Pastikan ESP32 menyala dan terhubung ke jaringan yang sama
        
        **IP yang umum digunakan:**
        - Campus: `10.203.15.109`
        - Home WiFi: `192.168.1.xxx` 
        - Hotspot: `192.168.4.1`
        """)

with tab2:
    # ==================== CONTROL PANEL ====================
    st.subheader("🎛️ Relay Control Panel")
    
    if st.session_state.connection_status != "connected":
        st.error("❌ Tidak dapat mengontrol relay - ESP32 belum terhubung!")
        st.info("Silakan test koneksi terlebih dahulu di sidebar")
    else:
        st.success(f"✅ Siap mengontrol relay di {st.session_state.esp_ip}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💡 Kontrol Lampu (Relay 1)")
            
            col1a, col1b = st.columns(2)
            with col1a:
                if st.button("🟢 NYALAKAN LAMPU", key="r1_on", use_container_width=True):
                    with st.spinner("Mengontrol relay..."):
                        success, result = control_relay(st.session_state.esp_ip, r1=1)
                        if success:
                            st.success(f"✅ Relay 1 ON: {result}")
                        else:
                            st.error(f"❌ Gagal: {result}")
                        time.sleep(1)
                        st.rerun()
            
            with col1b:
                if st.button("🔴 MATIKAN LAMPU", key="r1_off", use_container_width=True):
                    with st.spinner("Mengontrol relay..."):
                        success, result = control_relay(st.session_state.esp_ip, r1=0)
                        if success:
                            st.info(f"✅ Relay 1 OFF: {result}")
                        else:
                            st.error(f"❌ Gagal: {result}")
                        time.sleep(1)
                        st.rerun()
        
        with col2:
            st.markdown("### 🌬️ Kontrol Kipas (Relay 2)")
            
            col2a, col2b = st.columns(2)
            with col2a:
                if st.button("🟢 NYALAKAN KIPAS", key="r2_on", use_container_width=True):
                    with st.spinner("Mengontrol relay..."):
                        success, result = control_relay(st.session_state.esp_ip, r2=1)
                        if success:
                            st.success(f"✅ Relay 2 ON: {result}")
                        else:
                            st.error(f"❌ Gagal: {result}")
                        time.sleep(1)
                        st.rerun()
            
            with col2b:
                if st.button("🔴 MATIKAN KIPAS", key="r2_off", use_container_width=True):
                    with st.spinner("Mengontrol relay..."):
                        success, result = control_relay(st.session_state.esp_ip, r2=0)
                        if success:
                            st.info(f"✅ Relay 2 OFF: {result}")
                        else:
                            st.error(f"❌ Gagal: {result}")
                        time.sleep(1)
                        st.rerun()
        
        # Bulk Controls
        st.markdown("---")
        st.markdown("### 🔄 Kontrol Kombinasi")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if st.button("🏠 SEMUA ON", key="all_on", use_container_width=True):
                with st.spinner("Menyalakan semua relay..."):
                    success, result = control_relay(st.session_state.esp_ip, r1=1, r2=1)
                    if success:
                        st.success(f"✅ Semua relay ON: {result}")
                    else:
                        st.error(f"❌ Gagal: {result}")
                    time.sleep(1)
                    st.rerun()
        
        with col4:
            if st.button("🌙 SEMUA OFF", key="all_off", use_container_width=True):
                with st.spinner("Mematikan semua relay..."):
                    success, result = control_relay(st.session_state.esp_ip, r1=0, r2=0)
                    if success:
                        st.info(f"✅ Semua relay OFF: {result}")
                    else:
                        st.error(f"❌ Gagal: {result}")
                    time.sleep(1)
                    st.rerun()
        
        with col5:
            if st.button("🔄 TOGGLE SEMUA", key="toggle_all", use_container_width=True):
                # Ambil status terkini dulu
                success, current_data = get_sensor_data(st.session_state.esp_ip)
                if success:
                    new_r1 = 0 if current_data['relay1'] else 1
                    new_r2 = 0 if current_data['relay2'] else 1
                    success, result = control_relay(st.session_state.esp_ip, r1=new_r1, r2=new_r2)
                    if success:
                        st.warning(f"✅ Toggle berhasil: {result}")
                    else:
                        st.error(f"❌ Gagal: {result}")
                time.sleep(1)
                st.rerun()

with tab3:
    # ==================== ANALYTICS ====================
    st.subheader("📈 Sensor Data Analytics")
    
    if len(st.session_state.sensor_history) > 1:
        # Convert to DataFrame
        df = pd.DataFrame(st.session_state.sensor_history)
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌡️ Trend Suhu")
            fig = px.line(df, x='datetime', y='suhu', 
                         title='Perubahan Suhu Over Time',
                         labels={'suhu': 'Suhu (°C)', 'datetime': 'Waktu'})
            fig.update_traces(line_color='#ff6b6b', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 💡 Trend LDR")
            fig = px.line(df, x='datetime', y='ldr',
                         title='Perubahan Nilai LDR Over Time',
                         labels={'ldr': 'Nilai LDR', 'datetime': 'Waktu'})
            fig.update_traces(line_color='#4ecdc4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        st.markdown("---")
        st.subheader("📊 Statistics")
        
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            avg_temp = df['suhu'].mean()
            st.metric("Rata-rata Suhu", f"{avg_temp:.1f}°C")
        
        with col4:
            avg_ldr = df['ldr'].mean()
            st.metric("Rata-rata LDR", f"{avg_ldr:.0f}")
        
        with col5:
            max_temp = df['suhu'].max()
            st.metric("Suhu Tertinggi", f"{max_temp:.1f}°C")
        
        with col6:
            min_ldr = df['ldr'].min()
            st.metric("LDR Terendah", f"{min_ldr:.0f}")
        
        # Data Table
        st.markdown("---")
        st.subheader("📋 Historical Data")
        display_df = df[['timestamp', 'suhu', 'statusSuhu', 'ldr', 'statusLDR', 'relay1', 'relay2']].copy()
        display_df['relay1'] = display_df['relay1'].apply(lambda x: 'ON' if x else 'OFF')
        display_df['relay2'] = display_df['relay2'].apply(lambda x: 'ON' if x else 'OFF')
        st.dataframe(display_df.sort_values('timestamp', ascending=False), use_container_width=True)
        
    else:
        st.info("📊 Kumpulkan lebih banyak data untuk melihat analytics")
        if st.session_state.sensor_history:
            st.json(st.session_state.sensor_history[-1])

with tab4:
    # ==================== CONNECTION GUIDE ====================
    st.subheader("🔧 ESP32 Connection Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 Troubleshooting Steps")
        
        st.markdown("""
        1. **Periksa Jaringan**
           - Pastikan komputer dan ESP32 dalam jaringan yang sama
           - Coba ping IP ESP32 dari command prompt
        
        2. **Periksa IP ESP32**
           - Buka Serial Monitor di Arduino IDE
           - Cek IP address yang ditampilkan ESP32
           - Gunakan IP tersebut di aplikasi ini
        
        3. **Test Koneksi Manual**
           ```bash
           # Test dari browser atau curl
           http://[IP_ESP32]/data
           http://[IP_ESP32]/relay?r1=1
           ```
        
        4. **Common IP Ranges**
           - Campus: `10.x.x.x`
           - Home: `192.168.1.x` 
           - Hotspot: `192.168.4.x`
        """)
    
    with col2:
        st.markdown("### 📡 Endpoint Information")
        
        st.markdown("""
        **ESP32 Endpoints:**
        ```
        GET /data
        → Returns: JSON sensor data
        
        GET /relay?r1=1&r2=0  
        → Control relays (0=OFF, 1=ON)
        ```
        
        **Example Responses:**
        ```json
        // /data response
        {
          "ldr": 2613,
          "statusLDR": "Gelap", 
          "suhu": 25.80,
          "statusSuhu": "Normal",
          "relay1": 0,
          "relay2": 0
        }
        
        // /relay response
        "Relay1: OFF, Relay2: OFF"
        ```
        """)
    
    st.markdown("---")
    st.markdown("### 🔍 Find ESP32 IP")
    
    st.info("""
    **Cara menemukan IP ESP32:**
    1. Buka **Arduino IDE** → **Serial Monitor**
    2. Set baud rate ke **115200**
    3. Reset ESP32, lihat IP yang dicetak
    4. Gunakan IP tersebut di aplikasi ini
    """)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🏠 <strong>ESP32 Smart Home Controller</strong> | Connection: {status} | IP: {ip}</p>
    <p>Dibuat dengan ❤️ menggunakan Streamlit</p>
</div>
""".format(
    status=st.session_state.connection_status.upper(),
    ip=st.session_state.esp_ip
), unsafe_allow_html=True)
