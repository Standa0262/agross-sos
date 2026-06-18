# Firebase Cloud Messaging – Setup Guide

## 1. Vytvoření Firebase Project

### V Google Console (https://console.firebase.google.com/)

1. Klikni na **+ Přidat projekt**
2. Jméno: `A-GROSS-SOS`
3. Vyberi region: `Europe – prague`
4. Vyčkej na inicializaci

## 2. Povolení Cloud Messaging

1. V levém menu klikni na **Cloud Messaging**
2. Klikni na **Povolení** (Enable)
3. Vyberi payment plan (free tier je OK)

## 3. Service Account Key

1. V levém menu jdi na **Nastavení projektu** (Project Settings) → ikona ⚙️
2. Jdi na **Service Accounts** tab
3. Klikni na **Generovat nový privátní klíč** (Generate New Private Key)
4. Stáhne se `a-gross-sos-xxxxxxx.json`
5. **Přejmenuj na `firebase-key.json`** a ulož do projectu

## 4. Web App Configuration

1. V Console Firebase klikni na ikonku webové aplikace
2. Zkopíruj config:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "a-gross-sos.firebaseapp.com",
  projectId: "a-gross-sos",
  storageBucket: "a-gross-sos.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

## 5. Service Worker pro Web App

V `A_GROSS_SOS_VI.html` přidej na začátek `<head>`:

```html
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging.js"></script>
```

Na konec `<script>` sekce přidej:

```javascript
// Firebase Messaging Setup
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

// Registrace pro push notifikace
async function registerForPushNotifications() {
  try {
    const token = await messaging.getToken({
      vapidKey: 'YOUR_VAPID_KEY'
    });
    
    // Poslat token na backend
    await fetch(`${API_URL}/api/fcm/register`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        device_token: token,
        store_id: localStorage.getItem('storeId')
      })
    });
    
    console.log('✓ Zaregistrován pro push notifikace:', token);
  } catch (err) {
    console.error('Push notifikace chyba:', err);
  }
}

// Příjem notifikací v popředí
messaging.onMessage((payload) => {
  console.log('📬 Notifikace přijata:', payload);
  
  // Zobrazit banner
  const banner = document.createElement('div');
  banner.innerHTML = `
    <div style="background: #2a7a4a; color: white; padding: 15px; border-radius: 8px; margin: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
      <strong>${payload.notification.title}</strong><br>
      ${payload.notification.body}
    </div>
  `;
  document.body.insertBefore(banner, document.body.firstChild);
  
  // Zavřít po 5 sekundách
  setTimeout(() => banner.remove(), 5000);
});

// Pokud je stránka zavřena, notification se zobrazí v systému
messaging.onBackgroundMessage((payload) => {
  const options = {
    body: payload.notification.body,
    icon: '/icon-192x192.png',
    badge: '/badge-72x72.png',
    tag: payload.notification.title,
    requireInteraction: false
  };
  
  self.registration.showNotification(
    payload.notification.title,
    options
  );
});

// Zavolej při startu aplikace
if (Notification.permission === 'granted') {
  registerForPushNotifications();
} else if (Notification.permission !== 'denied') {
  Notification.requestPermission().then(() => {
    registerForPushNotifications();
  });
}
```

## 6. Spuštění Backend

```bash
pip install firebase-admin
python backend_extended.py
```

## 7. Testování v Admin Panelu

1. Otevři `http://localhost:5000/admin_panel.html`
2. Jdi na tab **Notifikace**
3. Napiš a pošli test notifikaci
4. Měla by se objevit na webovém klientovi

## Troubleshooting

- **401 Unauthorized**: Zkontroluj `firebase-key.json` v root directoru
- **Token invalid**: Regeneruj VAPID key v Firebase Console
- **Notifikace se neobjevuje**: Ověř, že je app v popředí a má permission
