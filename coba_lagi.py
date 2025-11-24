import streamlit as st
import requests
import time

# ===============================
# Konfigurasi IP ESP32
# ===============================
ESP_IP = "10.203.15.109"

# ===============================
# Fungsi GET DATA
# ===============================
def get_data():
    try:
        r = requests.get(f"http://{ESP_IP}/data", timeout=3)
        return r.json()
    except:
        return None

# ===============================
# Fungsi KONTROL RELAY
# ===============================
def set_relay(r1=None, r2=None):
    cmd = []
    if r1 is not None:
        cmd.append(f"r1={r1}")
    if r2 is not None:
        cmd.append(f"r2={r2}")

    url = f"http://{ESP_IP}/relay?{'&'.join(cmd)}"
    try:
        r = requests.get(url, timeout=3)
        return r.text
    except:
        return "Gagal mengirim perintah"


# ===============================
# Tampilan UI
# ===============================

st.set_page_config(page_title="SmartHome ESP32", layout="wide")

st.title("🏠 Smart Home Dashboard (ESP32)")
st.markdown("Status sensor & kontrol perangkat secara real-time.")


# Tombol refresh manual
if st.button("🔄 Refresh Data"):
    st.rerun()

# Ambil data dari ESP
data = get_data()

if data is None:
    st.error("❌ Tidak dapat terhubung ke ESP32. Pastikan ESP dan laptop satu jaringan WiFi.")
else:
    st.success("🟢 Terhubung ke ESP32!")

    # ===============================
    # Tampilan Data Sensor
    # ===============================
    col1, col2, col3 = st.columns(3)

    # LDR
    with col1:
        st.markdown("### 💡 Cahaya (LDR)")
        st.metric(label="Nilai LDR", value=data["ldr"])
        st.write("Status:", f"**{data['statusLDR']}**")

    # Suhu
    with col2:
        st.markdown("### 🌡 Suhu (DHT11)")
        st.metric(label="Suhu", value=f"{data['suhu']} °C")
        st.write("Status:", f"**{data['statusSuhu']}**")

    # Relay status
    with col3:
        st.markdown("### ⚡ Status Relay")
        st.metric(label="Relay Lampu (R1)", value="ON" if data["relay1"] == 1 else "OFF")
        st.metric(label="Relay Kipas (R2)", value="ON" if data["relay2"] == 1 else "OFF")

    st.markdown("---")

    # ===============================
    # Kontrol Relay
    # ===============================
    st.header("🔌 Kontrol Relay")

    colR1, colR2 = st.columns(2)

    with colR1:
        st.subheader("Lampu (Relay 1)")
        if st.button("Lampu ON"):
            st.write(set_relay(r1=1))
        if st.button("Lampu OFF"):
            st.write(set_relay(r1=0))

    with colR2:
        st.subheader("Kipas (Relay 2)")
        if st.button("Kipas ON"):
            st.write(set_relay(r2=1))
        if st.button("Kipas OFF"):
            st.write(set_relay(r2=0))

    st.markdown("---")

    # ===============================
    # Auto Refresh (opsional)
    # ===============================
    auto = st.checkbox("Auto-refresh setiap 2 detik")

    if auto:
        time.sleep(2)
        st.rerun()
