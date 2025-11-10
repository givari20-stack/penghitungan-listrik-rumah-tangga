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

st.set_page_config(page_title="Penghitung Konsumsi Listrik", page_icon="⚡", layout="wide")
st.title("⚡ Penghitung Konsumsi Listrik Rumah Tangga")

if 'alat_listrik' not in st.session_state:
    st.session_state.alat_listrik = []

if 'tarif_listrik' not in st.session_state:
    st.session_state.tarif_listrik = 1500

if 'data_esp32' not in st.session_state:
    st.session_state.data_esp32 = []

if 'server_status' not in st.session_state:
    st.session_state.server_status = "Stopped"

# Global variable untuk server
httpd = None
server_thread = None

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
    """Fungsi untuk mengekstrak konten dari response AI"""
    try:
        # Parse JSON response
        data = json.loads(response_text)
        
        # Cek jika response adalah list dan memiliki item pertama
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            
            # Cek jika ada message dan content
            if 'message' in first_item and 'content' in first_item['message']:
                content = first_item['message']['content']
                # Ganti \n dengan newline sebenarnya
                content = content.replace('\\n', '\n')
                return content
        
        # Fallback: return original text
        return response_text.replace('\\n', '\n')
        
    except json.JSONDecodeError:
        # Jika bukan JSON, return as-is
        return response_text.replace('\\n', '\n')

# HTTP Server untuk ESP32
class ESP32Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"ESP32 Data Receiver is Running!")
        
        elif self.path == "/status":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                "status": "running",
                "total_records": len(st.session_state.data_esp32),
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(status).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Endpoint not found")

    def do_POST(self):
        if self.path == "/api/esp32-data":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse JSON data
                data = json.loads(post_data.decode('utf-8'))
                
                # Validasi data yang diperlukan
                required_fields = ['device_id', 'tegangan', 'arus', 'daya_aktual', 'energi_kwh']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Field {field} tidak ditemukan")
                
                # Tambahkan timestamp
                data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Hitung biaya jika belum ada
                if 'biaya' not in data:
                    data['biaya'] = data['energi_kwh'] * st.session_state.tarif_listrik
                
                # Simpan ke session state
                st.session_state.data_esp32.append(data)
                simpan_data_esp32()
                
                # Response sukses
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "status": "success",
                    "message": "Data berhasil diterima",
                    "record_count": len(st.session_state.data_esp32)
                }
                self.wfile.write(json.dumps(response).encode())
                
                print(f"Data ESP32 diterima: {data['device_id']} - {data['energi_kwh']} kWh")
                
            except json.JSONDecodeError as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"status": "error", "message": "Format JSON tidak valid"}
                self.wfile.write(json.dumps(error_response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(error_response).encode())
                
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Endpoint not found")

    def log_message(self, format, *args):
        # Suppress default logging
        return

def run_server():
    global httpd
    try:
        httpd = HTTPServer(('0.0.0.0', 8000), ESP32Handler)
        st.session_state.server_status = "Running"
        print("Server ESP32 berjalan di port 8000")
        httpd.serve_forever()
    except Exception as e:
        st.session_state.server_status = f"Error: {str(e)}"
        print(f"Server error: {e}")

def start_server():
    global server_thread
    if server_thread is None or not server_thread.is_alive():
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        st.session_state.server_status = "Starting..."
        # Tunggu sebentar untuk konfirmasi server running
        time.sleep(1)

def stop_server():
    global httpd
    if httpd:
        httpd.shutdown()
        httpd.server_close()
        st.session_state.server_status = "Stopped"
        print("Server ESP32 dihentikan")

# Menu navigasi
menu = st.sidebar.radio("Menu Navigasi", ["Tambah Data", "Input ESP32", "Lihat Hasil", "Grafik", "Simpan Data"])

st.sidebar.subheader("Pengaturan Tarif Listrik")
tarif_baru = st.sidebar.number_input("Tarif Listrik (Rp/kWh)", min_value=500, max_value=5000,
                                     value=st.session_state.tarif_listrik, step=100)
if tarif_baru != st.session_state.tarif_listrik:
    st.session_state.tarif_listrik = tarif_baru
    st.sidebar.success(f"Tarif listrik diperbarui: Rp {tarif_baru:,.0f}/kWh")

st.sidebar.subheader("Opsi Perhitungan")
use_tiered = st.sidebar.checkbox("Gunakan Tarif Bertingkat (Tiered Pricing)")

# Sidebar untuk server control
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 ESP32 Server")

if st.sidebar.button("🚀 Start Server"):
    start_server()

if st.sidebar.button("🛑 Stop Server"):
    stop_server()

st.sidebar.write(f"**Status:** {st.session_state.server_status}")
st.sidebar.write(f"**Port:** 8000")
st.sidebar.write(f"**Records:** {len(st.session_state.data_esp32)}")

if menu == "Tambah Data":
    st.subheader("Tambah Data Alat Listrik Manual")
    
    with st.form("tambah_alat_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nama = st.text_input("Nama Alat", placeholder="Contoh: Kulkas, TV, AC")
            daya = st.number_input("Daya (Watt)", min_value=1, max_value=5000, value=100, step=10)
        
        with col2:
            jam_per_hari = st.number_input("Jam Penggunaan per Hari", min_value=0.0, max_value=24.0, value=5.0, step=0.5)
            hari_per_bulan = st.number_input("Hari Penggunaan per Bulan", min_value=1, max_value=31, value=30, step=1)
        
        submitted = st.form_submit_button("Tambah Alat")
        
        if submitted:
            if nama.strip() == "":
                st.error("Nama alat tidak boleh kosong!")
            else:
                energi, biaya = hitung_energi_dan_biaya(daya, jam_per_hari, hari_per_bulan, st.session_state.tarif_listrik)
                
                st.session_state.alat_listrik.append({
                    "nama": nama,
                    "daya": daya,
                    "jam_per_hari": jam_per_hari,
                    "hari_per_bulan": hari_per_bulan,
                    "energi": energi,
                    "biaya": biaya
                })
                
                st.success(f"Alat '{nama}' berhasil ditambahkan!")
                st.info(f"Konsumsi: {energi:.2f} kWh, Biaya: Rp {biaya:,.0f}")

elif menu == "Input ESP32":
    st.subheader("📡 Input Data dari ESP32")
    
    # Load data ESP32 yang tersimpan
    if not st.session_state.data_esp32:
        muat_data_esp32()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Input Data Real-time")
        
        with st.form("input_esp32_form"):
            st.markdown("**Masukkan data dari sensor ESP32:**")
            
            col3, col4, col5 = st.columns(3)
            
            with col3:
                device_id = st.text_input("Device ID", placeholder="ESP32_001", value="ESP32_001")
                tegangan = st.number_input("Tegangan (V)", min_value=0.0, max_value=250.0, value=220.0, step=0.1)
                
            with col4:
                arus = st.number_input("Arus (A)", min_value=0.0, max_value=50.0, value=1.5, step=0.1)
                daya_aktual = st.number_input("Daya (Watt)", min_value=0.0, max_value=5000.0, value=330.0, step=1.0)
                
            with col5:
                energi_kwh = st.number_input("Energi (kWh)", min_value=0.0, max_value=1000.0, value=0.5, step=0.01)
                faktor_daya = st.number_input("Faktor Daya", min_value=0.0, max_value=1.0, value=0.95, step=0.01)
            
            lokasi = st.text_input("Lokasi Sensor", placeholder="Ruang Tamu, Kamar Tidur, dll.")
            
            submitted = st.form_submit_button("📨 Simpan Data Sensor")
            
            if submitted:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                biaya = energi_kwh * st.session_state.tarif_listrik
                
                data_sensor = {
                    "timestamp": timestamp,
                    "device_id": device_id,
                    "lokasi": lokasi,
                    "tegangan": tegangan,
                    "arus": arus,
                    "daya_aktual": daya_aktual,
                    "energi_kwh": energi_kwh,
                    "faktor_daya": faktor_daya,
                    "biaya": biaya
                }
                
                st.session_state.data_esp32.append(data_sensor)
                simpan_data_esp32()
                
                st.success(f"✅ Data sensor dari {device_id} berhasil disimpan!")
                st.json(data_sensor)
    
    with col2:
        st.markdown("### 🔗 API Endpoint")
        st.markdown(f"""
        **Server Status:** `{st.session_state.server_status}`
        
        **Endpoint:** `POST http://[IP-ADDRESS]:8000/api/esp32-data`
        
        **Format JSON:**
        ```json
        {{
          "device_id": "ESP32_001",
          "tegangan": 220.0,
          "arus": 1.5,
          "daya_aktual": 330.0,
          "energi_kwh": 0.5,
          "faktor_daya": 0.95,
          "lokasi": "Ruang Tamu"
        }}
        ```
        
        **Test dengan curl:**
        ```bash
        curl -X POST http://localhost:8000/api/esp32-data \\
          -H "Content-Type: application/json" \\
          -d '{{
            "device_id": "ESP32_TEST",
            "tegangan": 220.0,
            "arus": 1.5,
            "daya_aktual": 330.0,
            "energi_kwh": 0.5,
            "faktor_daya": 0.95,
            "lokasi": "Test"
          }}'
        ```
        """)
        
        if st.button("🔄 Refresh Data"):
            if muat_data_esp32():
                st.success(f"Data ESP32 dimuat: {len(st.session_state.data_esp32)} records")
            else:
                st.warning("Belum ada data ESP32")
        
        if st.session_state.data_esp32:
            st.metric("Total Records", len(st.session_state.data_esp32))
            latest = st.session_state.data_esp32[-1]
            st.metric("Energi Terakhir", f"{latest['energi_kwh']:.3f} kWh")
    
    # Tampilkan data ESP32 yang tersimpan
    if st.session_state.data_esp32:
        st.markdown("### 📋 Data ESP32 Tersimpan")
        
        # Konversi ke DataFrame untuk tampilan yang lebih baik
        df_esp32 = pd.DataFrame(st.session_state.data_esp32)
        
        # Format kolom untuk tampilan
        display_df = df_esp32.copy()
        display_df['biaya'] = display_df['biaya'].apply(lambda x: f"Rp {x:,.0f}")
        display_df['energi_kwh'] = display_df['energi_kwh'].apply(lambda x: f"{x:.3f} kWh")
        display_df['daya_aktual'] = display_df['daya_aktual'].apply(lambda x: f"{x:.1f} W")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Opsi hapus data
        if st.button("🗑️ Hapus Semua Data ESP32"):
            st.session_state.data_esp32 = []
            simpan_data_esp32()
            st.success("Semua data ESP32 telah dihapus!")
            st.rerun()

elif menu == "Lihat Hasil":
    st.subheader("Hasil Perhitungan Konsumsi Listrik")
    
    # Load data yang tersimpan
    if not st.session_state.alat_listrik:
        muat_dari_file()
    if not st.session_state.data_esp32:
        muat_data_esp32()
    
    total_energi_manual = sum(item['energi'] for item in st.session_state.alat_listrik) if st.session_state.alat_listrik else 0
    total_energi_esp32 = sum(item['energi_kwh'] for item in st.session_state.data_esp32) if st.session_state.data_esp32 else 0
    
    # Tampilkan data manual
    if st.session_state.alat_listrik:
        st.markdown("### 📝 Data Manual")
        
        if use_tiered:
            total_biaya_manual = hitung_biaya_tiered(total_energi_manual)
        else:
            total_biaya_manual = sum(item['biaya'] for item in st.session_state.alat_listrik)
        
        data_tabel = []
        for item in st.session_state.alat_listrik:
            data_tabel.append({
                "Nama Alat": item['nama'],
                "Daya (Watt)": item['daya'],
                "Jam/Hari": item['jam_per_hari'],
                "Hari/Bulan": item['hari_per_bulan'],
                "Energi (kWh)": f"{item['energi']:.2f}",
                "Biaya (Rp)": f"{item['biaya']:,.0f}"
            })
        
        st.table(data_tabel)
    
    # Tampilkan data ESP32
    if st.session_state.data_esp32:
        st.markdown("### 📡 Data ESP32")
        
        total_biaya_esp32 = sum(item['biaya'] for item in st.session_state.data_esp32)
        
        df_esp32 = pd.DataFrame(st.session_state.data_esp32)
        st.dataframe(df_esp32, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Energi ESP32", f"{total_energi_esp32:.3f} kWh")
        with col2:
            st.metric("Total Biaya ESP32", f"Rp {total_biaya_esp32:,.0f}")
    
    # Hitung total keseluruhan
    total_energi = total_energi_manual + total_energi_esp32
    total_biaya = (total_biaya_manual if st.session_state.alat_listrik else 0) + total_biaya_esp32
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Konsumsi Energi", f"{total_energi:.2f} kWh")
    with col2:
        st.metric("Total Biaya Listrik", f"Rp {total_biaya:,.0f}")
    
    st.info(f"Estimasi biaya tahunan: Rp {total_biaya * 12:,.0f}")

    # BAGIAN AI ANALYSIS
    st.markdown("---")
    st.subheader("🤖 Analisis AI")
    
    if st.button("Dapatkan Analisis AI", type="primary"):
        url = "https://givari20.app.n8n.cloud/webhook/ai-listrik"
        
        # Gabungkan data manual dan ESP32 untuk analisis
        payload = {
            "total_kwh": total_energi,
            "total_biaya": total_biaya,
            "alat_listrik": st.session_state.alat_listrik,
            "data_esp32": st.session_state.data_esp32,
            "sumber_data": "manual_dan_esp32"
        }
        
        with st.spinner("🔄 Sedang menganalisis data dengan AI... Mohon tunggu 10-20 detik"):
            try:
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    # Ekstrak konten dari response
                    ai_content = ekstrak_konten_ai(response.text)
                    
                    st.success("✅ Analisis AI Berhasil!")
                    
                    # Tampilkan hasil analisis
                    st.markdown("---")
                    st.subheader("📊 Hasil Analisis AI")
                    
                    # Tampilkan konten dengan format yang rapi
                    st.markdown(ai_content)
                    
                else:
                    st.error(f"❌ Error dari server: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error("⏰ Waktu permintaan habis. Silakan coba lagi.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Gagal terhubung ke server. Periksa koneksi internet.")
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {str(e)}")

elif menu == "Grafik":
    st.subheader("Grafik Konsumsi Listrik")
    
    # Load data
    if not st.session_state.alat_listrik:
        muat_dari_file()
    if not st.session_state.data_esp32:
        muat_data_esp32()
    
    if st.session_state.alat_listrik or st.session_state.data_esp32:
        col1, col2 = st.columns(2)
        
        # Grafik data manual
        if st.session_state.alat_listrik:
            with col1:
                st.write("**Distribusi Konsumsi Energi Manual (kWh)**")
                nama_alat = [item['nama'] for item in st.session_state.alat_listrik]
                energi_alat = [item['energi'] for item in st.session_state.alat_listrik]
                
                fig1, ax1 = plt.subplots()
                ax1.pie(energi_alat, labels=nama_alat, autopct='%1.1f%%', startangle=90)
                ax1.axis('equal')  
                st.pyplot(fig1)
        
        # Grafik data ESP32
        if st.session_state.data_esp32:
            with col2:
                st.write("**Data Real-time ESP32**")
                df_esp32 = pd.DataFrame(st.session_state.data_esp32)
                
                if 'timestamp' in df_esp32.columns:
                    df_esp32['timestamp'] = pd.to_datetime(df_esp32['timestamp'])
                    df_esp32 = df_esp32.sort_values('timestamp')
                    
                    fig2, ax2 = plt.subplots()
                    ax2.plot(df_esp32['timestamp'], df_esp32['energi_kwh'], marker='o')
                    ax2.set_ylabel('Energi (kWh)')
                    ax2.set_xlabel('Waktu')
                    plt.xticks(rotation=45)
                    st.pyplot(fig2)
    else:
        st.warning("Belum ada data alat listrik. Silakan tambah data terlebih dahulu.")

elif menu == "Simpan Data":
    st.subheader("Simpan Data ke File")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 Data Manual")
        if st.session_state.alat_listrik:
            st.write("Data manual yang akan disimpan:")
            st.json(st.session_state.alat_listrik, expanded=False)
            
            if st.button("Simpan Data Manual ke JSON"):
                with st.spinner("💾 Menyimpan data manual..."):
                    if simpan_ke_file():
                        st.success("Data manual berhasil disimpan ke file 'data_listrik.json'")
        else:
            st.warning("Belum ada data manual")
    
    with col2:
        st.markdown("### 💾 Data ESP32")
        if st.session_state.data_esp32:
            st.write(f"Data ESP32: {len(st.session_state.data_esp32)} records")
            
            if st.button("Simpan Data ESP32 ke JSON"):
                with st.spinner("💾 Menyimpan data ESP32..."):
                    if simpan_data_esp32():
                        st.success("Data ESP32 berhasil disimpan ke file 'data_esp32.json'")
        else:
            st.warning("Belum ada data ESP32")
    
    st.markdown("---")
    st.subheader("📂 Muat Data dari File")
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("Muat Data Manual"):
            with st.spinner("📂 Memuat data manual..."):
                if muat_dari_file():
                    st.success("Data manual berhasil dimuat")
                    st.rerun()
                else:
                    st.error("File 'data_listrik.json' tidak ditemukan")
    
    with col4:
        if st.button("Muat Data ESP32"):
            with st.spinner("📂 Memuat data ESP32..."):
                if muat_data_esp32():
                    st.success("Data ESP32 berhasil dimuat")
                    st.rerun()
                else:
                    st.error("File 'data_esp32.json' tidak ditemukan")

st.sidebar.markdown("---")
st.sidebar.info("Aplikasi Penghitung Konsumsi Listrik Rumah Tangga")

# Auto-start server ketika aplikasi dimulai
if st.session_state.server_status == "Stopped":
    start_server()
