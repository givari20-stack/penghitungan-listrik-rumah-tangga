import streamlit as st
import json
import matplotlib.pyplot as plt
import os
import requests
from datetime import datetime
import re

st.set_page_config(page_title="Penghitung Konsumsi Listrik", page_icon="⚡", layout="wide")
st.title("⚡ Penghitung Konsumsi Listrik Rumah Tangga")

if 'alat_listrik' not in st.session_state:
    st.session_state.alat_listrik = []

if 'tarif_listrik' not in st.session_state:
    st.session_state.tarif_listrik = 1500

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

def ekstrak_konten_ai(response_text):
    """
    Fungsi untuk mengekstrak konten dari response n8n AI
    """
    try:
        # Coba parsing sebagai JSON
        data = json.loads(response_text)
        
        # Format 1: Array dengan message content
        if isinstance(data, list) and len(data) > 0:
            if 'message' in data[0] and 'content' in data[0]['message']:
                content = data[0]['message']['content']
                content = content.replace('\\n', '\n')
                return content
                
        # Format 2: Object langsung dengan content
        if 'content' in data:
            content = data['content']
            content = content.replace('\\n', '\n')
            return content
            
    except json.JSONDecodeError:
        # Jika bukan JSON, ekstrak dari text langsung
        if 'content:' in response_text:
            # Split by content: and take the part after it
            parts = response_text.split('content:', 1)
            if len(parts) > 1:
                content = parts[1]
                # Remove refusal and annotations parts
                if 'refusal:' in content:
                    content = content.split('refusal:')[0]
                if 'annotations:' in content:
                    content = content.split('annotations:')[0]
                
                content = content.strip()
                content = content.replace('\\n', '\n')
                return content
    
    # Fallback: return original text
    return response_text.replace('\\n', '\n')

menu = st.sidebar.radio("Menu Navigasi", ["Tambah Data", "Lihat Hasil", "Grafik", "Simpan Data"])

st.sidebar.subheader("Pengaturan Tarif Listrik")
tarif_baru = st.sidebar.number_input("Tarif Listrik (Rp/kWh)", min_value=500, max_value=5000,
                                     value=st.session_state.tarif_listrik, step=100)
if tarif_baru != st.session_state.tarif_listrik:
    st.session_state.tarif_listrik = tarif_baru
    st.sidebar.success(f"Tarif listrik diperbarui: Rp {tarif_baru:,.0f}/kWh")

st.sidebar.subheader("Opsi Perhitungan")
use_tiered = st.sidebar.checkbox("Gunakan Tarif Bertingkat (Tiered Pricing)")

if menu == "Tambah Data":
    st.subheader("Tambah Data Alat Listrik")
    
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

elif menu == "Lihat Hasil":
    st.subheader("Hasil Perhitungan Konsumsi Listrik")
    
    if not st.session_state.alat_listrik:
        if muat_dari_file():
            st.success("Data berhasil dimuat dari file!")
    
    if st.session_state.alat_listrik:
        total_energi = sum(item['energi'] for item in st.session_state.alat_listrik)
        
        if use_tiered:
            total_biaya = hitung_biaya_tiered(total_energi)
            st.info("Menggunakan sistem tarif bertingkat")
        else:
            total_biaya = sum(item['biaya'] for item in st.session_state.alat_listrik)
        
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
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Konsumsi Energi", f"{total_energi:.2f} kWh")
        with col2:
            st.metric("Total Biaya Listrik", f"Rp {total_biaya:,.0f}")
        
        st.info(f"Estimasi biaya tahunan: Rp {total_biaya * 12:,.0f}")

        # BAGIAN AI ANALYSIS - YANG SUDAH BERHASIL
        st.markdown("---")
        st.subheader("🤖 Analisis AI")
        
        if st.button("Dapatkan Analisis AI", type="primary"):
            url = "https://givari20.app.n8n.cloud/webhook/ai-listrik"
            
            payload = {
                "total_kwh": total_energi,
                "total_biaya": total_biaya,
                "alat_listrik": st.session_state.alat_listrik
            }
            
            with st.spinner("🔄 Sedang menganalisis data dengan AI... Mohon tunggu 10-20 detik"):
                try:
                    response = requests.post(url, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        st.success("✅ Analisis AI Berhasil!")
                        
                        # Ekstrak konten dari response
                        ai_content = ekstrak_konten_ai(response.text)
                        
                        # Tampilkan hasil analisis
                        st.markdown("---")
                        st.subheader("📊 Hasil Analisis AI")
                        
                        # Tampilkan dalam box yang rapi
                        st.markdown(f"""
                        <div style="
                            background-color: #f8f9fa;
                            padding: 20px;
                            border-radius: 10px;
                            border-left: 5px solid #4CAF50;
                            margin: 10px 0;
                            white-space: pre-wrap;
                            font-family: Arial, sans-serif;
                        ">
                        {ai_content}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Debug info (bisa disembunyikan)
                        with st.expander("🔧 Raw Response (Debug)"):
                            st.code(response.text)
                        
                    else:
                        st.error(f"❌ Error dari server: {response.status_code}")
                        st.text(f"Response: {response.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Waktu permintaan habis. Silakan coba lagi.")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Gagal terhubung ke server. Periksa koneksi internet.")
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan: {str(e)}")

    else:
        st.warning("Belum ada data alat listrik. Silakan tambah data terlebih dahulu.")

elif menu == "Grafik":
    st.subheader("Grafik Konsumsi Listrik")
    
    if st.session_state.alat_listrik:
        nama_alat = [item['nama'] for item in st.session_state.alat_listrik]
        energi_alat = [item['energi'] for item in st.session_state.alat_listrik]
        biaya_alat = [item['biaya'] for item in st.session_state.alat_listrik]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Distribusi Konsumsi Energi (kWh)**")
            fig1, ax1 = plt.subplots()
            ax1.pie(energi_alat, labels=nama_alat, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')  
            st.pyplot(fig1)
        
        with col2:
            st.write("**Biaya Listrik per Alat (Rp)**")
            fig2, ax2 = plt.subplots()
            ax2.bar(nama_alat, biaya_alat, color='orange')
            ax2.set_ylabel('Biaya (Rp)')
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig2)
    else:
        st.warning("Belum ada data alat listrik. Silakan tambah data terlebih dahulu.")

elif menu == "Simpan Data":
    st.subheader("Simpan Data ke File")
    
    if st.session_state.alat_listrik:
        st.write("Data yang akan disimpan:")
        st.json(st.session_state.alat_listrik, expanded=False)
        
        if st.button("Simpan Data ke File JSON"):
            with st.spinner("💾 Menyimpan data..."):
                if simpan_ke_file():
                    st.success("Data berhasil disimpan ke file 'data_listrik.json'")
                    
                    file_info = os.stat("data_listrik.json")
                    st.write(f"Ukuran file: {file_info.st_size} bytes")
                    st.write(f"Tanggal modifikasi: {datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    else:
        st.warning("Belum ada data alat listrik. Silakan tambah data terlebih dahulu.")
    
    st.subheader("Muat Data dari File")
    if st.button("Muat Data dari File JSON"):
        with st.spinner("📂 Memuat data..."):
            if muat_dari_file():
                st.success("Data berhasil dimuat dari file 'data_listrik.json'")
                st.rerun()
            else:
                st.error("File 'data_listrik.json' tidak ditemukan atau format tidak valid.")

st.sidebar.markdown("---")
st.sidebar.info("Aplikasi Penghitung Konsumsi Listrik Rumah Tangga")
