#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A-GROSS SOS – Admin Backend
Měsíční reporting pro sítě a správa komisí

Instalace:
    pip install flask flask-cors psycopg2-binary python-dateutil

Spuštění:
    DATABASE_URL=postgresql://... python backend_admin.py

API Endpoints:
    POST /api/db/init – Vytvoří databázové tabulky (pokud neexistují)
    POST /api/orders/sync – Příjem offline objednávek (ukládá do DB)
    GET /api/orders – Objednávky (filtr store_id, from_date, to_date, network)
    POST /api/stores/sync – Uložení/aktualizace prodejny
    GET /api/stores – Všechny prodejny
    GET /api/reports/monthly – Měsíční report pro síť
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor, Json

app = Flask(__name__)
CORS(app)

# ═════════════════════════════════════════════════════════════════════
# KONFIGURACE
# ═════════════════════════════════════════════════════════════════════

COMMISSION_RATES = {
    'Provector': 0.05,  # 5%
    'MO Partner': 0.05, # 5%
    # Přidat další sítě dle dohody
}

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
def sync_order():
    """
    Příjem objednávky z offline režimu.
    
    Postup:
    1. Přijmout objednávku z mobilní aplikace
    2. Uložit do databáze
    3. Označit jako "synced"
    4. Odeslat potvrzení
    
    JSON struktura:
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
        "status": "new"
    }
    """
    try:
        order = request.json

        # Validace
        if not order.get('storeId') or not order.get('items'):
            return jsonify({'error': 'Chybí storeId nebo items'}), 400

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
                order.get('storeId'),
                order.get('storeName'),
                order.get('date') or datetime.now().isoformat(),
                Json(order.get('items')),
                order.get('nc'),
                order.get('marze'),
                order.get('moc'),
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
def get_stores():
    """Vrátí všechny prodejny."""
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

@app.route('/api/reports/monthly', methods=['GET'])
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
