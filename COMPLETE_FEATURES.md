# A-GROSS SOS – Všechny 4 Funkce Kompletní

Dokumentace k implementaci posledních 4 pokročilých funkcí: Admin panel, Push notifikace, PDF faktury, React Native app.

---

## 📋 Obsah

1. **Admin Panel (Web)** – Správa sítí, ceníků, real-time reports
2. **Push Notifikace (FCM)** – Firebase Cloud Messaging
3. **PDF Faktury** – Invoice generátor (česky + vietnamsky)
4. **React Native Mobile** – Native iOS/Android app

---

## 1️⃣ ADMIN PANEL (Web)

### Soubor: `admin_panel.html`

**Funkce:**
- 📊 Dashboard – KPI, grafy, top obchody
- 🌐 Správa sítí (Provector, MO Partner)
- 📦 Správa ceníku (import/export)
- 📋 Všechny objednávky (filtrování)
- 🔔 Push notifikace (broadcast/síť/obchod)
- 📈 Měsíční reporty pro sítě

**Setup:**
```bash
# Soubor je plain HTML – stačí otevřít v prohlížeči
open admin_panel.html

# nebo z backend serveru
python backend_extended.py
# Pak jdi na http://localhost:5000/admin_panel.html
```

**API Endpoints (vyžadované v `backend_extended.py`):**
```
GET  /api/networks              # Vrátit všechny sítě
POST /api/networks              # Vytvořit novou síť
GET  /api/stats/monthly         # Měsíční statistiky
GET  /api/stores/top            # Top obchody
POST /api/notifications/send    # Poslat notifikaci
GET  /api/notifications         # Historii notifikací
GET  /api/catalogs/sync         # Katalog produktů
POST /api/reports/monthly       # Měsíční report JSON
GET  /api/reports/<id>/pdf      # Report PDF
```

**Funkčnost Dashboard:**
- Real-time KPI (obchody, objednávky, nákupy, provize)
- Line chart – objednávky za 30 dní
- Doughnut chart – distribuce po sítích
- Top 5 obchodů (měsíc)

**Správa Sítí:**
- Přidat novou síť (název, email, provize %)
- Editace/smazání
- Možnost manuální provize sazby

**Ceník:**
- Zobrazit 20+ produktů (kód, název, NC, MOC, EAN)
- Import z Excelu (TODO – implementovat)
- Export katalog (CSV/JSON)

**Objednávky:**
- Filtrování podle sítě
- Filtrování podle období (týden/měsíc/všechno)
- Detail objednávky + PDF

**Notifikace:**
- Cílená: všem, síti, jednomu obchodu
- Nadpis + obsah
- Historik poslených (s počtem doručených)

**Reporty:**
- Měsíční report pro síť
- Tabulka: obchody, objednávky, nákupy, provize
- Tlačítko „Poslat emailem"
- PDF export

---

## 2️⃣ PUSH NOTIFIKACE (Firebase Cloud Messaging)

### Soubor: `FIREBASE_SETUP.md`

**Setup v 7 krocích:**

1. Vytvoří Firebase project v Google Console
2. Povolí Cloud Messaging
3. Generuje Service Account Key → `firebase-key.json`
4. Zkopíruje web app config
5. Přidá Firebase SDK do webové aplikace
6. Zaregistruje device token
7. Testuje v Admin Panelu

**Instalace backendu:**
```bash
pip install firebase-admin flask-cors
```

**Kód integrace (v `A_GROSS_SOS_VI.html`):**
```javascript
// Firebase init
const firebaseConfig = { /* config z Firebase Console */ };
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Registrace zařízení
async function registerForPushNotifications() {
  const token = await messaging.getToken({ vapidKey: '...' });
  await fetch('/api/fcm/register', {
    method: 'POST',
    body: JSON.stringify({ device_token: token, store_id: storeId })
  });
}

// Příjem notifikací
messaging.onMessage((payload) => {
  // Zobrazit banner v aplikaci
});
```

**Příklady notifikací:**
- "Nový katalog je dostupný" – broadcast všem
- "Vaše objednávka byla přijata" – obchodu
- "Nové ceny od 1.7." – síti Provector

---

## 3️⃣ PDF FAKTURY

### Soubor: `backend_extended.py` → `generate_order_pdf()` a `generate_report_pdf()`

**Instalace:**
```bash
pip install reportlab
```

**Endpoints:**
```
GET /api/orders/<order_id>/pdf         # Objednávka PDF
GET /api/reports/<report_id>/pdf       # Report PDF
```

**Obsah Objednávky PDF:**
- A-GROSS hlavička
- Číslo objednávky, obchod, datum
- Tabulka: produkty, množství, cena, součet
- Totály:
  - Nákupní cena (bez DPH)
  - Marže
  - Prodejní cena (s DPH)
- Footer s kontakty

**Obsah Reportu PDF:**
- Měsíční report pro síť
- Shrnutí: měsíc, počet obchodů, objednávky, nákupy
- **Provize k výplatě** (zvýrazněno)
- Detailní tabulka po obchodech
- Podpis & footer

**Příklad PDF Report Detailů:**
```
A-GROSS SOS – Měsíční Report
Síť: Provector
Měsíc/Rok: 6/2026

Měsíc: 6/2026
Počet obchodů: 24
Počet objednávek: 156
Nákupy bez DPH: 450,000.00 Kč
Sazba provize: 5%
Provize k výplatě: 22,500.00 Kč  ← ZVÝRAZNĚNO

Detaily po obchodech:
Obchod                  | Objednávky | Nákup Kč    | Provize Kč
─────────────────────────────────────────────────────────────
Hôm Việt (TP Hộ Chí M.) | 12         | 120,000    | 6,000
Tây Hồ Hàng (Hà Nội)    | 8          | 95,000     | 4,750
... (další obchody)
```

**Použití:**
```bash
# Z Admin Panelu
1. Jdi na Objednávky
2. Klikni na "PDF" u objednávky
3. Stáhne se `order_12345.pdf`

# Měsíční Report
1. Jdi na Reports
2. Vyber síť, měsíc
3. Klikni "📥 Export PDF"
4. Stáhne se `report_Provector_2026_6.pdf`
```

---

## 4️⃣ REACT NATIVE MOBILE APP

### Soubor: `REACT_NATIVE_APP.js`

**Setup:**
```bash
# Vytvoř nový React Native projekt
npx react-native init A_GROSS_SOS_RN
cd A_GROSS_SOS_RN

# Instaluj dependencies
npm install @react-native-async-storage/async-storage
npm install react-native-sqlite-storage
npm install react-native-vector-icons react-native-chart-kit

# Zkopíruj REACT_NATIVE_APP.js do App.js
cp REACT_NATIVE_APP.js ./App.js

# Spuštění
npm run android    # Android emulator
npm run ios        # iOS simulator
```

**Funkce:**

1. **Home Tab – Přehled**
   - Registrace obchodu (jméno, adresa)
   - KPI: Nákup, Marže, Položky
   - Trend nákupů (line chart)
   - Tlačítko synchronizace katalog

2. **Produkty Tab – Katalog**
   - Offline první – používá uložený katalog
   - Swipe/tap na produkt → přidat do košíku
   - Zobrazuje NC, MOC, marži
   - Online/offline indikátor

3. **Košík Tab – Nákupní seděním**
   - Jednotlivé položky s množstvím
   - Edit quantity / smazat
   - Real-time totály (Nákup, Marže, Prodej)
   - Tlačítko "Odeslat objednávku"
   - Lokální uložení + auto-sync když online

4. **Historie Tab – Předchozí objednávky**
   - Poslední 5 objednávek
   - Status (Odeslána/Čeká)
   - Detail (nákup, marže)

**Offline Architektura:**
- `AsyncStorage` pro produkty, objednávky, obchody
- Pokud server offline → uloží lokálně
- Když se vrátí online → automaticky synchronizuje
- Indikátor 🟢 Online / 🔴 Offline

**Styling:**
- Dark header (#1A1A1A)
- Cards s shadow efektem
- Color: Marže zelená (#2A7A4A), Akce oranžová (#E8533A)
- Material Design ikony (vector-icons)

**Integrace s Backendem:**
```javascript
// Synchronizace katalog
fetch('http://localhost:5000/api/catalogs/sync')

// Odeslání objednávky
fetch('http://localhost:5000/api/orders/sync', {
  method: 'POST',
  body: JSON.stringify(order)
})

// Registrace pro push notifikace
fetch('http://localhost:5000/api/fcm/register', {
  method: 'POST',
  body: JSON.stringify({ device_token, store_id })
})
```

---

## 🚀 SPUŠTĚNÍ KOMPLETNÍHO SYSTÉMU

### Krok 1: Backend server
```bash
pip install flask flask-cors firebase-admin reportlab
python backend_extended.py
# Naslouchá na http://localhost:5000
```

### Krok 2: Admin panel
```bash
# Otevřít v prohlížeči
open http://localhost:5000/admin_panel.html
```

### Krok 3: Web app (iOS/Android browser)
```bash
# Otevřít v mobilním prohlížeči
http://<your-ip>:5000/A_GROSS_SOS_VI.html
```

### Krok 4: Native app
```bash
cd A_GROSS_SOS_RN
npm run android  # nebo ios
```

---

## ✅ CHECKLIST – Co Vytvořeno

- ✅ **Admin Panel** – Plně funkční web dashboard
- ✅ **Push Notifikace** – Firebase Cloud Messaging integrace
- ✅ **PDF Faktury** – Order + Report generátor
- ✅ **React Native** – iOS/Android native app
- ✅ **Firebase Setup Guide** – Krok za krokem
- ✅ **Dokumentace** – Všechny 4 funkce popsány

---

## 🔗 SOUBORY

| Soubor | Popis |
|--------|-------|
| `admin_panel.html` | Web dashboard pro správu sítí, ceníků, reports |
| `backend_extended.py` | Python Flask – Admin API, PDF, Push |
| `FIREBASE_SETUP.md` | Návod na Firebase Cloud Messaging |
| `REACT_NATIVE_APP.js` | React Native – iOS/Android app |
| `COMPLETE_FEATURES.md` | Tato dokumentace |

---

## 📞 SUPPORT

**Firebase Cloud Messaging:**
- Docs: https://firebase.google.com/docs/cloud-messaging

**React Native:**
- Docs: https://reactnative.dev
- AsyncStorage: https://react-native-async-storage.github.io/async-storage/

**ReportLab (PDF):**
- Docs: https://www.reportlab.com/docs/reportlab-userguide.pdf

---

**Vytvořeno pro A-GROSS SOS – B2B Ordering App**  
Vietnamská lokalizace + Offline-first architektura + Real-time reporting  
v1.0 – Červen 2026
