# 🚀 A-GROSS SOS – IMPLEMENTAČNÍ PRŮVODCE

**Status:** ✅ Beta Ready (Vietnamština + Offline Mode + Reporting)  
**Datum:** 2026-06-18  
**Verze:** 1.0.0

---

## 📋 CO BYLO VYTVOŘENO

### ✅ 1. VIETNAMSKÁ VERZE APLIKACE
**Soubor:** `A_GROSS_SOS_VI.html`

- **Lokalizace:** Profesionální transkreace (ne strojový překlad)
  - Oslovení: Formální tón (Quý vị, Anh/Chị)
  - Termin: Vietnamské obchodní expresy (Giá mua, Lợi nhuận, etc.)
  - Styl: Krátké, funkční texty (max. 2-3 slova na tlačítko)

- **Funkčnost:**
  - ✅ Offline režim (IndexedDB pro místní ukládání)
  - ✅ Katalog produktů v CZK/VND
  - ✅ Vyhledávání + skenování čárových kódů
  - ✅ Nákupní košík s kalkulací marže
  - ✅ Správa obchodů (registrace, kontakty)
  - ✅ Historie objednávek
  - ✅ Synchronizace katalogu (když je dostupný internet)

### ✅ 2. SERVICE WORKER (OFFLINE REŽIM)
**Soubor:** `sw.js`

- **Caching strategie:**
  - Network-first: HTML, CSS, JS (vždy pokusy o nové verze)
  - Cache-first: Obrázky, fonty (používá uložené kopie)
  - Fallback: Offline page při selhání

- **Background Sync:**
  - Automaticky synchronizuje offline objednávky když je WiFi

- **Instalace:**
  1. Umístěte `sw.js` do kořenového adresáře
  2. Aplikace automaticky zaregistruje Service Worker
  3. Testujte: Offline režim v DevTools (F12 → Network → Offline)

### ✅ 3. ADMIN BACKEND (MĚSÍČNÍ REPORTING)
**Soubor:** `backend_admin.py`

**Endpoints:**

```bash
# 1. Příjem offline objednávek
POST /api/orders/sync
{
  "storeId": "123",
  "storeName": "Coopmark – HCM",
  "items": [...],
  "nc": 197.20,
  "marze": 281.80,
  "date": "2026-06-18T10:30:00Z"
}
→ Vrátí: {"orderId": "ORD-1718xxx"}

# 2. Měsíční report pro síť (pro vyplacení komisí)
GET /api/reports/monthly?network=Provector&year=2026&month=6
→ Vrátí:
{
  "network": "Provector",
  "period": "Červen 2026",
  "total_purchase_value": 450000,
  "commission_rate": 0.05,
  "commission_amount": 22500,
  "stores": [
    {
      "store_name": "Coopmark HCM",
      "orders_count": 15,
      "total_purchase": 150000,
      "commission": 7500
    }
  ]
}

# 3. Export do CSV (pro emailing)
GET /api/reports/monthly/export?network=Provector&year=2026&month=6
→ Vrátí CSV soubor pro Excel

# 4. Synchronizace katalogu
GET /api/catalogs/sync
→ Vrátí JSON s aktuálními cenami a produkty

# 5. Health check
GET /health
→ Vrátí: {"status": "ok"}
```

**Konfigurační sazby komisí (`backend_admin.py`):**
```python
COMMISSION_RATES = {
    'Provector': 0.05,      # 5%
    'MO Partner': 0.05,     # 5%
    # Přidat dle dohod
}
```

---

## 🔧 INSTALACE & SPUŠTĚNÍ

### Frontend (Vietnamská aplikace)

1. **Odkaz pro vietnamské partnery:**
   ```
   https://a-gross.cz/app/vi/
   # nebo na localhost:
   file:///C:/Users/.../A_GROSS_SOS_VI.html
   ```

2. **Prvotní setup:**
   - Otevřou aplikaci v mobilním prohlížeči
   - Zaregistrují svou prodejnu (jméno, adresa, kontakt)
   - Nastaví URL katalogu (v Nastavení)
   - Aplikace stáhne seznam produktů do IndexedDB

3. **Test offline režimu:**
   - F12 → DevTools
   - Network tab → Offline (checkbox)
   - Aplikace stále funguje s lokálními daty

### Backend (Admin)

**Instalace:**
```bash
# 1. Nainstalovat Python 3.8+
# 2. Nainstalovat dependencies
pip install flask flask-cors python-dateutil

# 3. Spustit
python backend_admin.py

# 4. Server běží na:
http://localhost:5000

# 5. Test:
curl "http://localhost:5000/api/reports/monthly?network=Provector&year=2026&month=6"
```

**Docker (pro deployment):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend_admin.py .
RUN pip install flask flask-cors
CMD ["python", "backend_admin.py"]
```

---

## 📊 PRACOVNÍ TOK OBJEDNÁVKY

### Vietnamský nákupčí (Online)

1. Otevře aplikaci
2. Vybere svou prodejnu
3. Hledá produkty (vyhledávání, skenování EAN)
4. Přidává do košíku (marže se počítá v reálném čase)
5. Kontrola: Minimální objednávka 1.2M VND ✓
6. Klikne "Gửi đơn" (Odeslat objednávku)
7. Objednávka se pošle na `objednavky@a-gross.cz` (integrace s emailem)
8. **Zároveň** se uloží v offline databázi (IndexedDB)

### Vietnamský nákupčí (Offline)

1. Otevře aplikaci (bez internetu)
2. Vidí "🌐 Chế độ ngoại tuyến" badge
3. Normálně objednává
4. Objednávka se uloží lokálně
5. Když se připojí k WiFi → automaticky se synchronizuje

### Admin (Měsíční reporting)

1. **Koncem měsíce:**
   ```bash
   curl "http://localhost:5000/api/reports/monthly?network=Provector&year=2026&month=6"
   ```

2. **Dostane přehled:**
   - Počet aktivních obchodů
   - Počet objednávek
   - Součet nákupů bez DPH
   - Vypočítaná provize (5%)
   - Detaily po obchodě

3. **Exportuje do Excel:**
   ```bash
   curl "http://localhost:5000/api/reports/monthly/export?network=Provector" > report.csv
   ```

4. **Pošle emailem:**
   - Šablona: `EMAIL_PROVECTOR_REPORT.txt`
   - Příjemce: `finance@provector.cz`
   - Obsah: CSV s komisí

---

## 📱 TECHNICKÉ DETAILY

### IndexedDB Struktura

```javascript
Database: AGrossSOS (v1)

ObjectStores:
├─ products {keyPath: 'kod'}
│  └─ {kod, nazev, nc, moc, ean, ...}
│
├─ orders {keyPath: 'id'}
│  └─ {id, storeId, storeName, items, nc, marze, moc, date, synced}
│
├─ stores {keyPath: 'id'}
│  └─ {id, name, chain, manager, phone, address}
│
└─ sync {keyPath: 'key'}
   └─ {key: 'lastSync', value: '2026-06-18T10:00:00Z'}
```

### localStorage Klíče

```
ag_catalog_vi        → Katalog (backup IndexedDB)
ag_stores_vi         → Registrované obchody
ag_cart_vi           → Aktuální košík
ag_orders_vi         → Všechny objednávky
ag_store_vi          → Aktuálně vybraný obchod
ag_lastord_vi        → Poslední objednávka per produkt
ag_catalog_url_vi    → URL pro sync katalogu
```

### Service Worker Caching

```
CACHE_VERSION = 'agross-v1'

Network-first (HTML/CSS/JS):
  1. Zkus síť
  2. Pokud OK → ulož do cache
  3. Pokud selhá → vrať z cache
  4. Pokud v cache není → chyba

Cache-first (Fonty/Obrázky):
  1. Zkus cache
  2. Pokud OK → vrať
  3. Pokud není → zkus síť
  4. Pokud OK → ulož a vrať
```

---

## 🌍 INTEGRACE S VIETNAMEM

### Co je lokalizováno

| Česky | Vietnamština | Kontext |
|-------|--------------|---------|
| Nákupní cena | Giá mua | Finance |
| Marže | Lợi nhuận | Finance |
| Prodejny | Cửa hàng | UI |
| Košík | Giỏ hàng | E-commerce |
| Objednávka | Đơn hàng | Logistika |
| Offline režim | Chế độ ngoại tuyến | Tech |
| Synchronizace | Đồng bộ hóa | Tech |

### Měny & Formáty

```javascript
// Vietnamština
new Intl.NumberFormat('vi-VN').format(1234567)
→ "1.234.567"

// S jednotkou
fmt(n) + ' VND'
→ "1.234.567 VND"

// Vs. Česky (pro porovnání)
new Intl.NumberFormat('cs-CZ').format(1234567)
→ "1 234 567"
```

### Vietnamská podpora

- **Telefon support:** +84 9xx xxxx xxx (čekatel)
- **Email support:** support@a-gross.vn
- **WhatsApp:** +84 9xx xxxx xxx
- **Hodiny:** 8:00–17:00 (Hanoi time = UTC+7)

---

## 🧪 TESTOVÁNÍ

### 1. Offline Režim

```bash
# V prohlížeči (DevTools → F12)
1. Otevřít DevTools
2. Network tab
3. Zatrhnout "Offline"
4. Aplikace stále funguje
5. Objednávky se ukládají lokálně
```

### 2. Synchronizace

```bash
# Simulace online
1. DevTools → Network → Online
2. Kliknutí "↻ Đồng bộ ngay" (Sync Now)
3. Aplikace pokusí stáhnout nový katalog
4. Log v DevTools Console
```

### 3. Backend

```bash
# Localhost
python backend_admin.py
curl http://localhost:5000/health
→ {"status": "ok"}

# Test přijetí objednávky
curl -X POST http://localhost:5000/api/orders/sync \
  -H "Content-Type: application/json" \
  -d '{
    "storeId": "test123",
    "storeName": "Test Store",
    "items": [{"kod": "276921", "nazev": "Kim", "nc": 39.44, "qty": 5}],
    "nc": 197.20,
    "marze": 281.80,
    "moc": 479.00,
    "date": "2026-06-18T10:00:00Z"
  }'

# Měsíční report
curl "http://localhost:5000/api/reports/monthly?network=Provector&year=2026&month=6"
```

### 4. Ceník Import

```bash
# Příprava CSV (z Excelu)
kod;nazev;nc;moc;ean
276921;JEHLY ORGAN;39.44;95.90;8590580899993
...

# Převod na JSON (Python)
import csv
import json

with open('cenik.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    products = list(reader)

with open('cenik.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)
```

---

## 📈 ROADMAP (PŘÍŠTÍ FÁZE)

### Fáze 2 (Červenec–Srpen)

- [ ] **Admin Panel (web)** – Správa sítí, ceníků, reporty v real-time
- [ ] **Push Notifikace** – Firebase Cloud Messaging
- [ ] **Fotografie produktů** – CDN + komprese pro mobily
- [ ] **PDF faktury** – Generace v CZ/VN formátu
- [ ] **Statistiky & Analytics** – Grafy prodejů per síť
- [ ] **Kalkulačka marže** – Pokročilé scénáře (množstevní slevy)

### Fáze 3 (Září–Říjen)

- [ ] **Mobilní aplikace (iOS/Android)** – React Native
- [ ] **Platební brána** – Stripe/Momo (Vietnam)
- [ ] **Integrací s účetníctvím** – Export do knihy jízd
- [ ] **Chytrý inventář** – Predikce zásob

### Fáze 4 (Listopad+)

- [ ] **AI chatbot** – Tiếng Việt support 24/7
- [ ] **Marketplace** – Vietnamští nákupčí si kupují navzájem
- [ ] **Franchise model** – Scalování na dalších sítích

---

## 🔐 BEZPEČNOST

### Offline Databáze

```javascript
// IndexedDB je privátní per domain
// Nešifruje se automaticky ❌

// Doporučení:
// 1. Neukládat hesla (OK – používáme OAuth)
// 2. Šifrovat citlivá data:
//    localStorage.setItem('ag_secret', btoa(JSON.stringify(data)))
// 3. Auto-delete po 30 dnech nepoužití
```

### Server Backend

```python
# Doporučení:
1. HTTPS vždy
2. Authentication token (JWT)
3. Rate limiting (100 req/min)
4. CORS whitelist (jen a-gross.cz)
5. Database backup (daily)
```

---

## 📞 SUPPORT & KONTAKTY

### Czech Side
- **IT:** it@a-gross.cz
- **Obchodní:** objednavky@a-gross.cz
- **Telefon:** +420 585 xxx xxx

### Vietnam Side (TODO)
- **Support:** support@a-gross.vn (najměte!)
- **WhatsApp:** +84 9xx xxxx xxx
- **Facebook:** A-GROSS SOS Vietnam

---

## 📚 PŘÍLOHY

### 1. Ceník produkty (XLSX → JSON)
```json
[
  {
    "kod": "276921",
    "nazev": "JEHLY ORGAN UNIVERSAL 10ks",
    "nc": 39.44,
    "moc": 95.90,
    "ean": "8590580899993"
  }
]
```

### 2. Struktura objednávky
```json
{
  "id": "ORD-1718700000000",
  "storeId": "coop_hcm_001",
  "storeName": "Coopmark – Ho Chi Minh",
  "date": "2026-06-18T10:30:00Z",
  "items": [
    {
      "kod": "276921",
      "nazev": "Kim Organ Universal",
      "nc": 39.44,
      "qty": 5,
      "marze": 56.46
    }
  ],
  "nc": 197.20,
  "marze": 281.80,
  "moc": 479.00,
  "delivery": "Ihned (24h)",
  "status": "new",
  "synced": true,
  "synced_at": "2026-06-18T10:30:15Z"
}
```

### 3. Email šablona (Měsíční provize)
```
Předmět: A-GROSS SOS – Měsíční report & Provize – Červen 2026

---

Vážené kolegové,

V příloze naleznete měsíční report za období červen 2026:

**SOUHRN**
• Síť: Provector
• Registrované prodejny: 24
• Aktivní objednávky: 156
• Nákupní ceny bez DPH: 450.000 CZK
• Provize (5%): 22.500 CZK
• Status: ✓ Schválit k výplatě

Detailní přehled po prodejnách naleznete v připojeném souboru.

Děkujeme za spolupráci!

---
A-GROSS, s.r.o. | Olomouc-Holice
```

---

**Poslední aktualizace:** 2026-06-18  
**Kontakt:** it@a-gross.cz
