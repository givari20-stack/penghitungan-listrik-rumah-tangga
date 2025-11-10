import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime
import requests

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
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .sensor-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .energy-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .cost-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .section-title {
        font-size: 1.5rem;
        color: #1f77b4;
        margin: 2rem 0 1rem 0;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
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

# ==================== FUNGSI UTAMA ====================
def calculate_energy_cost(power_w, hours_per_day, days_per_month, rate_per_kwh):
    energy_kwh = (power_w * hours_per_day * days_per_month) / 1000
    cost = energy_kwh * rate_per_kwh
    return energy_kwh, cost

def load_sample_data():
    """Data sample untuk demo"""
    sample_devices = [
        {"name": "AC", "power": 800, "hours": 6, "days": 30, "energy": 144, "cost": 216000},
        {"name": "Kulkas", "power": 150, "hours": 24, "days": 30, "energy": 108, "cost": 162000},
        {"name": "LED TV", "power": 100, "hours": 5, "days": 30, "energy": 15, "cost": 22500},
        {"name": "Lampu", "power": 60, "hours": 8, "days": 30, "energy": 14.4, "cost": 21600}
    ]
    st.session_state.devices = sample_devices
    
    sample_sensor = [
        {"timestamp": "2024-01-15 08:00", "voltage": 220.5, "current": 2.1, "power": 463, "energy": 0.257, "temp": 26.5, "humidity": 65},
        {"timestamp": "2024-01-15 10:00", "voltage": 219.8, "current": 2.3, "power": 506, "energy": 0.512, "temp": 27.2, "humidity": 63},
        {"timestamp": "2024-01-15 12:00", "voltage": 221.2, "current": 2.8, "power": 619, "energy": 0.834, "temp": 28.1, "humidity": 61},
        {"timestamp": "2024-01-15 14:00", "voltage": 220.1, "current": 3.2, "power": 704, "energy": 1.225, "temp": 29.5, "humidity": 59}
    ]
    st.session_state.sensor_data = sample_sensor

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
        step=100
    )
    
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    if st.button("📊 Load Sample Data", use_container_width=True):
        load_sample_data()
        st.success("Data sample loaded!")
        
    if st.button("🔄 Reset Data", use_container_width=True, type="secondary"):
        st.session_state.devices = []
        st.session_state.sensor_data = []
        st.success("Data reset!")
    
    st.markdown("---")
    st.info("""
    **Smart Energy Monitor**
    
    Aplikasi monitoring konsumsi energi rumah tangga dengan analisis real-time.
    
    **Fitur:**
    • Monitoring perangkat
    • Sensor real-time  
    • Analisis biaya
    • Visualisasi data
    """)

# ==================== HEADER ====================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h1 class="main-header">⚡ SMART ENERGY MONITOR</h1>', unsafe_allow_html=True)
    st.markdown("**Sistem Monitoring Konsumsi Energi Rumah Tangga**")

# ==================== DASHBOARD UTAMA ====================
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "📊 Perangkat", "📈 Analytics", "🔧 Tambah Data"])

with tab1:
    # ==================== KPI CARDS ====================
    st.markdown('<div class="section-title">📊 Overview Konsumsi Energi</div>', unsafe_allow_html=True)
    
    total_energy = sum(device["energy"] for device in st.session_state.devices)
    total_cost = sum(device["cost"] for device in st.session_state.devices)
    device_count = len(st.session_state.devices)
    
    if st.session_state.sensor_data:
        current_power = st.session_state.sensor_data[-1]["power"]
        current_temp = st.session_state.sensor_data[-1]["temp"]
    else:
        current_power = 0
        current_temp = 25
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔋 Total Energi</h3>
            <h2>{total_energy:.1f} kWh</h2>
            <p>Bulanan</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="cost-card">
            <h3>💰 Biaya Listrik</h3>
            <h2>Rp {total_cost:,.0f}</h2>
            <p>Per Bulan</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="sensor-card">
            <h3>⚡ Daya Saat Ini</h3>
            <h2>{current_power} W</h2>
            <p>Real-time</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="energy-card">
            <h3>🌡️ Suhu</h3>
            <h2>{current_temp}°C</h2>
            <p>Ruangan</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== GRAFIK ====================
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Distribusi Konsumsi Perangkat")
        if st.session_state.devices:
            fig, ax = plt.subplots(figsize=(8, 6))
            device_names = [device["name"] for device in st.session_state.devices]
            energy_values = [device["energy"] for device in st.session_state.devices]
            
            bars = ax.bar(device_names, energy_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
            ax.set_ylabel('Energi (kWh)')
            ax.set_title('Konsumsi Energi Bulanan')
            
            # Tambah label value di bar
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f} kWh',
                        ha='center', va='bottom')
            
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("📝 Tambahkan perangkat untuk melihat grafik")
    
    with col2:
        st.markdown("#### 📊 Trend Konsumsi Real-time")
        if st.session_state.sensor_data:
            df = pd.DataFrame(st.session_state.sensor_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(df['timestamp'], df['power'], marker='o', linewidth=2, markersize=6, color='#FF6B6B')
            ax.set_ylabel('Daya (Watt)')
            ax.set_xlabel('Waktu')
            ax.set_title('Konsumsi Daya Real-time')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("📡 Data sensor akan muncul di sini")

with tab2:
    st.markdown('<div class="section-title">🔌 Data Perangkat Elektronik</div>', unsafe_allow_html=True)
    
    if st.session_state.devices:
        # Tampilkan data dalam tabel yang rapi
        device_data = []
        for device in st.session_state.devices:
            device_data.append({
                "Perangkat": device["name"],
                "Daya (W)": f"{device['power']} W",
                "Jam/Hari": f"{device['hours']} jam",
                "Hari/Bulan": device["days"],
                "Energi": f"{device['energy']:.1f} kWh",
                "Biaya": f"Rp {device['cost']:,.0f}"
            })
        
        df_devices = pd.DataFrame(device_data)
        st.dataframe(df_devices, use_container_width=True, hide_index=True)
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            max_device = max(st.session_state.devices, key=lambda x: x["energy"])
            st.metric("🏆 Konsumsi Tertinggi", f"{max_device['name']} ({max_device['energy']} kWh)")
        
        with col2:
            total_hours = sum(device["hours"] * device["days"] for device in st.session_state.devices)
            st.metric("⏱️ Total Jam Operasi", f"{total_hours} jam/bulan")
        
        with col3:
            avg_power = sum(device["power"] for device in st.session_state.devices) / len(st.session_state.devices)
            st.metric("⚡ Rata-rata Daya", f"{avg_power:.0f} W")
            
    else:
        st.info("""
        ## 📝 Belum Ada Data Perangkat
        
        **Untuk memulai:**
        1. Buka tab **"🔧 Tambah Data"**
        2. Tambahkan perangkat elektronik
        3. Atau klik **"Load Sample Data"** di sidebar untuk data demo
        """)

with tab3:
    st.markdown('<div class="section-title">📈 Analisis & Insights</div>', unsafe_allow_html=True)
    
    if st.session_state.devices:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💡 Breakdown Biaya")
            cost_data = {
                "Perangkat": [device["name"] for device in st.session_state.devices],
                "Biaya (Rp)": [device["cost"] for device in st.session_state.devices]
            }
            df_cost = pd.DataFrame(cost_data)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(df_cost["Biaya (Rp)"], labels=df_cost["Perangkat"], autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Distribusi Biaya Listrik')
            st.pyplot(fig)
        
        with col2:
            st.markdown("#### 🔄 Efisiensi Energi")
            
            # Hitung efisiensi (asumsi: semakin rendah daya per jam, semakin efisien)
            efficiency_data = []
            for device in st.session_state.devices:
                power_per_hour = device["power"] / device["hours"] if device["hours"] > 0 else device["power"]
                efficiency_data.append({
                    "Perangkat": device["name"],
                    "Konsumsi": f"{power_per_hour:.1f} W/jam"
                })
            
            df_eff = pd.DataFrame(efficiency_data)
            st.dataframe(df_eff, use_container_width=True, hide_index=True)
            
            st.info("""
            **💡 Tips Efisiensi:**
            - Matikan perangkat saat tidak digunakan
            - Gunakan perangkat hemat energi
            - Optimalkan waktu penggunaan
            """)
        
        # Annual Projection
        st.markdown("#### 📅 Proyeksi Tahunan")
        annual_energy = total_energy * 12
        annual_cost = total_cost * 12
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Energi Tahunan", f"{annual_energy:.0f} kWh")
        with col2:
            st.metric("Biaya Tahunan", f"Rp {annual_cost:,.0f}")
        with col3:
            savings = annual_cost * 0.15  # Asumsi 15% penghematan
            st.metric("Potensi Penghematan", f"Rp {savings:,.0f}")
            
    else:
        st.info("📊 Data analisis akan muncul setelah menambahkan perangkat")

with tab4:
    st.markdown('<div class="section-title">🔧 Kelola Data Perangkat</div>', unsafe_allow_html=True)
    
    with st.form("tambah_perangkat_form"):
        st.markdown("### ➕ Tambah Perangkat Baru")
        
        col1, col2 = st.columns(2)
        
        with col1:
            device_name = st.text_input("Nama Perangkat", placeholder="AC, Kulkas, TV, dll.")
            power_watt = st.number_input("Daya (Watt)", min_value=1, max_value=5000, value=100)
            
        with col2:
            hours_per_day = st.number_input("Jam Penggunaan per Hari", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
            days_per_month = st.number_input("Hari Penggunaan per Bulan", min_value=1, max_value=31, value=30)
        
        submitted = st.form_submit_button("💾 Simpan Perangkat", use_container_width=True)
        
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
                    "power": power_watt,
                    "hours": hours_per_day,
                    "days": days_per_month,
                    "energy": energy,
                    "cost": cost
                }
                
                st.session_state.devices.append(new_device)
                
                st.success(f"✅ **{device_name}** berhasil ditambahkan!")
                st.info(f"""
                **Detail Konsumsi:**
                - Energi: {energy:.1f} kWh/bulan
                - Biaya: Rp {cost:,.0f}/bulan
                """)
            else:
                st.error("❌ Nama perangkat tidak boleh kosong!")
    
    # Data Management
    if st.session_state.devices:
        st.markdown("---")
        st.markdown("### 📋 Kelola Data Existing")
        
        # Tampilkan perangkat yang ada dengan opsi hapus
        for i, device in enumerate(st.session_state.devices):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{device['name']}** - {device['power']}W")
            with col2:
                st.write(f"{device['energy']:.1f} kWh/bulan")
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.devices.pop(i)
                    st.success("Perangkat dihapus!")
                    st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>⚡ Smart Energy Monitor</strong> - Sistem Monitoring Konsumsi Energi Rumah Tangga</p>
        <p>Dibuat untuk Presentasi Akademik • © 2024</p>
    </div>
    """, unsafe_allow_html=True)

# ==================== AUTO-LOAD SAMPLE DATA ====================
if not st.session_state.devices and not st.session_state.sensor_data:
    load_sample_data()
