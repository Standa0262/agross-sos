# 🌐 DEPLOYMENT – VIETNAMSKÉ PARTNEŘSKÉ SÍTĚ

**Cíl:** Jak nasadit aplikaci pro Provector, MO Partner a další síťe  
**Formát:** Vietnamské instrukce + Technical Guide  
**Datum:** 2026-06-18

---

## 🚀 NASAZENÍ APLIKACE

### Možnost 1: PWA (Progressive Web App) – DOPORUČENO ✅

**Co to je?**
- Webová aplikace fungující na mobilu JAKO nativní aplikace
- Bez nutnosti stahovat z App Store/Google Play
- Funguje offline (bez internetu)
- Automaticky se aktualizuje

**Instalace pro vietnamské prodejny:**

#### Krok 1: Příprava serveru

```bash
# 1. Nasadit HTML na web server
# Struktura:
https://a-gross.vn/app/
├─ A_GROSS_SOS_VI.html
├─ sw.js (Service Worker)
├─ manifest.json (webové metadata)
└─ cenik.json (katalog)

# 2. Web server (Nginx/Apache)
# Obsluha HTTPS + CORS
```

**Nginx konfigurace:**
```nginx
server {
    listen 443 ssl;
    server_name a-gross.vn;
    
    ssl_certificate /etc/ssl/a-gross.vn.crt;
    ssl_certificate_key /etc/ssl/a-gross.vn.key;
    
    root /var/www/a-gross-sos/;
    index A_GROSS_SOS_VI.html;
    
    location / {
        try_files $uri $uri/ /A_GROSS_SOS_VI.html;
        add_header Cache-Control "public, max-age=3600";
    }
    
    # Service Worker – bez cachování!
    location /sw.js {
        add_header Cache-Control "public, max-age=0";
        add_header Service-Worker-Allowed "/";
    }
    
    # Katalog – update každou hodinu
    location /cenik.json {
        add_header Cache-Control "public, max-age=3600";
    }
}
```

#### Krok 2: Vytvoření `manifest.json`

```json
{
  "name": "A-GROSS SOS – Ứng dụng đặt hàng",
  "short_name": "A-GROSS SOS",
  "description": "Ứng dụng đặt hàng galanterie và phụ kiện may mặc – Offline + Real-time",
  "start_url": "/A_GROSS_SOS_VI.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1A1A1A",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Přidat do HTML headeru:**
```html
<link rel="manifest" href="/manifest.json">
<link rel="icon" type="image/png" href="/icon-192.png">
<meta name="theme-color" content="#1A1A1A">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

#### Krok 3: Vietnamským partnerům

**Email šablona (Vietnamština):**

```
Tựa: A-GROSS SOS – Ứng dụng đặt hàng (Cài đặt trên điện thoại)

---

Xin chào Quý vị,

A-GROSS SOS là ứng dụng đặt hàng thông qua internet. Bây giờ quý vị có thể
dùng ngay trên điện thoại!

📱 CÀI ĐẶT:

1. **Trên iPhone:**
   • Mở Safari → Nhập: a-gross.vn/app
   • Nhấn nút "Chia sẻ" (Share)
   • Chọn "Thêm vào Màn hình chính" (Add to Home Screen)
   • Đặt tên: "A-GROSS SOS"
   • Nhấn "Thêm" (Add)
   → Ứng dụng hiện thị như biểu tượng trên Home Screen

2. **Trên Android:**
   • Mở Chrome → Nhập: a-gross.vn/app
   • Nhấn 3 dấu chấm (⋮) → "Cài đặt ứng dụng" (Install app)
   • Xác nhận
   → Ứng dụng cài đặt như ứng dụng thường

✨ TÍNH NĂNG:
• ✅ Hoạt động MÀ KHÔNG CẦN INTERNET (Offline mode)
• ✅ Nhanh & nhẹ (không chiếm dung lượng như ứng dụng thường)
• ✅ Quét mã vạch (Barcode scanning)
• ✅ Tính toán lợi nhuận tự động
• ✅ Lịch sử đơn hàng

📞 HỖNH TRỢ:
Nếu có vấn đề, vui lòng liên hệ:
• Email: support@a-gross.vn
• WhatsApp: +84 9xx xxxx xxx
• Giờ làm việc: 8:00 – 17:00 (Việt Nam)

Cảm ơn đã sử dụng A-GROSS SOS!

---
A-GROSS, s.r.o. | Olomouc-Holice | www.a-gross.cz
```

---

### Možnost 2: Nativní Aplikace (iOS/Android) – PRO BUDOUCNOST

**Vývoj:** React Native / Flutter (Q3 2026)

```bash
# Budoucí struktura:
App Store:   "A-GROSS SOS"  → iOS 12.0+
Google Play: "A-GROSS SOS"  → Android 7.0+

# Aktuálně: PWA je plně funkční
```

---

## 📡 SYNCHRONIZACE KATALOGU

### Jak funguje?

1. **Vietnamský nákupčí** otevře aplikaci
2. Aplikace **automaticky kontroluje** nový katalog (1× denně)
3. Pokud je nový katalog dostupný, **stáhne si ho**
4. Data se **uloží lokálně** na telefonu
5. Nákupčí **vidí aktualizované ceny** hned

### Nastavení katalogu

**URL katalogu (v Admin nastavení):**
```
https://a-gross.vn/api/catalogs/sync
```

**Struktura JSON:**
```json
[
  {
    "kod": "276921",
    "nazev": "Kim Organ Universal 10 cái",
    "nc": 39.44,
    "moc": 95.90,
    "ean": "8590580899993"
  },
  ...
]
```

**Aktualizace katalogu:**
```bash
# 1. Exportovat z Excelu (cenik_produkty.xlsx)
# 2. Převést na JSON
# 3. Nahrát na server:

scp cenik.json root@a-gross.vn:/var/www/a-gross-sos/cenik.json

# 4. Ověřit dostupnost:
curl https://a-gross.vn/cenik.json
```

---

## 📧 MĚSÍČNÍ EMAILING SÍTÍM

### Automatizace (Cron job)

```bash
#!/bin/bash
# /usr/local/bin/agross-monthly-report.sh

MONTH=$(date +%m)
YEAR=$(date +%Y)
NETWORK="Provector"  # nebo "MO Partner"

# Stáhnout report
curl -s "http://localhost:5000/api/reports/monthly/export?network=$NETWORK&year=$YEAR&month=$MONTH" \
  > /tmp/report_${NETWORK}_${YEAR}_${MONTH}.csv

# Poslat emailem
mail -s "A-GROSS SOS – Měsíční report $NETWORK" \
     -a "From: finance@a-gross.cz" \
     -a "Content-Type: text/csv; charset=UTF-8" \
     finance@$NETWORK.cz < /tmp/report_${NETWORK}_${YEAR}_${MONTH}.csv

# Log
echo "[$(date)] Report sent to $NETWORK" >> /var/log/agross-reports.log
```

**Přidání do Cron (poslední den měsíce):**
```bash
crontab -e

# Přidat:
0 9 28 * * /usr/local/bin/agross-monthly-report.sh

# Spustí se každý 28. den v 9:00 (dost času na data)
```

---

## 🌐 SPRÁVA SÍTÍ

### Registrace nové sítě

**Admin panel TODO:**
```bash
POST /api/networks/register
{
  "name": "Provector",
  "contact_email": "finance@provector.vn",
  "commission_rate": 0.05,
  "region": "Vietnam"
}
→ Vrátí: {"network_id": "NET-123"}
```

**Manuálně v `backend_admin.py`:**
```python
COMMISSION_RATES = {
    'Provector': 0.05,
    'MO Partner': 0.05,
    'CoopMart': 0.04,      # Nová síť
    'Saigon Coop': 0.045,  # Nová síť
}
```

---

## 📊 MONITORING & HEALTH CHECK

### Status Dashboard (TODO – Admin Panel)

```bash
GET /api/health
→ {"status": "ok", "timestamp": "2026-06-18T10:00:00Z"}

GET /api/stats/daily
→ {
  "orders_today": 156,
  "unique_stores": 24,
  "total_purchase": 450000,
  "active_networks": 2
}

GET /api/stats/network?network=Provector
→ {
  "network": "Provector",
  "stores_active": 24,
  "orders_month": 156,
  "commission_pending": 22500
}
```

### Error Monitoring

```python
# backend_admin.py - přidat error logging
import logging

logging.basicConfig(
    filename='/var/log/agross-backend.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.errorhandler(Exception)
def handle_error(error):
    logging.error(f"API Error: {error}")
    return jsonify({'error': str(error)}), 500
```

---

## 🔒 BEZPEČNOSTNÍ KONTROLLIST

- [ ] **HTTPS:** Všechny domény mají SSL certifikát
- [ ] **CORS:** Povoleny jen a-gross.vn domény
- [ ] **Authentication:** API endpoints mají JWT token
- [ ] **Rate Limiting:** Max 100 req/min per IP
- [ ] **Data Encryption:** PII šifrované v transit
- [ ] **Database Backup:** Daily snapshots S3
- [ ] **Logging:** Všechny API calls zaznamenávány
- [ ] **Monitoring:** AlertSQL pro kritické chyby

---

## 🚨 TROUBLESHOOTING

### "Aplikace se nenačítá"
```
❌ Problem: Offline režim nefunguje
✅ Řešení:
   1. Vymazat cache: Nastavení → Apps → A-GROSS SOS → Clear Cache
   2. Stáhnout znovu: a-gross.vn/app
   3. Zkontrolovat WiFi
```

### "Starý katalog – ceny nejsou aktuální"
```
❌ Problem: Nový katalog se nestáhne
✅ Řešení:
   1. Settings → URL katalogu: https://a-gross.vn/cenik.json
   2. Klikni: ↻ Synchronizuj nyní
   3. Nebo: Vymazat offline data a zkusit znovu
```

### "Objednávka se neposlala"
```
❌ Problem: Offline režim – objednávka zůstala lokálně
✅ Řešení:
   1. Připoj se k WiFi
   2. Klikni: ↻ Synchronizuj nyní
   3. Aplikace automaticky pošle offline objednávky
```

---

## 📞 VIETNAMSKÝ SUPPORT (TODO)

**Najměte vietnamského tech support:**

```
Požadavky:
• Fluent vietnamština + angličtina
• Tech background (ne nutno developer)
• WhatsApp/Telegram dostupnost
• Čas: 8:00–17:00 Vietnamský čas (UTC+7)

Responsibilities:
• Odpovídání na otázky od partnerů
• Remote assistance (TeamViewer)
• Reporting issues do dev týmu
• Training nových obchodů
```

**Kontaktní info pro support:**
```
📞 Hotline: +84 9xx xxxx xxx
📧 Email: support@a-gross.vn
💬 WhatsApp: [QR kód na letáku]
🕐 Odpověď: do 2 hodin
```

---

## 📋 DEPLOYMENT CHECKLIST

- [ ] DNS: `a-gross.vn` → Serverowa IP
- [ ] SSL: Certifikát Let's Encrypt (automatický renew)
- [ ] Nginx: Config + restart
- [ ] Service Worker: `sw.js` dostupný
- [ ] Manifest: `manifest.json` linked
- [ ] Katalog: `cenik.json` nahrán
- [ ] Backend: Python server běží (port 5000)
- [ ] Database: `orders_db.json` vytvořen
- [ ] Monitoring: Logs nastaveny
- [ ] Support: Vietnamský partner přiřazen
- [ ] Email: Šablony pro sítě připraveny
- [ ] Testing: Offline režim ✓, Sync ✓, Reporting ✓

---

## 📈 POST-LAUNCH

### Týden 1
- [ ] Přidat Provector (hlavní síť)
- [ ] Onboarding 5-10 pilotních obchodů
- [ ] Monitoring: 0 errors?
- [ ] Feedback: Jaké problémy?

### Týden 2-4
- [ ] Přidat MO Partner
- [ ] Scale na 50+ obchodů
- [ ] Měsíční report: OK?
- [ ] Training vietnamských partnerů

### Měsíc 2
- [ ] Rozšíření na další sítě
- [ ] Optimizace dle feedback
- [ ] Admin panel (MVP)
- [ ] Statistiky & Analytics

---

**Kontakt:** it@a-gross.cz | +420 585 xxx xxx
