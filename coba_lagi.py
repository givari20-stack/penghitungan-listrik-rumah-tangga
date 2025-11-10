# =============================================
# SMART HOME SYSTEM - ESP32 DevKit V1
# Monitoring & Kontrol Energi Listrik
# =============================================

import machine
import time
import dht
import network
import urequests
import json
from machine import Pin, I2C, ADC
import math

# =============================================
# KONFIGURASI PIN & PERANGKAT
# =============================================

# Sensor DHT22 (Suhu & Kelembapan)
dht_sensor = dht.DHT22(Pin(4))

# Sensor LDR (Cahaya) - ADC
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)  # Rentang 0-3.3V

# Relay 4 Channel (Active LOW)
relay_pins = [16, 17, 18, 19]
relays = [Pin(pin, Pin.OUT) for pin in relay_pins]

# Inisialisasi relay OFF (HIGH)
for relay in relays:
    relay.value(1)

# I2C untuk INA219 dan LCD
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=100000)

# =============================================
# KONFIGURASI JARINGAN WiFi
# =============================================

SSID = "Your_WiFi_SSID"
PASSWORD = "Your_WiFi_Password"

# Server Streamlit (ganti dengan IP komputer yang menjalankan Streamlit)
SERVER_URL = "http://192.168.1.100:8000/api/esp32-data"
DEVICE_ID = "ESP32_SmartHome_001"
LOCATION = "Ruang_Tamu"

def connect_wifi():
    """Koneksi ke WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Menghubungkan ke WiFi...')
        wlan.connect(SSID, PASSWORD)
        
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print('.', end='')
    
    if wlan.isconnected():
        print('\nWiFi terhubung!')
        print('IP Address:', wlan.ifconfig()[0])
        return True
    else:
        print('\nGagal terhubung WiFi!')
        return False

# =============================================
# FUNGSI BACA SENSOR INA219 (Simulasi)
# =============================================

class INA219Simulator:
    """Simulator INA219 untuk pengukuran tegangan, arus, dan daya"""
    
    def __init__(self):
        self.base_voltage = 220.0  # Tegangan dasar
        self.base_current = 0.5    # Arus dasar
        self.power_factor = 0.95   # Faktor daya
        
    def read_voltage(self):
        """Baca tegangan dengan variasi kecil"""
        import random
        return self.base_voltage + random.uniform(-5, 5)
    
    def read_current(self):
        """Baca arus berdasarkan kondisi relay"""
        base_load = self.base_current
        # Tambahkan beban berdasarkan relay yang aktif
        if relays[0].value() == 0:  # Lampu 1 ON
            base_load += 0.2
        if relays[1].value() == 0:  # Lampu 2 ON
            base_load += 0.2
        if relays[2].value() == 0:  # Dummy Load ON
            base_load += 0.5
        if relays[3].value() == 0:  # TV ON
            base_load += 0.3
            
        return base_load + random.uniform(-0.1, 0.1)
    
    def read_power(self):
        """Hitung daya aktual"""
        voltage = self.read_voltage()
        current = self.read_current()
        return voltage * current * self.power_factor
    
    def read_energy(self, time_seconds):
        """Hitung energi dalam kWh"""
        power = self.read_power()
        return (power * time_seconds) / 3600000  # Convert to kWh

# Inisialisasi simulator INA219
ina219 = INA219Simulator()

# =============================================
# FUNGSI BACA SENSOR
# =============================================

def read_dht22():
    """Baca suhu dan kelembapan dari DHT22"""
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
        return temp, hum
    except Exception as e:
        print("Error DHT22:", e)
        return None, None

def read_ldr():
    """Baca intensitas cahaya dari LDR"""
    raw_value = ldr.read()
    # Konversi ke lux (approximasi)
    voltage = raw_value * 3.3 / 4095
    if voltage < 0.1:
        return 0
    resistance = 10000 * (3.3 - voltage) / voltage
    lux = 500 / (resistance / 1000)  # Approximasi lux
    return int(lux)

def read_power_data():
    """Baca semua data daya"""
    voltage = ina219.read_voltage()
    current = ina219.read_current()
    power = ina219.read_power()
    energy = ina219.read_energy(2)  # Energi untuk 2 detik
    
    return {
        'tegangan': round(voltage, 2),
        'arus': round(current, 3),
        'daya_aktual': round(power, 1),
        'energi_kwh': round(energy, 6),
        'faktor_daya': 0.95
    }

# =============================================
# FUNGSI KONTROL OTOMATIS
# =============================================

def automatic_control(temp, lux):
    """Kontrol relay otomatis berdasarkan kondisi sensor"""
    
    # Rule 1: Kontrol Lampu 1 berdasarkan cahaya
    if lux < 50:  # Gelap
        relays[0].value(0)  # Lampu 1 ON
        lamp1_status = "ON"
    else:
        relays[0].value(1)  # Lampu 1 OFF
        lamp1_status = "OFF"
    
    # Rule 2: Kontrol Dummy Load (kipas) berdasarkan suhu
    if temp is not None and temp > 30:
        relays[2].value(0)  # Dummy Load ON
        fan_status = "ON"
    else:
        relays[2].value(1)  # Dummy Load OFF
        fan_status = "OFF"
    
    # Rule 3: Kontrol TV simulasi berdasarkan tegangan
    power_data = read_power_data()
    if power_data['tegangan'] < 200:  # Tegangan rendah
        relays[3].value(0)  # TV ON (simulasi alarm)
        tv_status = "ON"
    else:
        relays[3].value(1)  # TV OFF
        tv_status = "OFF"
    
    # Lampu 2 manual control (bisa diatur via web nanti)
    # relays[1].value(1)  # Default OFF
    
    return {
        'lampu1': lamp1_status,
        'lampu2': 'OFF',
        'kipas': fan_status,
        'tv': tv_status
    }

# =============================================
# FUNGSI KIRIM DATA KE SERVER
# =============================================

def send_to_server(sensor_data, power_data, control_status):
    """Kirim data ke server Streamlit"""
    
    # Siapkan payload sesuai format yang diharapkan server
    payload = {
        "device_id": DEVICE_ID,
        "lokasi": LOCATION,
        "tegangan": power_data['tegangan'],
        "arus": power_data['arus'],
        "daya_aktual": power_data['daya_aktual'],
        "energi_kwh": power_data['energi_kwh'],
        "faktor_daya": power_data['faktor_daya'],
        "suhu": sensor_data['suhu'],
        "kelembapan": sensor_data['kelembapan'],
        "cahaya": sensor_data['cahaya'],
        "kontrol_status": control_status
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = urequests.post(SERVER_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("Data terkirim ke server!")
            response.close()
            return True
        else:
            print("Gagal kirim data. Status:", response.status_code)
            response.close()
            return False
            
    except Exception as e:
        print("Error kirim data:", e)
        return False

# =============================================
# FUNGSI TAMPILAN SERIAL
# =============================================

def display_serial_data(sensor_data, power_data, control_status):
    """Tampilkan data di serial monitor"""
    print("\n" + "="*50)
    print("SMART HOME MONITORING SYSTEM")
    print("="*50)
    
    print(f"Suhu: {sensor_data['suhu']}°C | Kelembapan: {sensor_data['kelembapan']}%")
    print(f"Cahaya: {sensor_data['cahaya']} lux")
    print(f"Tegangan: {power_data['tegangan']}V | Arus: {power_data['arus']}A")
    print(f"Daya: {power_data['daya_aktual']}W | Energi: {power_data['energi_kwh']} kWh")
    
    print("\nSTATUS RELAY:")
    for device, status in control_status.items():
        print(f"  {device.upper()}: {status}")
    
    print("="*50)

# =============================================
# PROGRAM UTAMA
# =============================================

def main():
    """Program utama"""
    
    print("Memulai Sistem Smart Home...")
    
    # Coba koneksi WiFi
    if not connect_wifi():
        print("Mode offline - hanya monitoring lokal")
    
    # Variabel akumulasi energi
    total_energy = 0
    
    # Loop utama
    while True:
        try:
            # Baca semua sensor
            temp, hum = read_dht22()
            lux = read_ldr()
            power_data = read_power_data()
            
            # Akumulasi energi
            total_energy += power_data['energi_kwh']
            power_data['energi_kwh'] = total_energy  # Gunakan akumulasi
            
            # Data sensor
            sensor_data = {
                'suhu': temp if temp is not None else 0,
                'kelembapan': hum if hum is not None else 0,
                'cahaya': lux
            }
            
            # Kontrol otomatis
            control_status = automatic_control(temp, lux)
            
            # Tampilkan di serial
            display_serial_data(sensor_data, power_data, control_status)
            
            # Kirim ke server jika WiFi terhubung
            if network.WLAN(network.STA_IF).isconnected():
                send_to_server(sensor_data, power_data, control_status)
            
            # Tunggu 2 detik sebelum loop berikutnya
            time.sleep(2)
            
        except Exception as e:
            print("Error dalam loop utama:", e)
            time.sleep(5)

# =============================================
# JALANKAN PROGRAM
# =============================================

if __name__ == "__main__":
    main()
