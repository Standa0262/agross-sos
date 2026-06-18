# TECHNICKÉ ZADÁNÍ: Systém Regionální Exkluzivity (GPS Ochrana Trhu)

## 1. PŘEHLED FUNKCIONALITY

Systém automaticky ověřuje, zda nová prodej (registrace) nespadá do již obsazené lokality. Rozhodnutí je založeno na:
- **Populaci obce** (z DB občanů ČR)
- **GPS vzdálenosti** od ostatních aktivních prodeje v síti
- **Zásada exkluzivity**: 1 modul v obci do 3 000 obyv., min. 800 m mezi moduly v městech

---

## 2. DATOVÉ PODKLADY

### 2.1 Zdroje dat
- **GPS souřadnice**: Prodej při registraci zadá adresu → aplikace geocoduje pomocí Google Maps API (nebo OpenStreetMap)
- **Databáze obcí ČR**: CSV/JSON se seznamem všech obcí, jejich populace a souřadnic
  - Zdroj: ČSÚ (Český statistický úřad) nebo prostřednictvím služby jako Nominatim (OpenStreetMap)
  - Minimální pole: `nazev_obce`, `pocet_obyvatel`, `lat`, `lng`, `okres`

### 2.2 Konfigurace pravidel
```
MALÁ OBEC (0 - 3000 obyvatel):
  - MAX_MODULY_V_OBCI = 1
  - AKCE = "Odmítnutí" (prodej si musí vybrat jinou obec)

STŘEDNÍ/VELKÁ OBEC (3001+):
  - MIN_VZDALENOST_METRŮ = 800
  - AKCE = "Kontrola" (systém upozorní, ale bude čekat na schválení)
```

---

## 3. PROCES REGISTRACE - AUTOMATICKÁ KONTROLA

### 3.1 Workflow
```
1. Prodej zadá ADRESU a vybere PRODUKTOVÝ MIX (krabičky)
   ↓
2. Systém geocoduje adresu → GPS (lat, lng)
   ↓
3. Ověří, která obec se nachází v poloměru 5 km
   ↓
4. Vyhledá v DB: "Všechny aktivní prodeje v TÉŽE obci"
   ↓
5a. MALÁ OBEC (≤3000): Pokud existuje aktivní prodej → ODMÍTNUTÍ
   ↓
5b. VELKÉ MĚSTO (>3000): Pokud existuje prodej v < 800 m → UPOZORNĚNÍ
   ↓
6. Pokud PASS: Registrace pokračuje, prodej je označen jako "čekající"
   Pokud FAIL: Zobrazit uživatelsky příjemnou hlášku (viz. kap. 4)
```

### 3.2 Ověření vzdálenosti (GPS)
```
FUNKCE: calculate_distance(lat1, lng1, lat2, lng2)
METODA: Haversine formula (vzdálenost v metrech po zemském povrchu)
KNIHOVNA: geopy (Python) nebo turf.js (Node.js)

VÝSTUP: 
  - Vzdálenost v metrech
  - Booleovská hodnota: can_register (true/false)
```

### 3.3 Databáze konfliktu
```sql
CREATE TABLE locality_conflict_log (
  id INT PRIMARY KEY AUTO_INCREMENT,
  conflicting_store_id INT (nová prodej),
  existing_store_id INT (stávající prodej),
  conflict_type VARCHAR (SMALL_TOWN | DISTANCE_TOO_CLOSE),
  distance_meters INT,
  municipality VARCHAR,
  population INT,
  timestamp DATETIME,
  status VARCHAR (BLOCKED | WARNING | RESOLVED)
);
```

---

## 4. UŽIVATELSKÁ ZPRÁVA PRO PRODEJ (Případ: Lokalita obsazená)

### 4.1 MALÁ OBEC (≤ 3000 obyv.)

**NADPIS:**
```
🚫 Lokalita je již v naší síti zastoupena
```

**TEXT:**
```
Děkujeme za váš zájem! V obci [NÁZEV OBCE] 
([POČET OBYVATEL] obyvatel) jsme se zavázali 
ochraňovat exkluzivitu našich partnerů a máme 
zde již aktivního prodejce.

Toto je naše zásada: V JEDNÉ MALÉ OBCI = JEDEN MODUL.
Chceme, aby naší produkty poznali správně a ne 
aby si konkurovali prodejci vedle sebe.

**Máte 3 možnosti:**

1️⃣ Podívejte se na **DOSTUPNÉ OBCE** (seznam obsazených + volných)
2️⃣ Zaregistrujte se v **SOUSEDNÍ OBCI** (bude 800m od vás)
3️⃣ **ČEKEJTE V KLUBU**: Zůstáváte v naší databázi, 
   a pokud se stávající prodejce zřekne licence, 
   vy budete první na řadě! (E-mail notifikace)

→ [TLAČÍTKO: Podívat se na dostupné obce]
→ [TLAČÍTKO: Zůstat v čekacím seznamu]
```

### 4.2 VELKÉ MĚSTO (> 3000 obyv.) - UPOZORNĚNÍ NA BLÍZKOST

**NADPIS:**
```
⚠️ V blízkosti je již jeden prodejce naší sítě
```

**TEXT:**
```
V městě [NÁZEV] jsme identifikovali jednoho partnera 
pouhých [VZDÁLENOST] metrů od vaší adresy.

Není to překážka! Máme zde prostor pro více modulů, 
ale s MINIMÁLNÍM ODSTUPEM 800 METRŮ.

**SITUACE:**
• Váš prodej: [VAŠE ADRESA]
• Stávající prodej: [ADRESA KONKURENTA] 
• Vzdálenost: [XXX] metrů
• Doporučená min. vzdálenost: 800 metrů

→ Chcete si vybrat **JINOU ADRESU** v téže lokalitě?
   (Navrhneme vám alternativy v mapě)

→ Chcete **POKRAČOVAT** s touto adresou?
   (Je to méně ideální, ale pokud to zvládnete,
   spojíme vás s vedením sítě pro individuální schválení)

→ [TLAČÍTKO: Změnit adresu / Zobrazit alternativy]
→ [TLAČÍTKO: Pokračovat s touto adresou (req. schválení)]
```

---

## 5. TECHNICKÉ IMPLEMENTACE (Backend)

### 5.1 API Endpoint pro validaci
```
POST /api/v1/validate-location
Content-Type: application/json

{
  "address": "Masarykova 15, 753 01 Přerov",
  "product_mix_id": "MIX_ABC123",
  "network_id": "PROVECTOR" // nebo "MO_PARTNER"
}

RESPONSE (Success):
{
  "valid": true,
  "municipality": "Přerov",
  "population": 44500,
  "lat": 49.4556,
  "lng": 17.4522,
  "nearest_competitor_distance": null
}

RESPONSE (Conflict):
{
  "valid": false,
  "conflict_type": "SMALL_TOWN_EXCLUSIVE",
  "message": "V obci [Drobovice] (1250 ob.) je již aktivní prodej.",
  "existing_store": {
    "id": 5847,
    "address": "Nám. Svobody 3, 753 45 Drobovice",
    "owner_email": "partner@drobovice.cz",
    "status": "ACTIVE"
  }
}

RESPONSE (Warning):
{
  "valid": true,
  "warning": true,
  "warning_type": "DISTANCE_CLOSE",
  "message": "Blízko je konkurent",
  "nearest_competitor": {
    "address": "Olšavská 8, Přerov",
    "distance": 650,
    "requires_approval": true
  }
}
```

### 5.2 Cron Job - Daily Sync obcí
```
# Jednou za 24 hodin stáhnout aktualizovanou DB obcí z ČSÚ
# Aktualizovat populaci (demografie se mění)
# Vyčistit duplicity a překlepy v adresách
```

### 5.3 Admin Panel - Spravování konfliktů
- Přehled všech registrací s "WARNING" nebo "BLOCKED" stavem
- Možnost manuálního schválení u velkých měst
- Export reportu: "Obsazenost trhu po okresech"

---

## 6. SEZNAM OBCÍ & VOLNÉ LOKALITY (Pro prodeje)

Aplikace bude mít veřejný přehled:
```
DOSTUPNÉ OBCE:
[ ] Drobovice (1200 ob.) - VOLNÁ
[ ] Lipník nad Bečvou (3100 ob.) - VOLNÉ (3 moduly)
[ ] Šumperk (26000 ob.) - VOLNÉ (5+ modulů)

OBSAZENÉ OBCE:
[✓] Přerov (44500 ob.) - 2 moduly
[✓] Hranice (8900 ob.) - 1 modul
```

---

## 7. MĚŘENÍ ÚSPĚCHU

- **Metriky**:
  - % schválených registrací bez upozornění
  - Průměrná vzdálenost mezi moduly v městech
  - Čas odpovědi na registrační žádost (< 5 minut)
  - Satisfaction prodejců: "Cítím se chráněný exkluzivitou" (NPS)

---

## 8. TIMELINE

- **Week 1**: Sběr & import DB obcí ČR
- **Week 2**: Dev geocodování & Haversine kalkulace
- **Week 3**: UI pro varování & hlášky
- **Week 4**: QA & pilotování s PROVECTOR (10-20 registrací)
