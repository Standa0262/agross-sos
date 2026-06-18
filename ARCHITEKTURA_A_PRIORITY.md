# A-GROSS SOS – Architektura & Prioritizace

**Datum:** 2026-06-18  
**Projekt:** B2B Obchodní App pro vietnamské síťě potravinářské distribuce

---

## 🎯 PRIORITY FEATURES

### ✅ PRIORITA 1 – Základní funkčnost (Existující)
- [x] Výběr sítě/partnera (MO Partner, Provector, ...)
- [x] Přihlášení prodejny pod síť
- [x] Katalog produktů s vietnamšitinou
- [x] Vyhledávání & skenování čárových kódů
- [x] Nákupní ceny (bez DPH) – vidí jen daná síť
- [x] Marže v reálném čase
- [x] Nákupní košík

---

### ⚠️ PRIORITA 2 – Vietnamská lokalizace
**DOPORUČENÍ:** Komplexní překlad není stačit jen změnou jazyka.
- [ ] Všechny texty aplikace v češtině → vietnamštině
- [ ] Vietnamský formát cen (VND nebo USD)
- [ ] Vietnamský kalendář/datumový formát
- [ ] Vietnamská telefonní čísla pro support (formát +84)
- [ ] Lokalizované komentáře k produktům (+ balicí informace)
- [ ] PDF faktury v vietnamštině
- **Fáze realizace:** Najměte rodilého vietnamského překladatele! Není stačit Google Translate.

---

### 🔄 PRIORITA 3 – Ukládání dat & Offline režim

#### **Problém:** Vietnamská infrastruktura má pomalý internet
#### **Doporučené řešení – HYBRIDNÍ PŘÍSTUP:**

#### 3a) **Lokální ukládání v telefonu (IndexedDB)**
```javascript
// Správa dat přímo v prohlížeči
const db = new Dexie('AGrossSOS');
db.version(1).stores({
  products: 'id, category',
  orders: 'id, createdAt',
  prices: 'id, networkId',
  userSettings: 'id'
});

// Automatické synchronizace když je WiFi:
async function syncToServer() {
  if (navigator.onLine) {
    const unsyncedOrders = await db.orders.where('synced').equals(false).toArray();
    // Odeslání na server
    // Stažení nových produktů, cen, atd.
  }
}
```

#### 3b) **Jak funguje OFFLINE:**
1. **Při prvním spuštění:** App stáhne katalog produktů + ceny pro danou síť
2. **Při objednávce offline:** Objednávka se uloží lokálně (IndexedDB/SQLite)
3. **Při připojení internetu:** Automaticky se synchronizuje se serverem
4. **Indikátor:** Ikona ⚠️ "Offline režim" v headeru

#### 3c) **Server-side:**
- PostgreSQL databáze pro správu objednávek
- API endpoint: `/api/sync` – příjem offline objednávek
- Verze produktů/cen – kontrola zda je aplikace aktuální

**Výhody:**
- Prodejna může objednat i bez internetu
- Automatická synchronizace když se připojí
- Nižší datový nárok

---

### 💰 PRIORITA 4 – Ceník & Marže

#### **Struktura dat (XLSX → Database):**
```
Prodejca: PROVECTOR
├─ ID produktu: 12345
├─ Nákupní cena bez DPH: 120 CZK
├─ MOC (Minimum Order Qty): 5 ks
├─ Marže %: 35%
└─ Kalkulované prodejní ceny:
   • 120 × (1 + 0.35) = 162 CZK s 35% marží
```

#### **Kde se zobrazuje marže:**
- ✅ Při hledání produktu (v seznamu)
- ✅ V detailu produktu
- ✅ V košíku (celková kalkulovaná výše marže)
- ✅ Na účtence/exportu

#### **Implementace:**
- CSV import z `cenik_produkty.xlsx`
- Uživatelský panel pro adminy: Nahrát nový ceník
- Verze ceníků – kontrola aktuality

---

## 🏢 SYSTÉM SÍTÍ A KOMISÍ

### Struktura:
```
SÍŤĚ DISTRIBUCE
├─ MO Partner
│  ├─ Provize: 5% z nákupních cen bez DPH
│  ├─ Počet prodejen: N
│  └─ Objednávky v měsíci: AUTO-KALKULACE
│
├─ Provector
│  ├─ Provize: [dle dohody]
│  ├─ Počet prodejen: N
│  └─ Objednávky v měsíci: AUTO-KALKULACE
│
└─ Další síť...
```

### Měsíční Report pro sít (pro vyplácení provizí):
```
MĚSÍČNÍ SOUHRN – Provector – Červen 2026
─────────────────────────────────────────
Počet zaregistrovaných prodejen: 24
Počet aktivních objednávek: 156
Součet nákupních cen (bez DPH): 450,000 CZK
Provize 5%: 22,500 CZK
Stav platby: [Zaplaceno / Čeká se]

Detaily po prodejnách:
Prodejna XYZ: 15 objednávek, 25,000 CZK → Podíl sítě: 1,250 CZK
```

**Implementace:**
- Exportní Report → PDF/Excel
- Generování 1× měsíčně automaticky
- Email notifikace příslušným sítím

---

## 🖼️ FOTOGRAFIE PRODUKTŮ

### Strategie:
1. **Zatím bez fotek** – Používat barvy/kategorie
2. **Když budou k dispozici:**
   - Nahrání přes admin panel
   - Komprese & CDN (pro mobily s pomalým internetem)
   - Thumbnaily pro seznam, full pro detail

---

## 📄 PDF EXPORT

### Funkčnost:
- ✅ Objednávku → Tisknutelné PDF
- ✅ Měsíční přehled → PDF
- ✅ Fakturu → PDF (vietnamské formáty)

**Tech stack:** `pdfkit` nebo `jsPDF` pro JavaScript

---

## 🔔 NOTIFIKACE

### Typy:
- **Push notifikace** – Nová objednávka, změna stavu
- **In-app notifikace** – Obsah kuponů, slevy
- **Email** – Měsíční zpráva pro síť, potvrzení objednávky

**Tech:** Firebase Cloud Messaging (FCM)

---

## 📊 STATISTIKY & ANALYTIKA

### Per Síť (Dashboard pro admina):
- Počet aktivních prodejen
- Počet objednávek (měsíčně, týdně, denně)
- Nejoblíbenější produkty
- Objem nákupů v čase (graf)
- Marže statistika

### Per Prodejna:
- Jejich nákupní historie
- Nejčastěji objednávané produkty
- Trend nákupů

**Tech:** Chart.js nebo Apache ECharts

---

## 🧮 KALKULAČKA MARŽE

### Funkce (JIŽ EXISTUJÍCÍ v app):
```
Marže se počítá REÁLNĚ v čase:
- Nákupní cena: 100 CZK
- Marže sazba: 35%
- Prodejní cena: 135 CZK
- Zisk na kus: 35 CZK

V košíku se automaticky zobrazuje:
- Počet produktů
- Součet nákupu
- Součet marže (kolik si vydělají)
```

---

## 📡 OFFLINE REŽIM

### Kapacita:
- Katalog až 5000 produktů (≈50MB)
- Místní objednávky: Neomezené
- Service Worker – Pracuje i bez internetu

### Indikátory:
- Status bar: "🔴 Offline" nebo "🟢 Online"
- Tlačítko: "Synchronizuj teď"

---

## 🛠️ TECHNOLOGICKÁ ARCHITEKTURA

```
FRONTEND (Progressive Web App)
├─ Framework: HTML5 + Vanilla JS (nebo React/Vue)
├─ Lokální storage: IndexedDB (Dexie.js)
├─ Offline: Service Worker + Cache API
├─ Notifikace: Push API
└─ Barcode scanning: BarcodeDetector API

↓↑

BACKEND (Node.js / Python)
├─ API (REST/GraphQL)
├─ Database: PostgreSQL
├─ File storage: AWS S3 nebo Azure Blob
├─ Komunikace sítím: Email + PDF reports
└─ Analytics: Mixpanel nebo Google Analytics

↓↑

ADMIN PANEL
├─ Správa sítí a komisí
├─ Upload cen (XLSX)
├─ Generování reportů
└─ User management
```

---

## 📋 IMPLEMENTAČNÍ PLÁN

### Fáze 1 (Týdny 1-2): Vietnamská lokalizace
- [ ] Překlad všech textů
- [ ] Testování v produkci

### Fáze 2 (Týdny 3-4): Offline & Synchronizace
- [ ] IndexedDB integrace
- [ ] Service Worker
- [ ] Sync algoritmus

### Fáze 3 (Týden 5): Ceník & Marže
- [ ] Import ze XLSX
- [ ] Kalkulace marže v reálném čase
- [ ] Admin panel pro nahrávání

### Fáze 4 (Týdny 6-7): Reporting
- [ ] Měsíční report pro sítě
- [ ] PDF export
- [ ] Automatické emaily

### Fáze 5 (Týdny 8+): Pokročilé funkce
- [ ] Fotografie produktů (až budou k dispozici)
- [ ] Push notifikace
- [ ] Analytics & statistiky

---

## ⚠️ KRITICKÉ POZNÁMKY

### Vietnam-specific:
1. **Jazyk:** Ne jen překlad! Doporučuji rodilého Vietnamce
2. **Valuta:** Standardně se používá VND, ne USD/CZK
3. **Čas & Datum:** UTC+7 (Vietnam Standard Time)
4. **Čárové kódy:** Vietnamské produkty mohou mít odlišný formát

### Technické:
1. **OFFLINE je KRITICKÉ** – Internet v Vietnamu je velmi nestabilní
2. **Mobilní optimalizace** – Většina bude přes 4G na malých telefonech
3. **Bezpečnost:** Šifrovat citlivá data objednávek v localStoragi

---

## ✉️ KONTAKTY NA PODPORU

- **Vietnam Customer Support:** +84 9xx xxxx xxx (telefonní linka)
- **Admin Support:** email@agross.cz
- **IT Help Desk:** IT support team

---

*Poslední aktualizace: 2026-06-18*
