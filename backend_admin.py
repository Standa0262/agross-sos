#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A-GROSS SOS – Admin Backend
Měsíční reporting pro sítě a správa komisí

Instalace:
    pip install flask flask-cors psycopg2-binary python-dateutil

Spuštění:
    DATABASE_URL=postgresql://... ADMIN_API_KEY=... STORE_APP_KEY=... python backend_admin.py

Autentizace (hlavička Authorization: Bearer <klíč>):
    ADMIN_API_KEY – admin panel (GET /api/orders, GET /api/stores, reporty, mazání, notifikace)
    STORE_APP_KEY – appka prodejen (orders/sync, stores/sync, check-exclusivity)
    bez klíče     – /health, /api/health, /api/catalogs/sync, /api/stores/public,
                    /api/notifications/active

API Endpoints:
    POST /api/db/init – Vytvoří databázové tabulky (pokud neexistují) [admin]
    POST /api/orders/sync – Příjem offline objednávek (ukládá do DB) [store]
    GET /api/orders – Objednávky (filtr store_id, from_date, to_date, network) [admin]
    POST /api/stores/sync – Uložení/aktualizace prodejny [store]
    GET /api/stores – Všechny prodejny, včetně PII [admin]
    GET /api/stores/public – Prodejny bez PII (jméno/řetězec/GPS/město) [public]
    GET /api/reports/monthly – Měsíční report pro síť [admin]
    POST /api/registrations/verify – Ověření jméno+PIN, rate limited [public]
    POST /api/catalog/prices – NC ceny katalogu pro přihlášenou prodejnu
        (jméno+PIN, stejné ověření a rate limit jako verify) [public]
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import hmac
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor, Json

app = Flask(__name__)

ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        'ALLOWED_ORIGINS', 'https://standa0262.github.io,null'
    ).split(',') if o.strip()
]
CORS(app, origins=ALLOWED_ORIGINS)

# ═════════════════════════════════════════════════════════════════════
# KONFIGURACE
# ═════════════════════════════════════════════════════════════════════

COMMISSION_RATES = {
    'Provector': 0.05,  # 5%
    'MO Partner': 0.05, # 5%
    # Přidat další sítě dle dohody
}

# ═════════════════════════════════════════════════════════════════════
# AUTORITATIVNÍ CENÍK (server-side zdroj pravdy pro ceny)
# ═════════════════════════════════════════════════════════════════════
# MUSÍ SE RUČNĚ SYNCHRONIZOVAT S PRODUCTS V A_GROSS_SOS.html PŘI KAŽDÉ
# ZMĚNĚ CENÍKU! Klient (appka prodejen) posílá jen kód a množství - nc/moc
# se VŽDY dopočítávají odsud, hodnoty poslané klientem se ignorují (viz
# recompute_order_pricing / endpoint /api/catalog/prices).
#
# ncCelofan: None = produkt v celofánovém balení není, použije se ncKrabicka
# i pro sítě s packaging:'celofan'.
PRICE_TABLE = {
    'S276921':   {'ncKrabicka': 39.44, 'ncCelofan': 37.44, 'moc': 95.9},
    'S276922':   {'ncKrabicka': 31.03, 'ncCelofan': 29.03, 'moc': 74.9},
    'S80415':    {'ncKrabicka': 35.78, 'ncCelofan': 33.78, 'moc': 86.9},
    'S80398':    {'ncKrabicka': 22.9,  'ncCelofan': 26.40, 'moc': 51.9},
    'S660085':   {'ncKrabicka': 28.49, 'ncCelofan': 26.49, 'moc': 69.0},
    'S80412':    {'ncKrabicka': 23.32, 'ncCelofan': 21.32, 'moc': 56.9},
    'S235':      {'ncKrabicka': 21.63, 'ncCelofan': 19.63, 'moc': 54.9},
    'S199':      {'ncKrabicka': 10.4,  'ncCelofan': 8.40,  'moc': 25.9},
    'S830040':   {'ncKrabicka': 27.48, 'ncCelofan': 25.48, 'moc': 59.0},
    'S830462':   {'ncKrabicka': 32.5,  'ncCelofan': 30.50, 'moc': 78.9},
    'S830095':   {'ncKrabicka': 32.5,  'ncCelofan': 30.50, 'moc': 78.9},
    'S700808':   {'ncKrabicka': 14.4,  'ncCelofan': 12.40, 'moc': 34.9},
    'S224004-1': {'ncKrabicka': 18.76, 'ncCelofan': 16.76, 'moc': 45.9},
    'S224004':   {'ncKrabicka': 18.76, 'ncCelofan': 16.76, 'moc': 45.9},
    'S224004-3': {'ncKrabicka': 18.76, 'ncCelofan': 16.76, 'moc': 45.4},
    'S314':      {'ncKrabicka': 28.18, 'ncCelofan': 26.18, 'moc': 68.2},
    'S661620':   {'ncKrabicka': 31.06, 'ncCelofan': 29.06, 'moc': 74.9},
    'S76':       {'ncKrabicka': 13.86, 'ncCelofan': 11.86, 'moc': 33.9},
    'S100':      {'ncKrabicka': 18.34, 'ncCelofan': 16.34, 'moc': 44.9},
    'S1020':     {'ncKrabicka': 10.4,  'ncCelofan': 11.90, 'moc': 25.17},
    'S1075':     {'ncKrabicka': 18.96, 'ncCelofan': 16.96, 'moc': 45.9},
    'S5080':     {'ncKrabicka': 19.8,  'ncCelofan': 17.80, 'moc': 47.9},
    'S342-1':    {'ncKrabicka': 12.9,  'ncCelofan': None,  'moc': 31.22},
    'S342-2':    {'ncKrabicka': 12.9,  'ncCelofan': None,  'moc': 31.22},
    'S304-1':    {'ncKrabicka': 13.9,  'ncCelofan': None,  'moc': 33.64},
    'S304-2':    {'ncKrabicka': 13.9,  'ncCelofan': None,  'moc': 33.64},
    'S668-1':    {'ncKrabicka': 14.9,  'ncCelofan': None,  'moc': 36.06},
    'S668-2':    {'ncKrabicka': 14.9,  'ncCelofan': None,  'moc': 36.06},
    'S559':      {'ncKrabicka': 7.05,  'ncCelofan': None,  'moc': 17.06},
    'S344-1':    {'ncKrabicka': 19.6,  'ncCelofan': 23.10, 'moc': 47.9},
    'S344-2':    {'ncKrabicka': 19.6,  'ncCelofan': 23.10, 'moc': 47.9},
    'S344-3':    {'ncKrabicka': 19.6,  'ncCelofan': 23.10, 'moc': 47.9},
    'S9901':     {'ncKrabicka': 16.4,  'ncCelofan': 14.40, 'moc': 39.9},
    'S9902':     {'ncKrabicka': 17.5,  'ncCelofan': 15.50, 'moc': 42.9},
    'S9903':     {'ncKrabicka': 16.4,  'ncCelofan': 14.40, 'moc': 39.9},
    'S9904':     {'ncKrabicka': 17.5,  'ncCelofan': 15.50, 'moc': 42.9},
    'S9905':     {'ncKrabicka': 17.4,  'ncCelofan': 15.40, 'moc': 42.2},
    'S9906':     {'ncKrabicka': 18.5,  'ncCelofan': 16.50, 'moc': 44.9},
    'S80394':    {'ncKrabicka': 17.67, 'ncCelofan': 21.17, 'moc': 42.9},
    'S80399':    {'ncKrabicka': 22.08, 'ncCelofan': 25.58, 'moc': 53.9},
    'S80400':    {'ncKrabicka': 19.58, 'ncCelofan': 23.08, 'moc': 47.9},
}

# MUSÍ SE RUČNĚ SYNCHRONIZOVAT S NETWORKS V A_GROSS_SOS.html PŘI KAŽDÉ
# ZMĚNĚ! Zrcadlí jen pole packaging (typ balení určuje, jestli se použije
# ncKrabicka nebo ncCelofan). key = klíč sítě, name/shortName = stejnojmenná
# pole NETWORKS[key] - používají se k dohledání sítě podle textového pole
# stores.chain (viz get_packaging_for_chain).
#
# DŮLEŽITÉ: appka při registraci pod síťovým odkazem (?sit=...) ukládá do
# stores.chain rovnou celé NETWORKS[key].name (window._lockedChain = net.name
# v A_GROSS_SOS.html), ne shortName - proto se matchuje primárně na name.
NETWORKS_PACKAGING = {
    'javor':         {'name': 'Obchodní aliance JAVOR',        'shortName': 'JAVOR',          'packaging': None},
    'mopartner':     {'name': 'MO Partner',                    'shortName': 'MO PARTNER',     'packaging': None},
    'bala':          {'name': 'BALA',                          'shortName': 'BALA',           'packaging': None},
    'coophb':        {'name': 'COOP Havlíčkův Brod',           'shortName': 'COOP HB',        'packaging': 'celofan'},
    'jednotaostroh': {'name': 'COOP Jednota Uherský Ostroh',   'shortName': 'JEDNOTA OSTROH', 'packaging': 'celofan'},
}


def get_packaging_for_chain(chain):
    """
    Dohledá typ balení (celofán/krabička) podle textového pole stores.chain
    (resp. u registrací obdobného zdroje). Zkouší postupně: klíč sítě, přesnou
    shodu s name (to appka reálně ukládá u síťově uzamčených prodejen), a jako
    fallback podřetězec shortName (pro ručně vyplněný chain). Když se síť
    nedá určit, výchozí je krabička (None) - stejné chování jako appka bez
    ?sit= parametru.
    """
    if not chain:
        return None
    chain_lower = chain.strip().lower()
    for key, cfg in NETWORKS_PACKAGING.items():
        if chain_lower == key.lower() or chain_lower == cfg['name'].lower():
            return cfg['packaging']
    for key, cfg in NETWORKS_PACKAGING.items():
        if cfg['shortName'].lower() in chain_lower:
            return cfg['packaging']
    return None


def recompute_order_pricing(items, packaging):
    """
    Autoritativní přepočet nc/marze/moc z PRICE_TABLE - hodnoty poslané
    klientem se IGNORUJÍ (appka je posílá jen pro čitelnost JSONu, ne jako
    zdroj pravdy). Vrací (přepočtené položky, nc, marze, moc).
    Raises ValueError(kod) když položka odkazuje na neexistující kód.
    """
    total_nc = 0.0
    total_moc = 0.0
    recomputed = []
    for it in (items or []):
        kod = str(it.get('kod', '')).strip()
        price = PRICE_TABLE.get(kod)
        if not price:
            raise ValueError(kod)
        try:
            qty = float(it.get('qty', 0) or 0)
        except (TypeError, ValueError):
            qty = 0
        unit_nc = price['ncCelofan'] if (packaging == 'celofan' and price['ncCelofan'] is not None) else price['ncKrabicka']
        unit_moc = price['moc']
        total_nc += unit_nc * qty
        total_moc += unit_moc * qty
        recomputed.append({**it, 'nc': unit_nc, 'moc': unit_moc})
    return recomputed, round(total_nc, 2), round(total_moc - total_nc, 2), round(total_moc, 2)

# ═════════════════════════════════════════════════════════════════════
# AUTENTIZACE (Bearer token v hlavičce Authorization)
# ═════════════════════════════════════════════════════════════════════
# ADMIN_API_KEY – admin panel (AGROSS_SOS_ADMIN.html), zadává se ručně
#                 do prohlížeče, NIKDY není součástí zdrojáku ani gitu.
# STORE_APP_KEY – appka pro prodejny (A_GROSS_SOS.html / _VI.html), je
#                 natvrdo v klientském JS – nejde o skutečné tajemství,
#                 jen o clonu proti masovému/náhodnému scanování.
# Obě se nastavují VÝHRADNĚ jako env proměnné (Render → Settings → Environment).

ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY')
STORE_APP_KEY = os.environ.get('STORE_APP_KEY')


def _key_matches(expected):
    if not expected:
        return False
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return False
    return hmac.compare_digest(auth[7:], expected)


def require_admin_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not _key_matches(ADMIN_API_KEY):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapper


def require_store_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not _key_matches(STORE_APP_KEY):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapper

# ═════════════════════════════════════════════════════════════════════
# RATE LIMITING (ochrana ověřování jméno+PIN proti brute-force)
# ═════════════════════════════════════════════════════════════════════
# Jednoduchý in-memory limiter klíčovaný podle (name, IP) - pro tuhle appku
# (jeden Render web dyno, malý provoz) dostatečné. POZOR: stav se ztrácí při
# restartu procesu a nesdílí se mezi více workery/instancemi - pokud by appka
# časem běžela na více instancích, je potřeba přejít na sdílené úložiště
# (Redis, nebo tabulka v Postgresu).
#
# Sdílí ji /api/registrations/verify i /api/catalog/prices - obě ověřují
# stejnou dvojici name+pin, takže mají sdílet i limit pokusů.
_rate_limit_attempts = defaultdict(list)  # (name, ip) -> [timestamp, ...]
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minut


def _client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


def check_rate_limit(name):
    """
    Zaznamená pokus o ověření pro (name, IP) volajícího a vrátí True, pokud
    je v posledních RATE_LIMIT_WINDOW_SECONDS pod limitem RATE_LIMIT_MAX_ATTEMPTS
    pokusů (požadavek je povolen). Vrátí False, pokud byl limit překročen -
    volající by měl odpovědět 429 a pokus dál neověřovat.
    """
    key = ((name or '').strip().lower(), _client_ip())
    now = time.time()
    attempts = _rate_limit_attempts[key]
    attempts[:] = [t for t in attempts if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(attempts) >= RATE_LIMIT_MAX_ATTEMPTS:
        return False
    attempts.append(now)
    return True

# ═════════════════════════════════════════════════════════════════════
# DATABÁZE (PostgreSQL – Neon.tech)
# ═════════════════════════════════════════════════════════════════════
# DATABASE_URL se nastavuje VÝHRADNĚ jako env proměnná (Render → Settings →
# Environment), nikdy napevno v kódu – jde o produkční přístupové údaje.

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL není nastavena (env proměnná).')
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def load_orders():
    """Načíst všechny objednávky z databáze (camelCase klíče pro frontend)."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders ORDER BY date DESC')
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return [
        {
            'id': r['id'],
            'storeId': r['store_id'],
            'storeName': r['store_name'],
            'date': r['date'].isoformat() if r['date'] else None,
            'items': r['items'],
            'nc': float(r['nc']) if r['nc'] is not None else 0,
            'marze': float(r['marze']) if r['marze'] is not None else 0,
            'moc': float(r['moc']) if r['moc'] is not None else 0,
            'delivery': r['delivery'],
            'status': r['status'],
            'hasExchange': r['has_exchange'],
        }
        for r in rows
    ]

# ═════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═════════════════════════════════════════════════════════════════════

@app.route('/api/db/init', methods=['POST'])
@require_admin_key
def db_init():
    """Vytvoří databázové tabulky (pokud ještě neexistují)."""
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS stores (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    chain TEXT,
                    manager TEXT,
                    phone TEXT,
                    address TEXT,
                    ico TEXT,
                    dic TEXT,
                    email TEXT,
                    hours_week TEXT,
                    hours_weekend TEXT,
                    note TEXT,
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    city TEXT,
                    population INTEGER,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            ''')
            # CREATE TABLE IF NOT EXISTS nedoplní sloupce do už existující
            # tabulky – starší nasazení mohly vzniknout před přidáním
            # lat/lon/city/population, proto je doplníme explicitně.
            cur.execute('ALTER TABLE stores ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION')
            cur.execute('ALTER TABLE stores ADD COLUMN IF NOT EXISTS lon DOUBLE PRECISION')
            cur.execute('ALTER TABLE stores ADD COLUMN IF NOT EXISTS city TEXT')
            cur.execute('ALTER TABLE stores ADD COLUMN IF NOT EXISTS population INTEGER')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    store_id TEXT,
                    store_name TEXT,
                    date TIMESTAMPTZ,
                    items JSONB,
                    nc NUMERIC,
                    marze NUMERIC,
                    moc NUMERIC,
                    delivery TEXT,
                    status TEXT,
                    has_exchange BOOLEAN DEFAULT false,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sos_exchanges (
                    id SERIAL PRIMARY KEY,
                    store_id TEXT,
                    old_kod TEXT,
                    new_kod TEXT,
                    date TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    text TEXT,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    active BOOLEAN DEFAULT true
                )
            ''')
            conn.commit()
            cur.close()
        finally:
            conn.close()

        return jsonify({
            'success': True,
            'message': 'Tabulky stores, orders, sos_exchanges, notifications jsou připraveny'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/sync', methods=['POST'])
@require_store_key
def sync_order():
    """
    Příjem objednávky z offline režimu.
    
    Postup:
    1. Přijmout objednávku z mobilní aplikace
    2. Uložit do databáze
    3. Označit jako "synced"
    4. Odeslat potvrzení
    
    JSON struktura (nc/marze/moc jsou zde jen pro čitelnost - server je VŽDY
    přepočítá z PRICE_TABLE podle kódu položky a sítě prodejny; hodnoty
    poslané klientem se ignorují, aby nešlo objednávku podvrhnout cenou;
    storeId/storeName jsou taky jen orientační - server dohledá autoritativní
    prodejnu podle name+pin, viz níž):
    {
        "storeId": "123",
        "storeName": "Coopmark – HCM",
        "items": [
            {"kod": "276921", "nazev": "Kim Organ", "nc": 39.44, "qty": 5},
            ...
        ],
        "nc": 197.20,
        "marze": 281.80,
        "moc": 479.00,
        "date": "2026-06-18T10:30:00Z",
        "status": "new",
        "name": "Koloniál Novák",
        "pin": "1234"
    }
    """
    try:
        order = request.json

        # STORE_APP_KEY (@require_store_key) je záměrně veřejný - je natvrdo
        # v klientském JS appky, takže sám o sobě neprokazuje, že objednávka
        # přišla od konkrétní přihlášené prodejny. Ověř proto navíc name+pin
        # stejně jako /api/registrations/verify a /api/catalog/prices - a se
        # STEJNÝM rate limitem (jinak by šlo tuhle trojici endpointů zkoušet
        # dohromady 3x rychleji než jeden).
        name = (order.get('name') or '').strip()
        pin = (order.get('pin') or '').strip()

        if not check_rate_limit(name):
            return jsonify({'error': 'Příliš mnoho pokusů, zkuste to znovu za pár minut.'}), 429

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM registrations
                WHERE pin = %s AND name = %s AND approved = TRUE
            """, (pin, name))
            reg_row = cur.fetchone()
            cur.close()
        finally:
            conn.close()
        if not reg_row:
            return jsonify({'error': 'Neplatné přihlášení prodejny'}), 401

        # Validace
        if not order.get('items'):
            return jsonify({'error': 'Chybí items'}), 400

        # Nedůvěřuj storeId/storeName, které pošle appka, pro určení, čí je
        # to objednávka - dohledej "pravou" prodejnu server-side podle
        # ověřeného jména (stejný princip jako get_packaging_for_registration).
        store_id, store_name, chain = resolve_authoritative_store(
            name, order.get('storeId'), order.get('storeName')
        )
        if not store_id:
            return jsonify({'error': 'Chybí storeId nebo items'}), 400

        packaging = get_packaging_for_chain(chain)

        # Autoritativní přepočet cen ze serverového PRICE_TABLE. Hodnoty
        # nc/marze/moc poslané klientem se IGNORUJÍ - objednávku jinak šlo
        # podvrhnout libovolnou cenou, protože STORE_APP_KEY je veřejný.
        try:
            items, nc, marze, moc = recompute_order_pricing(order.get('items'), packaging)
        except ValueError as bad_kod:
            return jsonify({'error': f'Neznámý kód produktu v objednávce: {bad_kod}'}), 400

        order_id = str(order.get('id') or f"ORD-{int(datetime.now().timestamp()*1000)}")

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO orders (id, store_id, store_name, date, items, nc, marze, moc, delivery, status, has_exchange)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    store_id = EXCLUDED.store_id,
                    store_name = EXCLUDED.store_name,
                    date = EXCLUDED.date,
                    items = EXCLUDED.items,
                    nc = EXCLUDED.nc,
                    marze = EXCLUDED.marze,
                    moc = EXCLUDED.moc,
                    delivery = EXCLUDED.delivery,
                    status = EXCLUDED.status,
                    has_exchange = EXCLUDED.has_exchange
            ''', (
                order_id,
                store_id,
                store_name,
                order.get('date') or datetime.now().isoformat(),
                Json(items),
                nc,
                marze,
                moc,
                order.get('delivery'),
                order.get('status', 'new'),
                bool(order.get('hasExchange', False)),
            ))
            conn.commit()
            cur.close()
        finally:
            conn.close()

        return jsonify({
            'success': True,
            'message': 'Objednávka přijata',
            'orderId': order_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
@require_admin_key
def get_orders():
    """
    Všechny objednávky v období.
    Query params:
        from_date: YYYY-MM-DD
        to_date: YYYY-MM-DD
        store_id: filtrovat podle cửa hàng
        network: filtrovat podle sítě (Provector, MO Partner)
    """
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        store_id = request.args.get('store_id')
        network = request.args.get('network')
        
        orders = load_orders()
        
        # Filtrovat podle datumu
        if from_date:
            orders = [o for o in orders if o.get('date', '') >= from_date + 'T00:00:00']
        if to_date:
            orders = [o for o in orders if o.get('date', '') <= to_date + 'T23:59:59']
        
        # Filtrovat podle obchodu
        if store_id:
            orders = [o for o in orders if o.get('storeId') == store_id]
        
        # Filtrovat podle sítě
        if network:
            orders = [o for o in orders if network in o.get('storeName', '')]
        
        return jsonify({
            'success': True,
            'count': len(orders),
            'orders': orders
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stores/sync', methods=['POST'])
@require_store_key
def sync_store():
    """
    Uložení/aktualizace prodejny.

    JSON struktura:
    {
        "id": "1781773557752",
        "name": "Coop Třinec",
        "chain": "Coop",
        "manager": "Jana Nováková",
        "phone": "+420 777 100 200",
        "address": "Nádražní 12, 739 61 Třinec",
        "ico": "12345678",
        "dic": "CZ12345678",
        "email": "prodejna@example.cz",
        "hoursWeek": "7:00–19:00",
        "hoursWeekend": "8:00–12:00",
        "note": "Dodávat v úterý"
    }
    """
    try:
        store = request.json

        if not store.get('id') or not store.get('name'):
            return jsonify({'error': 'Chybí id nebo name'}), 400

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO stores (id, name, chain, manager, phone, address, ico, dic, email, hours_week, hours_weekend, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    chain = EXCLUDED.chain,
                    manager = EXCLUDED.manager,
                    phone = EXCLUDED.phone,
                    address = EXCLUDED.address,
                    ico = EXCLUDED.ico,
                    dic = EXCLUDED.dic,
                    email = EXCLUDED.email,
                    hours_week = EXCLUDED.hours_week,
                    hours_weekend = EXCLUDED.hours_weekend,
                    note = EXCLUDED.note
            ''', (
                str(store.get('id')),
                store.get('name'),
                store.get('chain'),
                store.get('manager'),
                store.get('phone'),
                store.get('address'),
                store.get('ico'),
                store.get('dic'),
                store.get('email'),
                store.get('hoursWeek'),
                store.get('hoursWeekend'),
                store.get('note'),
            ))
            conn.commit()
            cur.close()
        finally:
            conn.close()

        return jsonify({
            'success': True,
            'message': 'Prodejna uložena',
            'storeId': str(store.get('id'))
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stores', methods=['GET'])
@require_admin_key
def get_stores():
    """Vrátí všechny prodejny se všemi údaji (PII) – jen pro admin panel."""
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM stores ORDER BY created_at DESC')
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()

        stores = [
            {
                'id': r['id'],
                'name': r['name'],
                'chain': r['chain'],
                'manager': r['manager'],
                'phone': r['phone'],
                'address': r['address'],
                'ico': r['ico'],
                'dic': r['dic'],
                'email': r['email'],
                'hoursWeek': r['hours_week'],
                'hoursWeekend': r['hours_weekend'],
                'note': r['note'],
            }
            for r in rows
        ]

        return jsonify({
            'success': True,
            'count': len(stores),
            'stores': stores
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stores/public', methods=['GET'])
def get_stores_public():
    """Vrátí prodejny bez PII (jméno/řetězec/GPS/město) – appky prodejen."""
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, name, chain, lat, lon, city FROM stores ORDER BY created_at DESC')
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()

        stores = [
            {
                'id': r['id'],
                'name': r['name'],
                'chain': r['chain'],
                'lat': r['lat'],
                'lon': r['lon'],
                'city': r['city'],
            }
            for r in rows
        ]

        return jsonify({
            'success': True,
            'count': len(stores),
            'stores': stores
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/monthly', methods=['GET'])
@require_admin_key
def monthly_report():
    """
    Měsíční report pro síť – podklady pro vyplacení komisí.
    
    Query params:
        network: Název sítě (Provector, MO Partner)
        year: Rok (2026)
        month: Měsíc (1-12)
    
    Vrací:
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
    """
    try:
        network = request.args.get('network')
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        if not network:
            return jsonify({'error': 'Chybí network parameter'}), 400
        
        if network not in COMMISSION_RATES:
            return jsonify({'error': f'Síť {network} není v databázi'}), 404
        
        # Načíst objednávky za období
        orders = load_orders()
        
        # Filtrovat podle sítě a měsíce
        from_date = f"{year}-{month:02d}-01"
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        to_date = f"{next_year}-{next_month:02d}-01"
        
        network_orders = [
            o for o in orders
            if network in o.get('storeName', '') and
               from_date <= o.get('date', '')[:10] < to_date
        ]
        
        # Agregovat po obchodech
        stores_data = defaultdict(lambda: {'orders': 0, 'purchase_total': 0})
        
        for order in network_orders:
            store_name = order.get('storeName')
            stores_data[store_name]['orders'] += 1
            stores_data[store_name]['purchase_total'] += order.get('nc', 0)
        
        # Celkem pro síť
        total_purchase = sum(s['purchase_total'] for s in stores_data.values())
        commission_rate = COMMISSION_RATES.get(network, 0)
        total_commission = total_purchase * commission_rate
        
        # Formát měsíce
        months_cz = [
            'Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen',
            'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'
        ]
        period = f"{months_cz[month-1]} {year}"
        
        return jsonify({
            'success': True,
            'network': network,
            'period': period,
            'total_purchase_value': round(total_purchase, 2),
            'commission_rate': commission_rate,
            'commission_amount': round(total_commission, 2),
            'stores_count': len(stores_data),
            'total_orders': len(network_orders),
            'stores': [
                {
                    'store_name': store_name,
                    'orders_count': data['orders'],
                    'total_purchase': round(data['purchase_total'], 2),
                    'commission': round(data['purchase_total'] * commission_rate, 2)
                }
                for store_name, data in sorted(stores_data.items(), 
                                               key=lambda x: x[1]['purchase_total'], 
                                               reverse=True)
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/monthly/export', methods=['GET'])
@require_admin_key
def export_monthly_report():
    """
    Exportovat měsíční report jako PDF/CSV pro emailing sítím.
    Vyžaduje: ReportLab (PDF) nebo csv modul
    """
    try:
        import csv
        from io import StringIO
        
        network = request.args.get('network')
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        # Načíst report
        report = monthly_report().json
        
        # Generovat CSV
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['A-GROSS SOS', 'Měsíční report'])
        writer.writerow(['Síť:', network])
        writer.writerow(['Období:', report['period']])
        writer.writerow([])
        writer.writerow(['SHRNUTÍ'])
        writer.writerow(['Počet obchodů:', report['stores_count']])
        writer.writerow(['Počet objednávek:', report['total_orders']])
        writer.writerow(['Nákupní ceny celkem:', f"{report['total_purchase_value']} VND"])
        writer.writerow(['Sazba provize:', f"{report['commission_rate']*100}%"])
        writer.writerow(['Provize celkem:', f"{report['commission_amount']} VND"])
        writer.writerow([])
        writer.writerow(['DETAILNĚ PO OBCHODECH'])
        writer.writerow(['Obchod', 'Objednávky', 'Nákup', 'Provize'])
        
        for store in report['stores']:
            writer.writerow([
                store['store_name'],
                store['orders_count'],
                store['total_purchase'],
                store['commission']
            ])
        
        csv_data = output.getvalue()
        
        return jsonify({
            'success': True,
            'csv': csv_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalogs/sync', methods=['GET'])
def sync_catalog():
    """
    Stažení aktualizovaného katalogu (ceny, nové produkty).
    Vrací JSON seznam produktů ve formátu pro aplikaci.
    """
    try:
        # Načíst aktuální ceník
        ceník_soubor = 'cenik_produkty.json'
        
        if os.path.exists(ceník_soubor):
            with open(ceník_soubor, 'r', encoding='utf-8') as f:
                products = json.load(f)
        else:
            # Default catalog
            products = []
        
        return jsonify({
            'success': True,
            'count': len(products),
            'products': products,
            'updated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['POST'])
@require_admin_key
def create_notification():
    try:
        data = request.json
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'Chybí text'}), 400
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE notifications SET active = false")
            cur.execute("INSERT INTO notifications (text, active) VALUES (%s, true)", (text,))
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return jsonify({'success': True, 'message': 'Oznámení uloženo'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/active', methods=['GET'])
def get_active_notification():
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT text FROM notifications WHERE active = true ORDER BY created_at DESC LIMIT 1")
            row = cur.fetchone()
            cur.close()
        finally:
            conn.close()
        if row:
            return jsonify({'success': True, 'text': row['text']}), 200
        return jsonify({'success': True, 'text': None}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/clear', methods=['POST'])
@require_admin_key
def clear_notification():
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE notifications SET active = false")
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return jsonify({'success': True, 'message': 'Oznámení smazáno'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def haversine_km(lat1, lon1, lat2, lon2):
    """Vzdálenost mezi dvěma GPS body v km (Haversine)."""
    import math
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.route('/api/stores/check-exclusivity', methods=['POST'])
@require_store_key
def check_exclusivity():
    """
    Zkontroluje GPS exkluzivitu pro novou prodejnu.

    Pravidla:
    - Obce do 3 000 obyvatel: max. 1 prodejna (kontrola stejné obce dle názvu)
    - Města nad 3 000 obyvatel: min. 800 m mezi prodejnami

    JSON vstup:
    {
        "lat": 49.6778,
        "lon": 18.3461,
        "city": "Třinec",
        "population": 35000,
        "store_id": "optional-id-if-editing"
    }

    Odpověď:
    {
        "allowed": true/false,
        "warning": "text varování nebo null",
        "conflicts": [{"store_name": "...", "distance_m": 450}]
    }
    """
    try:
        data = request.json
        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
        population = int(data.get('population', 0))
        city = (data.get('city') or '').strip().lower()
        exclude_id = str(data.get('store_id') or '')

        if not lat or not lon:
            return jsonify({'allowed': True, 'warning': 'GPS nedostupné – exkluzivita nekontrolována', 'conflicts': []}), 200

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, name, chain, lat, lon, city FROM stores WHERE lat IS NOT NULL AND lon IS NOT NULL')
            existing = cur.fetchall()
            cur.close()
        finally:
            conn.close()

        conflicts = []
        for s in existing:
            if str(s['id']) == exclude_id:
                continue
            if s['lat'] is None or s['lon'] is None:
                continue
            dist_km = haversine_km(lat, lon, float(s['lat']), float(s['lon']))
            dist_m = dist_km * 1000

            if population < 3000:
                # Malá obec: kontrola stejné obce
                s_city = (s['city'] or '').strip().lower()
                if s_city and city and s_city == city:
                    conflicts.append({'store_name': s['name'], 'distance_m': round(dist_m), 'reason': 'same_village'})
            else:
                # Město: min. 800 m
                if dist_m < 800:
                    conflicts.append({'store_name': s['name'], 'distance_m': round(dist_m), 'reason': 'too_close'})

        if conflicts:
            if population < 3000:
                msg = "Informace: V teto obci jiz mame jednu prodejnu ({}). Neni to prekazka — rozhodnuti je na vas.".format(conflicts[0]['store_name'])
            else:
                c = conflicts[0]
                msg = "Informace: V okoli {} m je jiz prodejna {}. Neni to prekazka — rozhodnuti je na vas.".format(c['distance_m'], c['store_name'])
            return jsonify({'allowed': True, 'warning': msg, 'conflicts': conflicts, 'message': msg}), 200

        return jsonify({'allowed': True, 'warning': None, 'conflicts': [], 'message': None}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stores/<store_id>', methods=['DELETE'])
@require_admin_key
def delete_store(store_id):
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM stores WHERE id = %s', (store_id,))
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return jsonify({'success': True, 'message': 'Prodejna smazána'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registrations', methods=['POST'])
def create_registration():
    try:
        data = request.json
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    ico TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    is_vietnamese BOOLEAN DEFAULT FALSE,
                    pin TEXT,
                    approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                INSERT INTO registrations (name, ico, phone, is_vietnamese)
                VALUES (%s, %s, %s, %s)
            """, (data['name'], data['ico'], data['phone'],
                  data.get('isVietnamese', False)))
            conn.commit()
            cur.close()
        finally:
            conn.close()

        try:
            is_viet = data.get('isVietnamese', False)
            viet_label = ' 🇻🇳 VIETNAMSKÁ PRODEJNA' if is_viet else ''

            msg = MIMEMultipart()
            msg['Subject'] = f"A-GROSS SOS – nová žádost o přístup: {data['name']}"
            msg['From'] = 'objednavky@a-gross.cz'
            msg['To'] = 'objednavky@a-gross.cz, litvin@a-gross.cz'

            body = f"""Nová žádost o přístup do A-GROSS SOS{viet_label}

Název prodejny: {data['name']}
IČO: {data['ico']}
Telefon: {data['phone']}
Datum: {data.get('timestamp', 'neuvedeno')}

Pro schválení otevřete admin panel:
https://standa0262.github.io/agross-sos/AGROSS_SOS_ADMIN.html

Po schválení odešlete PIN přes WhatsApp na: {data['phone']}
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP('smtp.a-gross.cz', 587) as server:
                server.starttls()
                server.login(
                    os.environ.get('SMTP_USER', 'objednavky@a-gross.cz'),
                    os.environ.get('SMTP_PASS', '')
                )
                server.send_message(msg)
        except Exception as mail_err:
            print(f'Email notifikace selhal: {mail_err}')

        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registrations/verify', methods=['POST'])
def verify_registration():
    try:
        data = request.json
        pin = data.get('pin', '').strip()
        name = data.get('name', '').strip()

        if not check_rate_limit(name):
            return jsonify({'success': False, 'error': 'Příliš mnoho pokusů, zkuste to znovu za pár minut.'}), 429

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM registrations
                WHERE pin = %s AND name = %s AND approved = TRUE
            """, (pin, name))
            row = cur.fetchone()
            cur.close()
        finally:
            conn.close()
        if row:
            return jsonify({'success': True}), 200
        return jsonify({'success': False}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def find_store_by_registration_name(name):
    """
    Dohledá záznam ve `stores` podle jména z registrace (case-insensitive
    shoda) - viz get_packaging_for_registration a resolve_authoritative_store
    níž pro vysvětlení kompromisu (registrations síť/store vůbec needeviduje).
    Vrací dict se sloupci id/name/chain, nebo None.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, name, chain FROM stores WHERE LOWER(name) = LOWER(%s) LIMIT 1', (name,))
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()
    return row


def get_packaging_for_registration(name):
    """
    Dohledá typ balení pro přihlášenou prodejnu podle jejího jména z registrace.

    POZOR - řešení kompromisu: tabulka `registrations` (jméno+PIN, přihlašovací
    údaje) síť vůbec neeviduje - appka ji při odeslání žádosti o přístup
    neposílá a nikde se needituje ani v admin panelu. Jediné místo, kde je síť
    (chain) uložená, je tabulka `stores` (vyplní se, až majitel založí profil
    prodejny v appce). Proto zkoušíme dohledat prodejnu se stejným názvem
    (case-insensitive) a použít její chain.

    Když se prodejna se stejným jménem v `stores` nenajde (typicky: přihlásil
    se, ale profil prodejny ještě nevyplnil), vrátí se výchozí krabička
    (None) - stejné chování jako appka bez ?sit= parametru.

    Robustnější dlouhodobé řešení by bylo přidat sloupec chain přímo do
    registrations (vyplňovaný adminem při schvalování) - to by ale znamenalo
    i úpravu admin panelu, což jsem v rámci tohoto zadání neimplementoval.
    """
    row = find_store_by_registration_name(name)
    return get_packaging_for_chain(row['chain'] if row else None)


def resolve_authoritative_store(name, client_store_id, client_store_name):
    """
    Server-side dohledání "pravé" prodejny pro objednávku (sync_order) -
    stejná fuzzy shoda jména jako get_packaging_for_registration, NE
    storeId/storeName, které pošle appka (to jde snadno podvrhnout, protože
    STORE_APP_KEY je veřejný - viz komentář u sync_order).

    Když se podle jména žádná prodejna v `stores` nenajde (typicky:
    přihlášený, ale profil prodejny ještě nevyplnil), spadneme zpět na
    storeId/storeName z požadavku - je to kompromis, ne ideální stav, ale
    bez něj by appka přestala fungovat pro legitimní prodejny bez
    vyplněného profilu. V tomhle fallbacku packaging defaultuje na
    krabičku (žádný ověřený zdroj chain) - stejné chování jako appka bez
    ?sit= parametru.

    Vrací (store_id, store_name, chain).
    """
    row = find_store_by_registration_name(name)
    if row:
        store_name = (row['chain'] + ' – ' + row['name']) if row['chain'] else row['name']
        return str(row['id']), store_name, row['chain']
    return client_store_id, client_store_name, None


@app.route('/api/catalog/prices', methods=['POST'])
def catalog_prices():
    """
    Vrátí nákupní ceny (NC) katalogu pro přihlášenou prodejnu - appka je
    dřív držela natvrdo v A_GROSS_SOS.html, kde je viděl kdokoli přes
    "zobrazit zdroj stránky" i bez přihlášení. Ověření stejné jako
    /api/registrations/verify (jméno+PIN, sdílí i rate limiting).

    Vstup: { "name": "...", "pin": "1234" }
    Odpověď (úspěch): { "success": true, "prices": {"S276921": 37.44, ...} }
    Odpověď (chyba):  { "success": false }, 401
    """
    try:
        data = request.json or {}
        pin = (data.get('pin') or '').strip()
        name = (data.get('name') or '').strip()

        if not check_rate_limit(name):
            return jsonify({'success': False, 'error': 'Příliš mnoho pokusů, zkuste to znovu za pár minut.'}), 429

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM registrations
                WHERE pin = %s AND name = %s AND approved = TRUE
            """, (pin, name))
            row = cur.fetchone()
            cur.close()
        finally:
            conn.close()

        if not row:
            return jsonify({'success': False}), 401

        packaging = get_packaging_for_registration(name)
        prices = {
            kod: (p['ncCelofan'] if (packaging == 'celofan' and p['ncCelofan'] is not None) else p['ncKrabicka'])
            for kod, p in PRICE_TABLE.items()
        }

        return jsonify({'success': True, 'prices': prices}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/registrations/list', methods=['GET'])
@require_admin_key
def list_registrations():
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, ico, phone, is_vietnamese,
                       pin, approved, created_at
                FROM registrations
                ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()
        return jsonify({'success': True, 'registrations': rows}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registrations/approve', methods=['POST'])
@require_admin_key
def approve_registration():
    try:
        data = request.json
        reg_id = data.get('id')
        pin = data.get('pin', '').strip()
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE registrations
                SET approved = TRUE, pin = %s
                WHERE id = %s
            """, (pin, reg_id))
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stores/update', methods=['POST'])
@require_admin_key
def update_store():
    try:
        data = request.json
        store_id = data.get('id')
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE stores SET
                  name=%s, manager=%s, phone=%s, address=%s,
                  ico=%s, email=%s, hours_week=%s, hours_weekend=%s, note=%s
                WHERE id=%s
            """, (data.get('name'), data.get('manager'), data.get('phone'),
                  data.get('address'), data.get('ico'), data.get('email'),
                  data.get('hoursWeek'), data.get('hoursWeekend'),
                  data.get('note'), store_id))
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registrations/<int:reg_id>', methods=['DELETE'])
@require_admin_key
def delete_registration(reg_id):
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM registrations WHERE id=%s', (reg_id,))
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/api/health', methods=['GET'])
def api_health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

# ═════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🚀 A-GROSS SOS Admin Backend")
    print("📍 http://localhost:5000")
    print("📊 Měsíční report: GET /api/reports/monthly?network=Provector&year=2026&month=6")
    print("📧 Export: GET /api/reports/monthly/export?network=Provector")
    print()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
