import streamlit as st
import json
import matplotlib.pyplot as plt
import os
import requests
from datetime import datetime

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
    """
    Fungsi untuk menghitung biaya dengan sistem tiered/bertingkat
    """
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

def proses_response_ai(raw_response):
    """
    Fungsi untuk memproses response dari n8n/AI
    """
    # Coba parsing sebagai JSON pertama
    try:
        data = json.loads(raw_response)
        if isinstance(data, dict):
            if 'message' in data and 'content' in data['message']:
                return data['message']['content']
            elif 'analysis' in data:
                return data['analysis']
            elif 'content' in data:
                return data['content']
    except:
        pass
    
    # Jika bukan JSON, proses sebagai text
    content = raw_response
    
    # Ekstrak bagian content dari format yang spesifik
    if "content:" in content:
        parts = content.split("content:")
        if len(parts) > 1:
            content_part = parts[1]
            # Hentikan pada refusal atau annotations
            if "refusal:" in content_part:
                content = content_part.split("refusal:")[0].strip()
            elif "annotations:" in content_part:
                content = content_part.split("annotations:")[0].strip()
            else:
                content = content_part.strip()
    
    # Bersihkan karakter escape dan format
    content = content.replace('\\n', '\n')
    content = content.replace('\\"', '"')
    
    # Hapus karakter kurung siku jika ada
    content = content.replace('[empty array]', '')
    content = content.replace('[empty array]', '')
    
    return content.strip()

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

        # Bagian AI Analysis yang sudah diperbaiki
        st.markdown("---")
        st.subheader("🤖 Analisis AI")
        
        if st.button("Dapatkan Analisis AI", type="primary"):
            url = "https://givari20.app.n8n.cloud/webhook/ai-listrik"
            
            payload = {
                "total_kwh": total_energi,
                "total_biaya": total_biaya,
                "alat_listrik": st.session_state.alat_listrik
            }
            
            with st.spinner("🔄 Sedang menganalisis data dengan AI... Mohon tunggu sebentar"):
                try:
                    response = requests.post(url, json=payload, timeout=60)
                    
                    if response.status_code == 200:
                        raw_response = response.text
                        
                        # Debug mode (bisa disembunyikan dengan comment)
                        with st.expander("🔧 Debug Info (Raw Response)"):
                            st.code(raw_response)
                        
                        # Proses response
                        analysis_content = proses_response_ai(raw_response)
                        
                        # Tampilkan hasil analisis
                        st.success("✅ Analisis AI Berhasil!")
                        
                        # Container untuk hasil analisis
                        with st.container():
                            st.markdown("### 📊 Hasil Analisis AI")
                            st.markdown("---")
                            st.markdown(analysis_content)
                        
                    else:
                        st.error(f"❌ Error dari server: {response.status_code}")
                        st.info("Silakan coba lagi beberapa saat kemudian")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Waktu permintaan habis. Silakan coba lagi.")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Gagal terhubung ke server. Periksa koneksi internet Anda.")
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan: {e}")
                    st.info("Pastikan endpoint n8n aktif dan dapat diakses")

        # Tips penghematan manual
        if total_energi > 200:
            st.markdown("---")
            st.subheader("💡 Tips Penghematan Energi")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **⚡ Penggunaan Alat Elektronik:**
                - Matikan alat elektronik ketika tidak digunakan
                - Cabut charger setelah selesai mengisi daya
                - Gunakan power strip dengan switch
                - Hindari mode standby yang berkepanjangan
                """)
            
            with col2:
                st.markdown("""
                **🏠 Kebiasaan Hemat Energi:**
                - Manfaatkan pencahayaan alami di siang hari
                - Gunakan AC pada suhu 24-25°C
                - Bersihkan filter AC secara berkala
                - Gunakan lampu LED hemat energi
                """)
            
            # Rekomendasi spesifik berdasarkan alat dengan konsumsi tertinggi
            if st.session_state.alat_listrik:
                alat_tertinggi = max(st.session_state.alat_listrik, key=lambda x: x['energi'])
                st.info(f"**Alat dengan konsumsi tertinggi:** {alat_tertinggi['nama']} ({alat_tertinggi['energi']:.2f} kWh/bulan)")
                
                rekomendasi = {
                    "AC": "Gunakan timer dan jaga suhu 24-25°C untuk efisiensi maksimal",
                    "Kulkas": "Pastikan pintu tertutup rapat dan atur suhu optimal",
                    "Water Heater": "Gunakan hanya saat diperlukan dan atur suhu sedang",
                    "Mesin Cuci": "Gunakan dengan kapasitas penuh dan air dingin",
                    "TV": "Matikan sepenuhnya, bukan standby",
                    "Komputer": "Aktifkan mode hemat energi dan matikan saat tidak digunakan"
                }
                
                for kata_kunci, saran in rekomendasi.items():
                    if kata_kunci.lower() in alat_tertinggi['nama'].lower():
                        st.success(f"**Rekomendasi untuk {alat_tertinggi['nama']}:** {saran}")
                        break
    else:
        st.warning("Belum ada data alat listrik. Silakan tambah data terlebih dahulu di menu 'Tambah Data'.")

elif menu == "Grafik":
    st.subheader("Grafik Konsumsi Listrik")
    
    if st.session_state.alat_listrik:
        nama_alat = [item['nama'] for item in st.session_state.alat_listrik]
        energi_alat = [item['energi'] for item in st.session_state.alat_listrik]
        biaya_alat = [item['biaya'] for item in st.session_state.alat_listrik]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Distribusi Konsumsi Energi (kWh)**")
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            colors = plt.cm.Set3(range(len(energi_alat)))
            ax1.pie(energi_alat, labels=nama_alat, autopct='%1.1f%%', startangle=90, colors=colors)
            ax1.axis('equal')  
            st.pyplot(fig1)
        
        with col2:
            st.write("**Biaya Listrik per Alat (Rp)**")
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            bars = ax2.bar(nama_alat, biaya_alat, color='skyblue', alpha=0.7)
            ax2.set_ylabel('Biaya (Rp)')
            ax2.ticklabel_format(style='plain', axis='y')
            plt.xticks(rotation=45, ha='right')
            
            # Tambahkan nilai di atas bar
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'Rp {height:,.0f}', ha='center', va='bottom', fontsize=8)
            
            st.pyplot(fig2)
        
        # Grafik perbandingan energi vs biaya
        st.write("**Perbandingan Konsumsi vs Biaya**")
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        
        x = range(len(nama_alat))
        width = 0.35
        
        bars1 = ax3.bar([i - width/2 for i in x], energi_alat, width, label='Energi (kWh)', color='lightgreen')
        bars2 = ax3.bar([i + width/2 for i in x], [b/1000 for b in biaya_alat], width, label='Biaya (Rp/1000)', color='salmon')
        
        ax3.set_xlabel('Alat Listrik')
        ax3.set_ylabel('Nilai')
        ax3.set_title('Perbandingan Konsumsi Energi dan Biaya')
        ax3.set_xticks(x)
        ax3.set_xticklabels(nama_alat, rotation=45, ha='right')
        ax3.legend()
        
        st.pyplot(fig3)
        
    else:
        st.warning("Belum ada data alat listrik. Silakan tambah data terlebih dahulu di menu 'Tambah Data'.")

elif menu == "Simpan Data":
    st.subheader("Simpan dan Muat Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Simpan Data ke File**")
        if st.session_state.alat_listrik:
            st.info(f"Jumlah alat yang akan disimpan: {len(st.session_state.alat_listrik)}")
            
            if st.button("💾 Simpan Data ke JSON", type="primary"):
                with st.spinner("Menyimpan data..."):
                    if simpan_ke_file():
                        st.success("Data berhasil disimpan ke file 'data_listrik.json'")
                        
                        file_info = os.stat("data_listrik.json")
                        st.write(f"📁 Ukuran file: {file_info.st_size} bytes")
                        st.write(f"📅 Tanggal modifikasi: {datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        st.error("Gagal menyimpan data")
        else:
            st.warning("Belum ada data untuk disimpan")
    
    with col2:
        st.write("**Muat Data dari File**")
        if st.button("📂 Muat Data dari JSON", type="secondary"):
            with st.spinner("Memuat data..."):
                if muat_dari_file():
                    st.success("Data berhasil dimuat dari file 'data_listrik.json'")
                    st.rerun()
                else:
                    st.error("File tidak ditemukan atau format tidak valid")
    
    # Preview data
    if st.session_state.alat_listrik:
        st.markdown("---")
        st.write("**Preview Data Saat Ini:**")
        st.json(st.session_state.alat_listrik, expanded=False)
        
        # Opsi reset data
        st.markdown("---")
        st.write("**Opsi Data**")
        if st.button("🗑️ Hapus Semua Data", type="secondary"):
            st.session_state.alat_listrik = []
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("""
**ℹ️ Tentang Aplikasi:**
- Hitung konsumsi listrik rumah tangga
- Analisis dengan AI
- Tips penghematan energi
- Simpan/muat data
""")

# Footer
st.markdown("---")
st.caption("© Tugas Project Dasar Pemerograman Givari dan Hanif")
