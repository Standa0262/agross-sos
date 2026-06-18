# PROCES: Samoobslužná Rotace Ležáků & Vratka/Výměna

## OVERVIEW - "Garance Bestseller" Program

Slibujeme:
```
❌ Po 3 měsících neprodejné zboží = ZDARMA VÝMĚNA za bestsellery
✓ Bez administrativa
✓ Bez emaily/volání
✓ Bez odesílání do skladu
✓ Přímo v aplikaci → Objednávka
```

---

## 1. PODMÍNKY AKTIVACE GARANCE

### 1.1 Aby prodej mohl vrátit/vyměnit, musí splnit:

```
POVINNÉ:
□ Stojan je umístěn "U POKLADNY" nebo "NA VIDITELNÉM MÍSTĚ"
  (Fotografie povinná – viz. kap. 2)
□ Prodej má AKTIVNÍ SMLOUVU (minimálně 1 měsíc v síti)
□ Zboží je neprodejné = NULA kusy prodáno za 3 měsíce
  (Ověřeno z objednávek v aplikaci)
□ Minimálně 20 ks k vrácení (hromadná výměna, ne jednotlivosti)

ČASOVÉ OKNO:
→ Výměna je povolena od MĚSÍCE 4 (3 měsíce ~ cca den 91+)
→ Výměna je možná JEDNOU ZA 6 MĚSÍCŮ (na prodej)
→ Bez limitace na počet návratů pokud mění assortiment
```

### 1.2 Definice "Neprodejné zboží"

```
= SKU, který má v systému "0 ks prodáno" za posledních 90 dnů
  a fyzicky je ještě na stojanu

NE: Rozbitý/poškozený materiál (to je jiný program - scrap)
NE: Zboží starší 3 měsíce (pokud byl někdy prodán)
NE: Zboží kterého se zbavili a teď si ho vyměňují
```

---

## 2. WORKFLOW: Jak prodej iniciuje výměnu

### 2.1 UI v aplikaci

**KROK 1: Přihlášení do aplikace**
```
Domovská obrazovka → Tlačítko "MOJE OBJEDNÁVKY"
```

**KROK 2: Nová sekce – "VRATKA & VÝMĚNA"**
```
┌─────────────────────────────────┐
│ 📥 VRATKA & VÝMĚNA              │
├─────────────────────────────────┤
│ ✅ Máte nárok na výměnu?         │
│ 🔍 Zkontrolujeme vaše zboží      │
│                                 │
│ [TLAČÍTKO: Zahájit výměnu]      │
└─────────────────────────────────┘
```

**KROK 3: Ověření fotografie**
```
Aplikace poprosí:
"Prosím, vyfotografujte stojan u POKLADNY (nebo na viditelném místě)
aby jsme ověřili, že je správně umístěný."

[📷 FOTOGRAFIE]

Upozornění: Bez fotografie nemůžete pokračovat.
(Umělá inteligence ověří: Je to opravdu prodejnový prostor?
 Obsahuje to nákupčí? Je to v místě s vysokou viditelností?)
```

**KROK 4: Výběr neprodejného zboží**
```
Systém zobrazí:
"Toto zboží jste nikdy neproběli za 90 dnů:"

☑ PřF - Kulaté nůžky (5 ks) - 44,90 Kč
☑ PřF - Náplast sada (3 ks) - 44,90 Kč
☑ PřF - Gáza sterilní (8 ks) - 95,90 Kč
─────────────────────────
TOTAL K VRÁCENÍ: 16 ks
SUMA: 1 087,60 Kč (= kredit pro novou objednávku)

[TLAČÍTKO: Pokračovat - Vybrat náhradu]
```

**KROK 5: Výběr bestseller produktů (Náhrada)**
```
Systém nabídne:
"Jaké produkty vám doporučujeme místo toho?"

Bestsellery v ČR (za poslední měsíc):
☐ Náplast klasik sada 2-4 (TOP 1)
☐ Obličejové kapesníčky (TOP 2)
☐ Dezinfekce na ruce 0,5L (TOP 3)

Máte KREDIT: 1 087,60 Kč → vyberte si produkty v součtu
```

**KROK 6: Potvrzení a finalizace**
```
SHRNUTÍ OBJEDNÁVKY:
────────────────────
VRATKA:
  - Kulaté nůžky (5 ks) → Kredit 224,50 Kč
  - Náplast sada (3 ks) → Kredit 134,70 Kč
  - Gáza sterilní (8 ks) → Kredit 766,40 Kč
────────────────────
NOVÁ OBJEDNÁVKA (z kreditu):
  - Náplast klasik (10 ks) → 449,00 Kč
  - Dezinfekce (2 x 0,5L) → 638,60 Kč
────────────────────
ZŮSTALO NA KREDITU: 0,00 Kč

[TLAČÍTKO: Potvrzit a odeslat objednávku]
```

---

## 3. INTEGRACI DO OBJEDNÁVKOVÉHO EMAILU / WhatsApp

### 3.1 WhatsApp notifikace (Template)

```
Ahoj [JMÉNO]! 👋

Vaše objednávka ze dne [DATUM] je PŘIPRAVENA:

📦 VRATKA (zdarma výměna):
   - Kulaté nůžky (5 ks)
   - Náplast sada (3 ks)
   - Gáza sterilní (8 ks)
   ✅ Kredit na nákup: 1 087,60 Kč

📦 NOVÝ NÁKUP (z kreditu):
   - Náplast klasik (10 ks)
   - Dezinfekce (2 x 0,5L)

💰 Cena bez vratky: 1 087,60 Kč
🆓 Cena s VRÁTKOU: 0,00 Kč (ZDARMA!)

Děkujeme za vrácení neprodejného zboží!
Doručení během 3 pracovních dnů.

[POTVRZENÍ V APLIKACI] [CANCELOVAT]
```

### 3.2 Email notifikace (Format s více detaily)

```
Subject: ✅ Vaše objednávka s VRÁTKOU je potvrzena

Objednávka č.: ORD-20250618-7854
Prodej: [Název prodejny]
Datum: 18. června 2025

═════════════════════════════════════
📥 VRÁCENÉ ZBOŽÍ (Garance Bestseller Program)
═════════════════════════════════════

Všechny tyto produkty nepředstavovaly prodej za 90 dnů 
a vrací se ZDARMA za nový sortiment:

SKU: PF001 | Kulaté nůžky | 5 ks × 44,90 Kč = 224,50 Kč
SKU: PF012 | Náplast sada | 3 ks × 44,90 Kč = 134,70 Kč
SKU: PF045 | Gáza sterilní | 8 ks × 95,90 Kč = 766,40 Kč

─────────────────────────────────────
VRÁCENO CELKEM: 16 ks | KREDIT: 1 087,60 Kč

═════════════════════════════════════
📦 NOVÁ OBJEDNÁVKA (financovaná z kreditu)
═════════════════════════════════════

SKU: PF011 | Náplast klasik sada | 10 ks × 44,90 Kč = 449,00 Kč
SKU: PF089 | Dezinfekce 0,5L | 2 ks × 319,30 Kč = 638,60 Kč

─────────────────────────────────────
NOVÁ OBJEDNÁVKA CELKEM: 12 ks | SUMA: 1 087,60 Kč

═════════════════════════════════════
💰 FINANČNĚ
═════════════════════════════════════

Původní cena (bez vrátky): 1 087,60 Kč
Kredit z vrátky: -1 087,60 Kč
K ÚHRADĚ: 0,00 Kč ✅ ZDARMA

═════════════════════════════════════
🚚 LOGISTIKA
═════════════════════════════════════

Doručení nového sortimentu: 3 pracovní dny
Vyzvednutí vrácaného zboží: Bude dojednáno s kurýrem

Máte dotazy? Odpovězte na tento email nebo zavolejte:
+420 123 456 789 (CZ support)
+420 987 654 321 (EN/VN support)

Děkujeme za partnerství! 🙏
A-GROSS SOS Team
```

---

## 4. LIMITY A OCHRANA PROTI ZNEUŽITÍ

### 4.1 Maximální frekvence výměny

```
PER PRODEJ:
  • Výměna 1× za 6 měsíců (= pokud vraťte neprodejné, čekáte 6 měsíců)
  • MIMO: Pokud se jedná o sortiment-refresh (vedení schválí),
    lze to udělat 2× ročně

DETEKCE ZNEUŽITÍ:
  • Pokud prodej vraacuje stejné SKU podruhé v řadě → alarm
  • Pokud prodej vrací zboží, které PREDTÍM prodal → flag pro audit
  • Systém sleduje vzorce chování (anomaly detection)
```

### 4.2 Minimální objem k vrácení

```
MIN. 20 ks K VRÁCENÍ
  → Není možné vrátit "jednu nit" nebo "5 ks"
  → Zabraňuje administrativnímu peklu
  → Pobízí prodejce ke strategickému přemýšlení
  
VÝJIMKA: Pokud je prodej NOVÝ (< 30 dnů) a zřejmě špatně 
         vybral assortiment → vedení může schválit nižší objem
```

### 4.3 Expirace kreditu

```
Kredit z vrátky platí POUZE JEDNOU
 → Pokud prodej nevybere náhradu do 14 dnů, kredit vypršel
 → Nový návrh: Automatické doporučení bestselleru (neutrální)
```

---

## 5. FOTOGRAFIE POVINNĚ - "Proof of Placement"

### 5.1 Proč fotografie?

```
Problém: Prodejce stojanu schovává do mrtvého koutu,
         nikdo ho nevidí → nula prodejů
         Ale pak říká: "Zboží se neprodávalo, chci si ho vyměnit"

Řešení: Fotografie = Garance, že stojan byl skutečně viditelný
```

### 5.2 Technické ověření fotografie

```
CHECKLIST - co aplikace kontroluje na fotografii:
□ Jedná se o prodejní prostor (jsou tam nákupčí, regály, pokladna)?
□ Je stojan viditelný (u pokladny / na hlavní cestě)?
□ Je na fotografii vidět NÁŠ STOJAN (A-GROSS branding)?
□ Je fotografie v poslední "věrohodné" poloze (datum metadata)?

TECHNOLOGIE: AI vision (computer vision API)
  - Google Cloud Vision API
  - AWS Rekognition
  - Lokální ML model (offline, bez datové stopy)

POKUD FOTOGRAFIE SELŽE:
  → Aplikace ji zamítne a poprosí o novou
  → Max. 3 pokusy za sezónu
  → Pokud je 3. pokus zamítnut → prodej má zablokován program na 3 měsíce
```

### 5.3 Uživatelský pokyn

```
📸 FOTOGRAFIE POVINNĚ

Prosím, vyfotografujte stojan takto:
✓ STOJAN musí být viditelný
✓ Musí to být z prodejního prostoru (nikoliv ze skladu!)
✓ Ideálně s dalším "kontextem" (pokladna, produkty, lid)
✓ Jasná fotografie (osvětlení OK)

SPRÁVNĚ:
[Fotka: Stojan u pokladny, viditelný, s zákazníky]

ŠPATNĚ:
[Fotka: Stojan schovaný za dveřmi, v mrtvém koutě]

Máte fotografii? Pošlete ji a ověříme ji během 5 minut.
```

---

## 6. ADMIN PANEL - Monitorování Vrácení

### 6.1 Dashboard pro vedení

```
REPORTS:
 • Počet vratek per měsíc (trend)
 • % prodejen, které vrací vs. nikdy nevrací
 • Top 10 nejčastěji vracených SKU (indikator špatného produktu?)
 • Top 10 nejvíce objednaných produktů po vrácení (bestsellery)
 • Počet zamítnutých vrácení (fotografie, limit, fraud)

ALERTS:
 • Pokud prodej vrací > 1× za 3 měsíce → zvaž pohovor
 • Pokud vrací + opět objednávají STEJNÝ produkt → vyšetř
 • Pokud fotografie jsou suspecious → flag pro ruční audit
```

---

## 7. MESSAGING / KOMUNIKACE S PRODEJNAMI

### 7.1 Při spuštění programu (Email)

```
Subject: 🎁 GARANCE BESTSELLER: Výměňujeme neprodejné zboží ZDARMA!

Dobrý den,

Chceme vám dát jistotu: Pokud se nějaký sortiment v A-GROSS SOS neujme,
nemusíte se vám ho zbývat koukat v pultě 3 měsíce.

NOVÝ PROGRAM: GARANCE BESTSELLER
→ Pokud zboží nemáte prodejní za 90 dnů, zavolejte nám
→ Vrátíme vám ho ZDARMA a nahradíme bestsellery
→ Bez otázek, bez administrativy
→ Přímo v aplikaci

Vše zvládnete během 5 minut. Stačí fotografie stojanu a hotovo.

Detaily: [LINK DO APLIKACE]
Otázky? Zavolejte: +420 123 456 789

S důvěrou,
A-GROSS SOS Team
```

### 7.2 Při iniciaci vrácení (SMS)

```
Ahoj! Věděli jste, že máte právo na VRÁCENÍ neprodejného zboží?
Máte 3 měsíce bez prodejů? → Vyměníme vám zdarma!
Zahajte v aplikaci:  [DEEP LINK] 📱
```

---

## 8. TECHNICKÉ ZADÁNÍ PRO DEVELOPERY

### 8.1 Backend

```sql
-- Nová tabulka pro vratky
CREATE TABLE returns (
  id INT PRIMARY KEY AUTO_INCREMENT,
  store_id INT NOT NULL,
  return_date DATETIME DEFAULT NOW(),
  status ENUM ('PENDING', 'APPROVED', 'REJECTED', 'SHIPPED'),
  items JSON, -- [{sku: 'PF001', qty: 5, price: 44.90}, ...]
  credit_amount DECIMAL(10,2),
  photo_url VARCHAR(500),
  photo_verified BOOLEAN DEFAULT FALSE,
  next_return_eligible_date DATE,
  notes TEXT
);

-- Sledování creditu
CREATE TABLE return_credits (
  id INT PRIMARY KEY AUTO_INCREMENT,
  store_id INT NOT NULL,
  credit_amount DECIMAL(10,2),
  expiry_date DATE,
  used_date DATETIME NULL,
  order_id INT FOREIGN KEY
);

-- AI verification logs
CREATE TABLE photo_verifications (
  id INT PRIMARY KEY AUTO_INCREMENT,
  photo_url VARCHAR(500),
  verified BOOLEAN,
  confidence DECIMAL(3,2),
  ai_model VARCHAR(50),
  verification_date DATETIME
);
```

### 8.2 API Endpoints

```
POST /api/v1/returns/initiate
  Input: { store_id, photo_file }
  Output: { return_id, detected_items, credit_amount }

POST /api/v1/returns/{return_id}/verify-photo
  Input: { photo_file }
  Output: { verified: bool, confidence: %, message }

POST /api/v1/returns/{return_id}/confirm
  Input: { items_to_return: [...], replacement_items: [...] }
  Output: { order_id, credit_used, shipping_label }

GET /api/v1/returns/history
  Output: [{ return_id, date, status, items, credit, ... }]
```

---

## 9. TIMELINE

- **Week 1**: Design UI / Mockupy
- **Week 2**: Photo AI integration (Google Vision / AWS Rekognition)
- **Week 3**: Backend development (DB + API)
- **Week 4**: Frontend integration
- **Week 5**: QA + Pilot (10 prodejen)
- **Week 6**: Full rollout PROVECTOR + MO_PARTNER

---

## 10. OČEKÁVANÝ DOPAD

```
✓ Zvýšená důvěra prodejců (vědí, že nejsou sami s neprodejným zbožím)
✓ Vyšší vstupní motivace (menší riziko při prvním nákupu)
✓ Lepší data o tom, který sortiment se ujímá/ne
✓ Opportunity cross-sell (nový bestseller = nová příležitost)
✓ Retention: "V téhle síti mám záruky" = lepší LTV partnera
```
