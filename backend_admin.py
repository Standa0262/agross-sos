#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A-GROSS SOS – Admin Backend
Měsíční reporting pro sítě a správa komisí

Instalace:
    pip install flask flask-cors psycopg2 python-dateutil
    
Spuštění:
    python app.py
    
API Endpoints:
    POST /api/orders/sync – Příjem offline objednávek
    GET /api/reports/monthly – Měsíční report pro síť
    GET /api/orders – Všechny objednávky v období
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

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

DATA_FILE = 'orders_db.json'

# ═════════════════════════════════════════════════════════════════════
# DATABÁZE (JSONl soubor – ve výrobě bude PostgreSQL)
# ═════════════════════════════════════════════════════════════════════

def load_orders():
    """Načíst všechny objednávky ze souboru"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_orders(orders):
    """Uložit objednávky"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

# ═════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═════════════════════════════════════════════════════════════════════

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
        
        # Přidat metadata
        order['id'] = order.get('id') or f"ORD-{int(datetime.now().timestamp()*1000)}"
        order['synced'] = True
        order['synced_at'] = datetime.now().isoformat()
        
        # Uložit
        orders = load_orders()
        orders.append(order)
        save_orders(orders)
        
        return jsonify({
            'success': True,
            'message': 'Objednávka přijata',
            'orderId': order['id']
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

# ═════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health_check():
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
