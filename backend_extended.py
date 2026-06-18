#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A-GROSS SOS – Extended Backend
admin_panel.html + push notifikace + PDF faktury

Instalace:
    pip install flask flask-cors firebase-admin pdfkit python-dateutil

Spuštění:
    python backend_extended.py
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json, os, io, sys
from datetime import datetime, timedelta

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8')
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials, messaging
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib import colors

app = Flask(__name__)
CORS(app)

# ═════════════════════════════════════════════════════════════════════
# FIREBASE SETUP (Push Notifications)
# ═════════════════════════════════════════════════════════════════════

try:
    firebase_admin.initialize_app(
        credentials.Certificate('firebase-key.json')
    )
except:
    print("⚠️ Firebase not configured. Push notifications disabled.")

# ═════════════════════════════════════════════════════════════════════
# DATABÁZE
# ═════════════════════════════════════════════════════════════════════

DATA_FILE = 'orders_db.json'
NETWORKS_FILE = 'networks.json'
NOTIF_FILE = 'notifications.json'

def load_json(filename, default=[]):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

COMMISSION_RATES = {
    'Provector': 0.05,
    'MO Partner': 0.05,
}

# ═════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ═════════════════════════════════════════════════════════════════════

@app.route('/api/networks', methods=['GET'])
def get_networks():
    """Vrátí všechny registrované sítě"""
    networks = load_json(NETWORKS_FILE, [])
    # Přidej default sítě
    if not networks:
        networks = [
            {
                'id': 'net-1',
                'name': 'Provector',
                'email': 'finance@provector.vn',
                'commission_rate': 0.05,
                'contact': '+84 9xx xxxx xxx'
            },
            {
                'id': 'net-2',
                'name': 'MO Partner',
                'email': 'finance@mopartner.cz',
                'commission_rate': 0.05,
                'contact': '+420 5xx xxx xxx'
            }
        ]
    return jsonify(networks), 200

@app.route('/api/networks', methods=['POST'])
def create_network():
    """Přidat novou síť"""
    try:
        network = request.json
        network['id'] = f"net-{int(datetime.now().timestamp()*1000)}"
        
        networks = load_json(NETWORKS_FILE, [])
        networks.append(network)
        save_json(NETWORKS_FILE, networks)
        
        return jsonify({'success': True, 'network_id': network['id']}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/monthly', methods=['GET'])
def monthly_stats():
    """Měsíční statistiky - pro dashboard"""
    try:
        orders = load_json(DATA_FILE, [])
        networks = load_json(NETWORKS_FILE, [])
        
        # Filtrovat objednávky za poslední měsíc
        today = datetime.now()
        month_ago = today - timedelta(days=30)
        recent_orders = [
            o for o in orders
            if datetime.fromisoformat(o.get('date', '')).date() >= month_ago.date()
        ]
        
        # Agregovat
        total_purchase = sum(o.get('nc', 0) for o in recent_orders)
        total_commission = total_purchase * 0.05  # default 5%
        
        stores = set(o.get('storeId') for o in recent_orders)
        
        return jsonify({
            'success': True,
            'active_stores': len(stores),
            'total_orders': len(recent_orders),
            'total_purchase': round(total_purchase, 2),
            'total_commission': round(total_commission, 2),
            'networks_count': len(networks)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stores/top', methods=['GET'])
def top_stores():
    """Top obchody podle objednávek"""
    try:
        limit = int(request.args.get('limit', 5))
        orders = load_json(DATA_FILE, [])
        
        store_stats = defaultdict(lambda: {'count': 0, 'total': 0})
        for o in orders:
            store_name = o.get('storeName', 'Unknown')
            store_stats[store_name]['count'] += 1
            store_stats[store_name]['total'] += o.get('nc', 0)
        
        # Sort by order count
        top = sorted(
            [
                {
                    'name': name,
                    'orders_count': stats['count'],
                    'total_purchase': stats['total'],
                    'network': '—'
                }
                for name, stats in store_stats.items()
            ],
            key=lambda x: x['orders_count'],
            reverse=True
        )[:limit]
        
        return jsonify(top), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/catalogs/sync', methods=['GET'])
def catalogs_sync():
    """Vrátí katalog produktů (pro admin panel a synchronizaci)
    Pokud neexistuje `catalog.json`, vrátí vestavěný demo katalog."""
    try:
        products = load_json('catalog.json', None)
        if products is None or not isinstance(products, list) or len(products) == 0:
            # Default demo produkty
            products = [
                {'kod': 'P001', 'nazev': 'Kim Organ 10m', 'nc': 45.0, 'moc': 79.0, 'ean': '8594000000001'},
                {'kod': 'P002', 'nazev': 'Chỉ may 100m', 'nc': 12.5, 'moc': 25.0, 'ean': '8594000000002'},
                {'kod': 'P003', 'nazev': 'Khóa spona', 'nc': 30.0, 'moc': 55.0, 'ean': '8594000000003'},
            ]
        return jsonify({'products': products}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Vrátí seznam všech objednávek (pro admin panel)"""
    try:
        orders = load_json(DATA_FILE, [])
        # řadit podle data sestupně
        orders_sorted = sorted(orders, key=lambda o: o.get('date', ''), reverse=True)
        return jsonify({'orders': orders_sorted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders/sync', methods=['POST'])
def sync_order():
    """Přijme objednávku od klienta a uloží do databáze (orders_db.json)"""
    try:
        order = request.json
        if not order.get('id'):
            order['id'] = f"order-{int(datetime.now().timestamp()*1000)}"
        # zajistit pole date
        if not order.get('date'):
            order['date'] = datetime.now().isoformat()

        orders = load_json(DATA_FILE, [])
        orders.append(order)
        save_json(DATA_FILE, orders)
        return jsonify({'success': True, 'order_id': order['id']}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/monthly', methods=['GET'])
def monthly_report_json():
    """Vrátí měsíční report pro zadanou síť ve formátu JSON
    Query params: network (volitelné), year, month"""
    try:
        network = request.args.get('network', '')
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))

        orders = load_json(DATA_FILE, [])
        from_date = datetime(year, month, 1)
        if month == 12:
            to_date = datetime(year + 1, 1, 1)
        else:
            to_date = datetime(year, month + 1, 1)

        # filtr podle data a (volitelně) sítě
        def in_range(o):
            try:
                od = datetime.fromisoformat(o.get('date'))
                if not (from_date <= od < to_date):
                    return False
                if network:
                    return network.lower() in o.get('storeName', '').lower()
                return True
            except:
                return False

        filtered = [o for o in orders if in_range(o)]

        # agregace po obchodech
        store_stats = defaultdict(lambda: {'orders_count': 0, 'total_purchase': 0.0})
        for o in filtered:
            name = o.get('storeName', 'Unknown')
            store_stats[name]['orders_count'] += 1
            store_stats[name]['total_purchase'] += float(o.get('nc', 0))

        stores_list = []
        for name, s in store_stats.items():
            stores_list.append({
                'store_name': name,
                'orders_count': s['orders_count'],
                'total_purchase': round(s['total_purchase'], 2),
                'commission': round(s['total_purchase'] * 0.05, 2)
            })

        total_purchase = sum(s['total_purchase'] for s in store_stats.values())
        commission_rate = 0.05
        commission_amount = round(total_purchase * commission_rate, 2)

        report = {
            'network': network or 'ALL',
            'period': f"{month}/{year}",
            'stores_count': len(store_stats),
            'total_orders': len(filtered),
            'total_purchase_value': round(total_purchase, 2),
            'commission_rate': commission_rate,
            'commission_amount': commission_amount,
            'stores': sorted(stores_list, key=lambda x: x['total_purchase'], reverse=True)
        }

        return jsonify(report), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═════════════════════════════════════════════════════════════════════
# PUSH NOTIFICATIONS (Firebase Cloud Messaging)
# ═════════════════════════════════════════════════════════════════════

@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """Poslat push notifikaci všem nákupčím nebo cílové skupině"""
    try:
        data = request.json
        target = data.get('target', 'all')  # all, network, store
        title = data.get('title', '')
        body = data.get('body', '')
        
        # Vytvořit FCM zprávu
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data={
                'target': target,
                'sent_at': datetime.now().isoformat()
            },
            # TODO: Filter devices based on target
            tokens=['device_token_1', 'device_token_2']  # placeholder
        )
        
        # Poslat (pokud je Firebase configured)
        try:
            response = messaging.send_multicast(message)
            delivered = response.success_count
        except:
            delivered = 0
        
        # Log notifikaci
        notif_log = {
            'id': f"notif-{int(datetime.now().timestamp()*1000)}",
            'sent_at': datetime.now().isoformat(),
            'target': target,
            'title': title,
            'body': body,
            'delivered': delivered
        }
        
        notifications = load_json(NOTIF_FILE, [])
        notifications.append(notif_log)
        save_json(NOTIF_FILE, notifications)
        
        return jsonify({
            'success': True,
            'notification_id': notif_log['id'],
            'delivered': delivered
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Vrátí historii poslených notifikací"""
    notifications = load_json(NOTIF_FILE, [])
    return jsonify({'notifications': notifications}), 200

# ═════════════════════════════════════════════════════════════════════
# PDF FAKTURY
# ═════════════════════════════════════════════════════════════════════

@app.route('/api/orders/<order_id>/pdf', methods=['GET'])
def generate_order_pdf(order_id):
    """Generovat PDF fakturu pro objednávku"""
    try:
        orders = load_json(DATA_FILE, [])
        order = next((o for o in orders if o.get('id') == order_id), None)
        
        if not order:
            return {'error': 'Order not found'}, 404
        
        # Vytvořit PDF v paměti
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Nadpis
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1A1A1A'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("A-GROSS SOS", title_style))
        story.append(Paragraph("FAKTURA/OBJEDNÁVKA", styles['Heading2']))
        story.append(Spacer(1, 0.5*cm))
        
        # Detaily objednávky
        data = [
            ['Číslo objednávky:', order.get('id')],
            ['Prodej na:', order.get('storeName')],
            ['Datum:', datetime.fromisoformat(order.get('date')).strftime('%d.%m.%Y')],
            ['Status:', order.get('status', 'Nová')]
        ]
        
        table = Table(data, colWidths=[6*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5F0E8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*cm))
        
        # Tabulka s položkami
        item_data = [['Kód', 'Název', 'Ks', 'Cena', 'Součet']]
        for item in order.get('items', []):
            qty = item.get('qty', 0)
            price = item.get('nc', 0)
            item_data.append([
                item.get('kod'),
                item.get('nazev')[:30],
                str(qty),
                f"{price:.2f}",
                f"{price*qty:.2f}"
            ])
        
        items_table = Table(item_data, colWidths=[2*cm, 6*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A1A1A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Totály
        totals_data = [
            ['Nákupní cena (bez DPH):', f"{order.get('nc', 0):.2f} Kč"],
            ['Marže:', f"{order.get('marze', 0):.2f} Kč"],
            ['Prodejní cena (s DPH):', f"{order.get('moc', 0):.2f} Kč"]
        ]
        
        totals_table = Table(totals_data, colWidths=[10*cm, 6*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2A7A4A')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 1*cm))
        
        # Footer
        story.append(Paragraph(
            "A-GROSS, s.r.o. | Olomouc-Holice | www.a-gross.cz",
            styles['Normal']
        ))
        
        # Generovat PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"order_{order_id}.pdf"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<report_id>/pdf', methods=['GET'])
def generate_report_pdf(report_id):
    """Generovat PDF měsíční report pro síť"""
    try:
        network = request.args.get('network')
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        # Načíst report
        orders = load_json(DATA_FILE, [])
        from_date = f"{year}-{month:02d}-01"
        next_m = month + 1 if month < 12 else 1
        next_y = year if month < 12 else year + 1
        to_date = f"{next_y}-{next_m:02d}-01"
        
        network_orders = [
            o for o in orders
            if network in o.get('storeName', '') and
               from_date <= o.get('date', '')[:10] < to_date
        ]
        
        # Agregovat
        store_stats = defaultdict(lambda: {'orders': 0, 'total': 0})
        for o in network_orders:
            store = o.get('storeName')
            store_stats[store]['orders'] += 1
            store_stats[store]['total'] += o.get('nc', 0)
        
        total_purchase = sum(s['total'] for s in store_stats.values())
        commission_rate = 0.05  # TODO: get from COMMISSION_RATES
        total_commission = total_purchase * commission_rate
        
        # Vytvořit PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        story.append(Paragraph(f"A-GROSS SOS – Měsíční Report", styles['Heading1']))
        story.append(Paragraph(f"Síť: {network}", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        # Shrnutí
        summary_data = [
            ['Měsíc/Rok:', f"{month}/{year}"],
            ['Počet obchodů:', str(len(store_stats))],
            ['Počet objednávek:', str(len(network_orders))],
            ['Nákupy bez DPH:', f"{total_purchase:.2f} Kč"],
            ['Sazba provize:', f"{commission_rate*100}%"],
            ['Provize k výplatě:', f"{total_commission:.2f} Kč"]
        ]
        
        summary_table = Table(summary_data, colWidths=[6*cm, 10*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5F0E8')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, -1), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, -1), (1, -1), colors.HexColor('#2A7A4A')),
            ('FONTSIZE', (1, -1), (1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Detaily po obchodech
        detail_data = [['Obchod', 'Objednávky', 'Nákup Kč', 'Provize Kč']]
        for store, stats in sorted(store_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            provize = stats['total'] * commission_rate
            detail_data.append([
                store,
                str(stats['orders']),
                f"{stats['total']:.2f}",
                f"{provize:.2f}"
            ])
        
        detail_table = Table(detail_data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A1A1A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(detail_table)
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"report_{network}_{year}_{month}.pdf"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═════════════════════════════════════════════════════════════════════
# CATALOG & ORDERS (Missing endpoints)
# ═════════════════════════════════════════════════════════════════════

@app.route('/api/catalogs/sync', methods=['GET'])
def sync_catalog():
    """Vrátit katalog produktů"""
    try:
        # Default produkty (stejné jako v web app)
        products = [
            {'kod': 'KIM-001', 'nazev': 'Kim Organ A', 'nc': 5.50, 'moc': 8.20, 'ean': '8594177130006'},
            {'kod': 'KIM-002', 'nazev': 'Kim Organ B', 'nc': 6.00, 'moc': 9.00, 'ean': '8594177130013'},
            {'kod': 'KHOA-001', 'nazev': 'Khóa czip #3', 'nc': 12.00, 'moc': 18.00, 'ean': '4006166053108'},
            {'kod': 'CHI-001', 'nazev': 'Chỉ polyester 40x300', 'nc': 8.50, 'moc': 12.75, 'ean': '8718721050407'},
            {'kod': 'TAI-001', 'nazev': 'Tái sử dụng khóa 5mm', 'nc': 15.00, 'moc': 22.50, 'ean': '8716999932197'},
            {'kod': 'NUT-001', 'nazev': 'Nút 2 lỗ 13mm', 'nc': 3.20, 'moc': 4.80, 'ean': '8715384000008'},
            {'kod': 'VAI-001', 'nazev': 'Vải cotton twill', 'nc': 45.00, 'moc': 67.50, 'ean': '5901625509030'},
            {'kod': 'BANG-001', 'nazev': 'Băng dệt 25mm', 'nc': 22.00, 'moc': 33.00, 'ean': '8721027400108'},
        ]
        return jsonify({'success': True, 'products': products}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

# ═════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🚀 A-GROSS SOS Extended Backend")
    print("📊 Admin Panel: http://localhost:5000/admin_panel.html")
    print("📞 API: http://localhost:5000")
    print()
    app.run(host='0.0.0.0', port=5000, debug=False)
