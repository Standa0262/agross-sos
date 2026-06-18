# 🚀 QUICK START – 5 Minut na Spuštění

Pro rychlý start všech 4 nových funkcí:

---

## 1️⃣ Backend Server (3 minuty)

```bash
# Instalace
pip install flask flask-cors firebase-admin reportlab

# Spuštění
python backend_extended.py

# Výstup:
# 🚀 A-GROSS SOS Extended Backend
# 📊 Admin Panel: http://localhost:5000/admin_panel.html
# 📞 API: http://localhost:5000
```

**✓ Backend je online!**

---

## 2️⃣ Admin Panel (30 sekund)

```
Otevřít v prohlížeči:
http://localhost:5000/admin_panel.html
```

**Interakce:**
- 📊 **Dashboard** → Vidíš KPI, grafy
- 🌐 **Sítě** → Přidej novou síť (Provector, MO Partner)
- 📦 **Ceník** → Zobrazí 20+ produktů
- 📋 **Objednávky** → Filtruj a vidíš objednávky
- 🔔 **Notifikace** → Pošli test notifikaci
- 📈 **Reporty** → Generuj měsíční report

**✓ Admin panel funguje!**

---

## 3️⃣ Push Notifikace (Volitelné – 10 minut)

### Setup Firebase

1. Jdi na https://console.firebase.google.com
2. Vytvoř nový projekt `A-GROSS-SOS`
3. Aktivuj **Cloud Messaging**
4. Generuj **Service Account Key** → Ulož jako `firebase-key.json` do root
5. Zkopíruj **Web App Config**

### Integrace do Web App

V `A_GROSS_SOS_VI.html` přidej (v `<head>`):

```html
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging.js"></script>
```

Na konec `<script>` sekce:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "a-gross-sos.firebaseapp.com",
  projectId: "a-gross-sos",
  storageBucket: "a-gross-sos.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

async function registerForPushNotifications() {
  try {
    const token = await messaging.getToken({
      vapidKey: 'YOUR_VAPID_KEY'
    });
    
    await fetch('http://localhost:5000/api/fcm/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        device_token: token,
        store_id: localStorage.getItem('storeId')
      })
    });
  } catch (err) {
    console.error('Push error:', err);
  }
}

// Příjem notifikací
messaging.onMessage((payload) => {
  const banner = document.createElement('div');
  banner.innerHTML = `
    <div style="background: #2a7a4a; color: white; padding: 15px; margin: 10px; border-radius: 8px;">
      <strong>${payload.notification.title}</strong><br>
      ${payload.notification.body}
    </div>
  `;
  document.body.insertBefore(banner, document.body.firstChild);
  setTimeout(() => banner.remove(), 5000);
});

// Zavolej na start
if (Notification.permission === 'granted') {
  registerForPushNotifications();
} else if (Notification.permission !== 'denied') {
  Notification.requestPermission().then(() => {
    registerForPushNotifications();
  });
}
```

### Test v Admin Panelu

1. Otevřít Admin Panel
2. Jít na tab **Notifikace**
3. Napsat a poslat notifikaci
4. Měla by se objevit na webovém klientovi

**✓ Push notifikace funguje!**

---

## 4️⃣ PDF Faktury (Automaticky)

Backend už umí generovat PDF:

```bash
# Objednávka PDF
GET http://localhost:5000/api/orders/order-123/pdf

# Report PDF
GET http://localhost:5000/api/reports/report-123/pdf?network=Provector&year=2026&month=6
```

V Admin Panelu:
- **Objednávky** → Detail objednávky → Klikni na "PDF"
- **Reporty** → Vygeneruj → "📥 Export PDF"

**✓ PDF faktury fungují!**

---

## 5️⃣ React Native App (5 minut)

```bash
# Vytvoř nový projekt
npx react-native init A_GROSS_SOS_RN
cd A_GROSS_SOS_RN

# Instaluj dependencies
npm install @react-native-async-storage/async-storage react-native-chart-kit react-native-vector-icons

# Zkopíruj App.js
cp ../REACT_NATIVE_APP.js ./App.js

# Spusť na Android
npm run android

# Nebo na iOS
npm run ios
```

**Funkce v aplikaci:**
- 📊 **Home** – Registrace obchodu, KPI, trend
- 📦 **Produkty** – Procházení katalog, přidání do košíku
- 🛒 **Košík** – Edit, odeslání objednávky
- 📋 **Historie** – Předchozí objednávky

**Offline režim:**
- Když je server offline → používá uložený katalog
- Když se vrátí online → automaticky synchronizuje
- Indikátor 🟢 Online / 🔴 Offline

**✓ React Native app funguje!**

---

## 📊 Ověření – Všechno Funguje?

- [ ] Backend běží (`http://localhost:5000`)
- [ ] Admin Panel načítá (`admin_panel.html`)
- [ ] API endpointy jsou dostupné:
  ```bash
  curl http://localhost:5000/api/networks
  curl http://localhost:5000/api/stats/monthly
  curl http://localhost:5000/api/stores/top
  ```
- [ ] Firebase notifikace přijímá (pokud nakonfigurován)
- [ ] PDF se generují
- [ ] React Native app běží na emulátoru/zařízení

---

## 🎯 Příklad Workflow

### Prodávající (Store Owner)

1. Otevře web app: `http://localhost:5000/A_GROSS_SOS_VI.html`
2. Zaregistruje obchod (Vietnamské jméno)
3. Procházuje produkty, přidává do košíku
4. Odešle objednávku (lokálně uloženo + online sync)
5. Vidí historii objednávek
6. Dostane push notifikaci (Nový katalog, ceny, atd.)

### Admin (Network Manager)

1. Otevře Admin Panel: `http://localhost:5000/admin_panel.html`
2. Vidí dashboard – KPI, top obchody
3. Spravuje sítě (Provector, MO Partner)
4. Filtruje objednávky
5. Generuje měsíční report
6. Pošle push notifikaci všem prodávajícím
7. Exportuje report jako PDF a pošle emailem

---

## 🔧 Troubleshooting

**Backend se nenačte?**
```bash
# Zkontroluj, jestli máš Flask
pip list | grep Flask

# Zkontroluj port
lsof -i :5000
# Pokud obsazeno: kill -9 <PID>
```

**Admin Panel zobrazí chybu?**
- Zkontroluj, že backend běží
- Otevři Developer Console (F12) a check chyby
- Zkus F5 (refresh)

**Firebase notifikace se neobjevuje?**
- Zkontroluj, že máš `firebase-key.json` v root
- Ověř Web App config (apiKey, projectId, atd.)
- Zkus Chrome DevTools → Application → Service Workers

**React Native se nenačte?**
```bash
# Vymaž node_modules
rm -rf node_modules
npm install

# Vymaž cache
npm start -- --reset-cache
```

---

## 📱 Na Mobilním Zařízení

Chceš spustit na skutečném telefonu?

**Android:**
1. Připoj zařízení USB
2. `adb devices` (zkontroluj, že vidíš zařízení)
3. `npm run android`

**iOS:**
1. Připoj na Xcode
2. `npm run ios`

---

## ✅ Hotovo!

Všechny 4 funkce běží:
- ✅ Admin Panel – Web dashboard
- ✅ Push Notifikace – Firebase
- ✅ PDF Faktury – Server-side
- ✅ React Native – iOS/Android

**Teď jdeš na production? Čti `DEPLOYMENT_GUIDE.md`**

---

**Potřebuješ help? Čti:**
- 📘 `COMPLETE_FEATURES.md` – Detailní dokumentace
- 🔧 `FIREBASE_SETUP.md` – Firebase setup
- 🚀 `DEPLOYMENT_GUIDE.md` – Production nasazení
