import streamlit as st
import json
import matplotlib.pyplot as plt
import os
import requests
from datetime import datetime
import pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import socket

st.set_page_config(page_title="Penghitung Konsumsi Listrik", page_icon="⚡", layout="wide")
st.title("⚡ Smart Home Energy Monitoring")

# Inisialisasi session state
if 'alat_listrik' not in st.session_state:
    st.session_state.alat_listrik = []

if 'tarif_listrik' not in st.session_state:
    st.session_state.tarif_listrik = 1500

if 'data_esp32' not in st.session_state:
    st.session_state.data_esp32 = []

if 'server_status' not in st.session_state:
    st.session_state.server_status = "Stopped"

if 'total_energy' not in st.session_state:
    st.session_state.total_energy = 0.0

# Global variables untuk server
httpd = None
server_thread = None

def get_local_ip():
    """Dapatkan IP lokal untuk koneksi ESP32"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def hitung_energi_dan_biaya(daya, jam_per_hari, hari_per_bulan, tarif):
    energi = (daya * jam_per_hari * hari_per_bulan) / 1000
    biaya = energi * tarif
    return energi, biaya

def hitung_biaya_tiered(kwh_total):
    if kwh_total <= 50:
        return kwh_total * 1000
    elif kwh_total <= 100:
        return (50 * 1000) + ((kwh_total - 50) * 1200)
    elif kwh_total <= 200:
        return (50 * 1000) + (50 * 1200) + ((kwh_total - 100) * 1500)
    else:
        return (50 * 1000) + (50 * 1200) + (100 * 1500) + ((kwh_total - 200) * 2000)

def simpan_ke_file():
    try:
        with open("data_listrik.json", "w") as f:
            json.dump(st.session_state.alat_listrik, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")
        return False

def muat_dari_file():
    try:
        if os.path.exists("data_listrik.json"):
            with open("data_listrik.json", "r") as f:
                st.session_state.alat_listrik = json.load(f)
            return True
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
    return False

def simpan_data_esp32():
    try:
        with open("data_esp32.json", "w") as f:
            json.dump(st.session_state.data_esp32, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data ESP32: {e}")
        return False

def muat_data_esp32():
    try:
        if os.path.exists("data_esp32.json"):
            with open("data_esp32.json", "r") as f:
                st.session_state.data_esp32 = json.load(f)
            return True
    except Exception as e:
        st.error(f"Gagal memuat data ESP32: {e}")
    return False

def ekstrak_konten_ai(response_text):
    try:
        data = json.loads(response_text)
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if 'message' in first_item and 'content' in first_item['message']:
                content = first_item['message']['content']
                content = content.replace('\\n', '\n')
                return content
        return response_text.replace('\\n', '\n')
    except json.JSONDecodeError:
        return response_text.replace('\\n', '\n')

# HTTP Server untuk ESP32
class ESP32Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"ESP32 Smart Home Receiver Ready!")
        
        elif self.path == "/status":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                "status": "running",
                "total_records": len(st.session_state.data_esp32),
                "total_energy": st.session_state.total_energy,
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(status).encode())
        
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/esp32-data":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                data = json.loads(post_data.decode('utf-8'))
                
                # Validasi field wajib
                required_fields = ['device_id', 'tegangan', 'arus', 'daya_aktual', 'energi_kwh']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Missing field: {field}")
                
                # Tambahkan timestamp dan hitung biaya
                data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data['biaya'] = data['energi_kwh'] * st.session_state.tarif_listrik
                
                # Simpan data
                st.session_state.data_esp32.append(data)
                st.session_state.total_energy += data['energi_kwh']
                simpan_data_esp32()
                
                # Response sukses
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "status": "success",
                    "message": "Data received successfully",
                    "record_count": len(st.session_state.data_esp32),
                    "total_energy": st.session_state.total_energy
                }
                self.wfile.write(json.dumps(response).encode())
                
                print(f"📡 Data received from {data['device_id']}: {data['energi_kwh']} kWh")
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(error_response).encode())
                
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def run_server():
    global httpd
    try:
        httpd = HTTPServer(('0.0.0.0', 8000), ESP32Handler)
        st.session_state.server_status = "Running"
        print("🚀 ESP32 Server running on port 8000")
        httpd.serve_forever()
    except Exception as e:
        st.session_state.server_status = f"Error: {str(e)}"
        print(f"❌ Server error: {e}")

def start_server():
    global server_thread
    if server_thread is None or not server_thread.is_alive():
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        st.session_state.server_status = "Starting..."
        time.sleep(2)

def stop_server():
    global httpd
    if httpd:
        httpd.shutdown()
        httpd.server_close()
        st.session_state.server_status = "Stopped"
        print("🛑 ESP32 Server stopped")

# Muat data saat startup
if not st.session_state.alat_listrik:
    muat_dari_file()
if not st.session_state.data_esp32:
    muat_data_esp32()

# Sidebar Navigation
st.sidebar.title("🔧 Navigation")
menu = st.sidebar.radio("Pilih Menu:", ["🏠 Dashboard", "📊 Data Manual", "📡 ESP32 Monitor", "📈 Analytics", "💾 Data Management"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Power Settings")
tarif_baru = st.sidebar.number_input("Tarif Listrik (Rp/kWh)", min_value=500, max_value=5000, value=st.session_state.tarif_listrik, step=100)
if tarif_baru != st.session_state.tarif_listrik:
    st.session_state.tarif_listrik = tarif_baru
    st.sidebar.success(f"Tarif diperbarui: Rp {tarif_baru:,.0f}/kWh")

use_tiered = st.sidebar.checkbox("Gunakan Tarif Bertingkat")

# Server Control Section
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 ESP32 Server Control")

local_ip = get_local_ip()
st.sidebar.info(f"**Local IP:** {local_ip}")

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🚀 Start Server", use_container_width=True):
        start_server()
with col_btn2:
    if st.button("🛑 Stop Server", use_container_width=True):
        stop_server()

st.sidebar.write(f"**Status:** {st.session_state.server_status}")
st.sidebar.write(f"**Port:** 8000")
st.sidebar.write(f"**Total Records:** {len(st.session_state.data_esp32)}")
st.sidebar.write(f"**Total Energy:** {st.session_state.total_energy:.6f} kWh")

# Main Content Area
if menu == "🏠 Dashboard":
    st.subheader("🏠 Smart Home Energy Dashboard")
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_manual = sum(item['energi'] for item in st.session_state.alat_listrik)
        st.metric("Manual Energy", f"{total_manual:.2f} kWh")
    
    with col2:
        total_esp32 = st.session_state.total_energy
        st.metric("ESP32 Energy", f"{total_esp32:.6f} kWh")
    
    with col3:
        total_energy = total_manual + total_esp32
        if use_tiered:
            total_cost = hitung_biaya_tiered(total_energy)
        else:
            total_cost = total_energy * st.session_state.tarif_listrik
        st.metric("Total Cost", f"Rp {total_cost:,.0f}")
    
    with col4:
        if st.session_state.data_esp32:
            latest = st.session_state.data_esp32[-1]
            st.metric("Current Power", f"{latest['daya_aktual']} W")
        else:
            st.metric("Current Power", "0 W")
    
    # Real-time Data Display
    if st.session_state.data_esp32:
        st.markdown("### 📊 Real-time Sensor Data")
        latest_data = st.session_state.data_esp32[-1]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Voltage:** {latest_data['tegangan']} V")
            st.info(f"**Current:** {latest_data['arus']} A")
        with col2:
            st.info(f"**Power:** {latest_data['daya_aktual']} W")
            st.info(f"**Energy:** {latest_data['energi_kwh']:.6f} kWh")
        with col3:
            if 'suhu' in latest_data:
                st.info(f"**Temperature:** {latest_data['suhu']} °C")
                st.info(f"**Humidity:** {latest_data.get('kelembapan', 'N/A')} %")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            muat_data_esp32()
            st.rerun()
    with col2:
        if st.button("🤖 Get AI Analysis", use_container_width=True):
            st.session_state.analyze_ai = True

elif menu == "📊 Data Manual":
    st.subheader("📊 Tambah Data Perangkat Manual")
    
    with st.form("tambah_alat_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nama = st.text_input("Nama Perangkat", placeholder="Kulkas, TV, AC, dll.")
            daya = st.number_input("Daya (Watt)", min_value=1, max_value=5000, value=100)
        
        with col2:
            jam_per_hari = st.number_input("Jam/Hari", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
            hari_per_bulan = st.number_input("Hari/Bulan", min_value=1, max_value=31, value=30)
        
        submitted = st.form_submit_button("➕ Tambah Perangkat")
        
        if submitted:
            if nama.strip():
                energi, biaya = hitung_energi_dan_biaya(daya, jam_per_hari, hari_per_bulan, st.session_state.tarif_listrik)
                
                st.session_state.alat_listrik.append({
                    "nama": nama,
                    "daya": daya,
                    "jam_per_hari": jam_per_hari,
                    "hari_per_bulan": hari_per_bulan,
                    "energi": energi,
                    "biaya": biaya
                })
                simpan_ke_file()
                
                st.success(f"✅ {nama} ditambahkan!")
                st.info(f"Konsumsi: {energi:.2f} kWh/bulan, Biaya: Rp {biaya:,.0f}/bulan")
            else:
                st.error("❌ Nama perangkat tidak boleh kosong!")
    
    # Tampilkan data manual
    if st.session_state.alat_listrik:
        st.markdown("### 📋 Data Perangkat Manual")
        df_manual = pd.DataFrame(st.session_state.alat_listrik)
        st.dataframe(df_manual, use_container_width=True)

elif menu == "📡 ESP32 Monitor":
    st.subheader("📡 ESP32 Real-time Monitor")
    
    st.info("""
    **ESP32 Configuration:**
    - **Endpoint:** `http://""" + local_ip + """:8000/api/esp32-data`
    - **Method:** POST
    - **Content-Type:** application/json
    """)
    
    # Connection Guide
    with st.expander("🔧 ESP32 Setup Guide"):
        st.markdown("""
        **Format data yang dikirim ESP32:**
        ```json
        {
          "device_id": "ESP32_SmartHome",
          "tegangan": 220.5,
          "arus": 1.2,
          "daya_aktual": 264.6,
          "energi_kwh": 0.000147,
          "faktor_daya": 0.95,
          "suhu": 28.5,
          "kelembapan": 65,
          "cahaya": 120
        }
        ```
        
        **Pastikan ESP32 terhubung ke WiFi yang sama dengan komputer ini!**
        """)
    
    # Real-time Data Display
    if st.session_state.data_esp32:
        st.markdown("### 📊 Data Terakhir dari ESP32")
        latest = st.session_state.data_esp32[-1]
        
        # Tampilkan dalam metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Voltage", f"{latest['tegangan']} V")
            st.metric("Current", f"{latest['arus']} A")
        with col2:
            st.metric("Power", f"{latest['daya_aktual']} W")
            st.metric("Energy", f"{latest['energi_kwh']:.6f} kWh")
        with col3:
            if 'suhu' in latest:
                st.metric("Temperature", f"{latest['suhu']} °C")
                st.metric("Humidity", f"{latest.get('kelembapan', 'N/A')} %")
        with col4:
            st.metric("Cost", f"Rp {latest['biaya']:,.0f}")
            if 'cahaya' in latest:
                st.metric("Light", f"{latest['cahaya']} lux")
        
        # Historical Data
        st.markdown("### 📈 Historical Data")
        df_esp32 = pd.DataFrame(st.session_state.data_esp32)
        if 'timestamp' in df_esp32.columns:
            df_esp32['timestamp'] = pd.to_datetime(df_esp32['timestamp'])
            df_display = df_esp32.tail(10)  # Show last 10 records
            st.dataframe(df_display, use_container_width=True)
        
        # Data Management
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear ESP32 Data", type="secondary"):
                st.session_state.data_esp32 = []
                st.session_state.total_energy = 0.0
                simpan_data_esp32()
                st.success("Data ESP32 berhasil dihapus!")
                st.rerun()
        with col2:
            if st.button("💾 Export to CSV"):
                df_esp32.to_csv("esp32_data_export.csv", index=False)
                st.success("Data berhasil diexport ke CSV!")
    
    else:
        st.warning("📭 Belum ada data dari ESP32. Pastikan:")
        st.write("1. Server sudah di-start")
        st.write("2. ESP32 terhubung ke WiFi yang sama")
        st.write("3. ESP32 mengirim data ke endpoint yang benar")

elif menu == "📈 Analytics":
    st.subheader("📈 Energy Analytics")
    
    total_manual = sum(item['energi'] for item in st.session_state.alat_listrik)
    total_esp32 = st.session_state.total_energy
    total_energy = total_manual + total_esp32
    
    if use_tiered:
        total_cost = hitung_biaya_tiered(total_energy)
    else:
        total_cost = total_energy * st.session_state.tarif_listrik
    
    # Summary Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Energy", f"{total_energy:.2f} kWh")
    with col2:
        st.metric("Monthly Cost", f"Rp {total_cost:,.0f}")
    with col3:
        st.metric("Yearly Estimate", f"Rp {total_cost * 12:,.0f}")
    
    # Charts
    if st.session_state.alat_listrik or st.session_state.data_esp32:
        col1, col2 = st.columns(2)
        
        # Pie Chart for Manual Data
        if st.session_state.alat_listrik:
            with col1:
                st.write("**Manual Energy Distribution**")
                labels = [item['nama'] for item in st.session_state.alat_listrik]
                values = [item['energi'] for item in st.session_state.alat_listrik]
                
                fig1, ax1 = plt.subplots()
                ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                ax1.axis('equal')
                st.pyplot(fig1)
        
        # Line Chart for ESP32 Data
        if st.session_state.data_esp32:
            with col2:
                st.write("**ESP32 Energy Trend**")
                df_esp32 = pd.DataFrame(st.session_state.data_esp32)
                if 'timestamp' in df_esp32.columns:
                    df_esp32['timestamp'] = pd.to_datetime(df_esp32['timestamp'])
                    df_esp32 = df_esp32.sort_values('timestamp')
                    
                    fig2, ax2 = plt.subplots()
                    ax2.plot(df_esp32['timestamp'], df_esp32['energi_kwh'].cumsum(), marker='o')
                    ax2.set_ylabel('Cumulative Energy (kWh)')
                    ax2.set_xlabel('Time')
                    plt.xticks(rotation=45)
                    st.pyplot(fig2)
    
    # AI Analysis Section
    st.markdown("---")
    st.subheader("🤖 AI Energy Analysis")
    
    if st.button("🚀 Get Smart Analysis", type="primary"):
        url = "https://givari20.app.n8n.cloud/webhook/ai-listrik"
        
        payload = {
            "total_kwh": total_energy,
            "total_biaya": total_cost,
            "alat_listrik": st.session_state.alat_listrik,
            "data_esp32": st.session_state.data_esp32[-10:] if st.session_state.data_esp32 else [],  # Last 10 records
            "sumber_data": "smart_home_system"
        }
        
        with st.spinner("🔮 Analyzing your energy usage..."):
            try:
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    ai_content = ekstrak_konten_ai(response.text)
                    st.success("✅ Analysis Complete!")
                    
                    st.markdown("### 💡 Smart Recommendations")
                    st.markdown(ai_content)
                    
                else:
                    st.error(f"❌ Analysis failed: {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ Analysis error: {str(e)}")

elif menu == "💾 Data Management":
    st.subheader("💾 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 Manual Data")
        if st.session_state.alat_listrik:
            st.write(f"**Records:** {len(st.session_state.alat_listrik)}")
            st.json(st.session_state.alat_listrik, expanded=False)
            
            if st.button("💾 Save Manual Data"):
                if simpan_ke_file():
                    st.success("Data manual tersimpan!")
            
            if st.button("🗑️ Clear Manual Data"):
                st.session_state.alat_listrik = []
                simpan_ke_file()
                st.success("Data manual dihapus!")
                st.rerun()
        else:
            st.warning("No manual data")
    
    with col2:
        st.markdown("### 📁 ESP32 Data")
        if st.session_state.data_esp32:
            st.write(f"**Records:** {len(st.session_state.data_esp32)}")
            st.write(f"**Total Energy:** {st.session_state.total_energy:.6f} kWh")
            
            if st.button("💾 Save ESP32 Data"):
                if simpan_data_esp32():
                    st.success("Data ESP32 tersimpan!")
            
            if st.button("📥 Load ESP32 Data"):
                if muat_data_esp32():
                    st.success("Data ESP32 dimuat!")
                    st.rerun()
        else:
            st.warning("No ESP32 data")
    
    st.markdown("---")
    st.markdown("### 🔄 System Operations")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reload All Data", use_container_width=True):
            muat_dari_file()
            muat_data_esp32()
            st.success("All data reloaded!")
            st.rerun()
    
    with col2:
        if st.button("🗂️ Export All Data", use_container_width=True):
            # Export manual data
            if st.session_state.alat_listrik:
                pd.DataFrame(st.session_state.alat_listrik).to_csv("manual_data_export.csv", index=False)
            
            # Export ESP32 data
            if st.session_state.data_esp32:
                pd.DataFrame(st.session_state.data_esp32).to_csv("esp32_data_export.csv", index=False)
            
            st.success("All data exported to CSV!")

# Auto-start server
if st.session_state.server_status == "Stopped":
    start_server()

st.markdown("---")
st.caption("🔋 Smart Home Energy Monitoring System | Powered by Streamlit & ESP32")
