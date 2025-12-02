# 🌱 GRASS BOT - Anti-Detection Guide

## 🚀 Instalasi & Menjalankan Bot

### 📦 Requirements

- **Python 3.8+** (Download: https://www.python.org/downloads/)
- **Internet Connection** (untuk terhubung ke Grass Network)
- **User ID** dari akun Grass.io

### 1️⃣ Install Python Packages

Buka terminal/PowerShell di folder bot, lalu jalankan:

```powershell
pip install asyncio aiohttp websockets loguru
```

Atau install semua sekaligus:

```powershell
pip install asyncio aiohttp websockets loguru
```

### 2️⃣ Setup Config File

Buat file `config.json` dengan isi seperti ini:

```json
{
  "accounts": [
    {
      "user_id": "GANTI-DENGAN-USER-ID-KAMU",
      "username": "Akun_1",
      "proxy": null,
      "country": "ID",
      "device_type": "extension"
    }
  ],
  "settings": {
    "ping_interval_min": 18,
    "ping_interval_max": 25,
    "reconnect_delay": 30,
    "max_reconnect_delay": 120,
    "default_country": "ID"
  }
}
```

**Penjelasan Config:**
- `user_id`: User ID dari akun Grass kamu (lihat cara dapat di bawah)
- `username`: Nama identifier untuk log (bebas)
- `proxy`: Proxy address atau `null` (format: `http://user:pass@ip:port`)
- `country`: Kode negara proxy (ID=Indonesia, US=Amerika, dll)
- `device_type`: `"extension"` (2.00x) atau `"mobile"` (3.00x)
- `ping_interval_min`: Ping minimal dalam detik (default: 18)
- `ping_interval_max`: Ping maksimal dalam detik (default: 25)
- `reconnect_delay`: Delay reconnect saat disconnect (detik)

**Ganti `GANTI-DENGAN-USER-ID-KAMU`** dengan User ID kamu (lihat cara dapat User ID di bawah).

### 3️⃣ Menjalankan Bot

#### ✅ Windows:
```powershell
python grass_multi.py
```

#### ✅ Linux/Mac:
```bash
python3 grass_multi.py
```

### 4️⃣ Verifikasi Bot Berjalan

Bot berhasil jika muncul log seperti ini:

```
2025-12-03 10:30:15 | INFO | ✅ Checkin OK
2025-12-03 10:30:16 | INFO | ✅ Connected & Mining!
2025-12-03 10:30:36 | INFO | 📡 Ping #1
2025-12-03 10:30:56 | INFO | 📡 Ping #2
```

### 🔄 Menjalankan Bot 24/7

#### Metode 1: Background Process (Windows)

```powershell
Start-Process python -ArgumentList "grass_multi.py" -WindowStyle Hidden
```

#### Metode 2: Nohup (Linux/Mac)

```bash
nohup python3 grass_multi.py > grass.log 2>&1 &
```

#### Metode 3: Screen (Linux)

```bash
screen -S grass
python3 grass_multi.py
# Tekan Ctrl+A lalu D untuk detach
# screen -r grass untuk attach kembali
```

#### Metode 4: Task Scheduler (Windows)

1. Buka **Task Scheduler**
2. Create Basic Task → Name: "Grass Bot"
3. Trigger: **At startup** atau **Daily**
4. Action: **Start a program**
5. Program: `python.exe`
6. Arguments: `grass_multi.py`
7. Start in: `D:\APLIKASI\Grass` (sesuaikan dengan folder bot)

### ⚙️ Konfigurasi Ping Interval (Anti-Detection)

Bot menggunakan **random ping interval** untuk menghindari deteksi sebagai bot:

#### Default Setting (Recommended):
```json
"settings": {
  "ping_interval_min": 18,  
  "ping_interval_max": 25   
}
```

**Behavior:**
- Ping #1: tunggu 21.3 detik ⏱️
- Ping #2: tunggu 19.7 detik ⏱️
- Ping #3: tunggu 24.1 detik ⏱️
- **Random setiap ping = lebih natural!** ✅

#### Opsi Lainnya:

**Conservative (Paling Aman):**
```json
"ping_interval_min": 20,
"ping_interval_max": 30
```
- Lebih lambat tapi sangat aman
- Cocok untuk long-term farming

**Balanced (Recommended):**
```json
"ping_interval_min": 18,
"ping_interval_max": 25
```
- Sweet spot antara speed & safety
- Default setting

**Aggressive (Medium Risk):**
```json
"ping_interval_min": 15,
"ping_interval_max": 22
```
- Lebih cepat tapi risiko deteksi naik
- Hanya untuk experienced users

**⚠️ JANGAN pakai interval < 15 detik!** Risiko banned sangat tinggi!

### ⚠️ Troubleshooting

| Error | Solusi |
|-------|--------|
| `ModuleNotFoundError` | Install package: `pip install <nama-package>` |
| `SSL Error` | Update Python atau disable SSL di bot |
| `Connection timeout` | Cek internet/VPN, atau gunakan proxy |
| `HTTP 429` | Terlalu banyak request, tunggu beberapa menit |
| `Invalid User ID` | Pastikan User ID sudah benar (lihat cara dapat User ID) |

---

## 📋 Cara Mendapatkan User ID

### Metode 1: Via Browser Console (Recommended) ✅

1. **Login** ke https://app.grass.io/dashboard
2. Buka **Browser DevTools**:
   - Windows/Linux: Tekan `F12` atau `Ctrl + Shift + I`
   - Mac: Tekan `Cmd + Option + I`
3. Klik tab **Console**
4. **Ketik command** berikut dan tekan Enter:
   ```javascript
   localStorage.getItem('userId')
   ```
5. **Copy User ID** yang muncul (tanpa tanda kutip)
   - Contoh hasil: `"939afaf8-xxxx-xxxx-xxxx-xxxxxxxxxxxx"`
   - Yang di-copy: `"939afaf8-xxxx-xxxx-xxxx-xxxxxxxxxxxx"`

### Metode 2: Via Application Storage

1. **Login** ke https://app.grass.io/dashboard
2. Buka **Browser DevTools** (F12)
3. Klik tab **Application** (Chrome/Edge) atau **Storage** (Firefox)
4. Di sidebar kiri, expand **Local Storage**
5. Klik **https://app.grass.io**
6. Cari key `userId` di daftar
7. **Copy value**-nya (kolom Value)

### Metode 3: Via Network Tab

1. **Login** ke https://app.grass.io/dashboard
2. Buka **DevTools** (F12) → tab **Network**
3. Refresh halaman (F5)
4. Cari request ke `director.getgrass.io`
5. Lihat **Request Headers** atau **Payload**
6. User ID ada di dalam request body

### 📸 Screenshot Panduan:

```
┌─────────────────────────────────────────┐
│  🌐 Browser DevTools (F12)              │
├─────────────────────────────────────────┤
│  > Console                              │
│                                         │
│  > localStorage.getItem('userId')      │
│  "939afaf8-fe28-44e6-9cdb-1dc8a6bef..." │
│    ↑ Copy User ID ini                   │
└─────────────────────────────────────────┘
```

### ⚠️ Tips Penting:

- ✅ User ID berbentuk **UUID** (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
- ✅ **Simpan User ID** di tempat aman (jangan sampai hilang)
- ✅ **Jangan share** User ID ke orang lain
- ✅ Untuk **multi-account**, ulangi langkah di atas dengan **login akun berbeda**
- ✅ Setiap akun punya User ID **unik** dan **berbeda**

---

## 🛡️ Cara Menghindari Deteksi Bot

### 1. **Gunakan Proxy Negara yang Sama**

Untuk menghindari deteksi, **SEMUA akun** sebaiknya menggunakan proxy dari **negara yang sama** dengan lokasi asli Anda.

**Contoh untuk Indonesia:**
```json
{
  "accounts": [
    {
      "user_id": "user-id-1",
      "username": "Account_1",
      "proxy": "http://user:pass@id-proxy1.com:8080",
      "country": "ID"
    },
    {
      "user_id": "user-id-2", 
      "username": "Account_2",
      "proxy": "http://user:pass@id-proxy2.com:8080",
      "country": "ID"
    },
    {
      "user_id": "user-id-3",
      "username": "Account_3",
      "proxy": "http://user:pass@id-proxy3.com:8080",
      "country": "ID"
    }
  ],
  "settings": {
    "default_country": "ID"
  }
}
```

### 2. **Tips Anti-Detection:**

✅ **DO (Lakukan):**
- Gunakan **1 IP per akun** (jangan share IP)
- Gunakan **residential proxy** (bukan datacenter)
- Semua proxy dari **negara yang sama** (Indonesia = ID)
- Gunakan **user agent berbeda** per akun (bot sudah otomatis randomize)
- **Jarak waktu** antar akun dibuat (jangan bikin sekaligus)
- **Browser ID berbeda** per akun (bot sudah otomatis)

❌ **DON'T (Jangan):**
- Jangan pakai 1 IP untuk banyak akun
- Jangan mix negara berbeda (misal 1 akun ID, 1 akun US)
- Jangan pakai datacenter proxy (mudah terdeteksi)
- Jangan pakai VPN gratis untuk multi-account
- Jangan login dari lokasi berbeda dengan akun yang sama

### 3. **Provider Proxy dengan Negara Filter:**

#### ABCProxy (Recommended):
```
Format: http://user-country_ID-session_XXX:pass@proxy.abcproxy.com:port
```
- Support negara spesifik
- Residential proxy
- Session rotation

#### NSTProxy:
```
Format: http://user-residential-country_ID-session_XXX:pass@gate.nstproxy.io:port
```
- Support Indonesia
- High quality

#### IPRoyal:
```
Format: http://user:pass@id.iproyal.com:port
```
- Dedicated country endpoint

### 4. **Contoh Konfigurasi Aman (3 Akun):**

```json
{
  "accounts": [
    {
      "user_id": "user-id-1",
      "username": "Main_Account",
      "proxy": "http://user-country_ID-session_abc123:pass@proxy.com:8080",
      "country": "ID"
    },
    {
      "user_id": "user-id-2",
      "username": "Account_2",
      "proxy": "http://user-country_ID-session_def456:pass@proxy.com:8080",
      "country": "ID"
    },
    {
      "user_id": "user-id-3",
      "username": "Account_3",
      "proxy": "http://user-country_ID-session_ghi789:pass@proxy.com:8080",
      "country": "ID"
    }
  ]
}
```

**Key Points:**
- ✅ Semua proxy negara **ID** (Indonesia)
- ✅ **Session berbeda** untuk setiap akun
- ✅ Username unik per akun

### 5. **Negara Code Reference:**

- 🇮🇩 Indonesia: `ID` atau `country_ID`
- 🇺🇸 USA: `US` atau `country_US`
- 🇸🇬 Singapore: `SG` atau `country_SG`
- 🇲🇾 Malaysia: `MY` atau `country_MY`
- 🇹🇭 Thailand: `TH` atau `country_TH`

### 6. **Strategi Multiple Accounts:**

**Pemula (1-3 akun):**
```json
{
  "accounts": [
    {"user_id": "user-1", "username": "Akun_1", "proxy": null, "country": "ID", "device_type": "extension"},
    {"user_id": "user-2", "username": "Akun_2", "proxy": null, "country": "ID", "device_type": "extension"}
  ],
  "settings": {
    "ping_interval_min": 18,
    "ping_interval_max": 25,
    "default_country": "ID"
  }
}
```
- Gunakan VPN berkualitas dari negara yang sama
- Atau 1 residential proxy dengan session rotation

**Advanced (5-10 akun):**
```json
{
  "accounts": [
    {"user_id": "user-1", "proxy": "http://user:pass@proxy1.com:8080", "country": "ID", "device_type": "extension"},
    {"user_id": "user-2", "proxy": "http://user:pass@proxy2.com:8080", "country": "ID", "device_type": "extension"},
    {"user_id": "user-3", "proxy": "http://user:pass@proxy3.com:8080", "country": "ID", "device_type": "extension"}
  ],
  "settings": {
    "ping_interval_min": 18,
    "ping_interval_max": 25
  }
}
```
- 1 residential proxy per akun
- Semua dari negara yang sama
- Buat akun dengan jarak waktu (1-2 hari per akun)

**Pro (10+ akun) - Mix Device Type:**
```json
{
  "accounts": [
    {"user_id": "user-1", "proxy": "residential-1", "country": "ID", "device_type": "extension"},
    {"user_id": "user-2", "proxy": "residential-2", "country": "ID", "device_type": "extension"},
    {"user_id": "user-3", "proxy": "4g-mobile-1", "country": "ID", "device_type": "mobile"}
  ],
  "settings": {
    "ping_interval_min": 20,
    "ping_interval_max": 30
  }
}
```
- Dedicated residential proxy per akun
- Mix provider (jangan semua dari 1 provider)
- Mobile device type hanya dengan mobile proxy!
- Conservative ping interval untuk safety

### 7. **Budget Estimation:**

**Residential Proxy Indonesia:**
- ABCProxy: ~$5-10/GB
- NSTProxy: ~$8-15/GB
- IPRoyal: ~$7/GB

**Estimasi Pemakaian:**
- 1 akun ≈ 2-5 GB/bulan
- 5 akun ≈ 10-25 GB/bulan
- 10 akun ≈ 20-50 GB/bulan

### 8. **Red Flags yang Dihindari:**

🚨 **Tanda-tanda Bot Terdeteksi:**
- Multiple accounts dari IP yang sama
- Login dari negara berbeda-beda
- Pola ping yang terlalu konsisten
- Datacenter IP (bukan residential)
- Browser fingerprint yang sama

### 9. **Best Practices:**

1. **Start Small**: Mulai dengan 1-2 akun dulu
2. **Monitor**: Cek dashboard regular untuk suspicious activity
3. **Rotate**: Ganti session proxy secara berkala
4. **Diversify**: Jangan taruh semua telur di satu keranjang
5. **Stay Natural**: Jangan terlalu greedy dengan banyak akun

### 10. **Contoh Setup dengan ABCProxy:**

```json
{
  "accounts": [
    {
      "user_id": "user-1",
      "username": "Account_1",
      "proxy": "http://customer-user123-country_ID-session-rand1:pass@pr.abcproxy.com:4950",
      "country": "ID"
    },
    {
      "user_id": "user-2",
      "username": "Account_2", 
      "proxy": "http://customer-user123-country_ID-session-rand2:pass@pr.abcproxy.com:4950",
      "country": "ID"
    }
  ],
  "settings": {
    "default_country": "ID",
    "session_rotation": true,
    "rotation_interval": 3600
  }
}
```

## 🔒 Security Tips:

- Jangan share config.json (ada User ID dan proxy credentials)
- Gunakan password yang kuat untuk akun Grass
- Enable 2FA jika tersedia
- Backup User ID di tempat aman

## ⚠️ Disclaimer:

Gunakan bot ini dengan bijak dan sesuai Terms of Service Grass.io. Multi-accounting mungkin melanggar ToS, lakukan dengan risiko sendiri.

**Stay Safe & Happy Farming!** 🌱
