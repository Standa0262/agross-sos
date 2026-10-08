# -*- coding: utf-8 -*-
"""
Testy čistých chyb ve veřejných endpointech: netextové vstupy -> 400
"Neplatný požadavek." bez sahání do DB a limitu pokusů; pád databáze -> 500
s obecnou hláškou, bez interního textu výjimky v odpovědi i v logu.
Databáze je falešná (FakeDB z test_change_pin) - testy se nikdy nepřipojují
k produkčnímu Postgresu.
"""
import logging

import pytest

import backend_admin as ba
from test_change_pin import FakeDB, NAME, STORE_KEY

SECRET = 'TAJNY-INTERNI-TEXT heslo=xyz pin 9711'
AUTH = {'Authorization': 'Bearer ' + STORE_KEY}

# endpointy s name+pin: (cesta, hlavičky)
NAME_PIN_ENDPOINTS = [
    ('/api/registrations/verify', {}),
    ('/api/catalog/prices', {}),
    ('/api/orders/sync', AUTH),
]


@pytest.fixture
def db(monkeypatch):
    fake = FakeDB()
    fake.add(50, NAME, '9711')
    monkeypatch.setattr(ba, 'get_db', fake.connect)
    monkeypatch.setattr(ba, 'STORE_APP_KEY', STORE_KEY)
    ba._rate_limit_attempts.clear()
    ba._name_failed_attempts.clear()
    return fake


@pytest.fixture
def client():
    ba.app.config['TESTING'] = True
    return ba.app.test_client()


# ── netextové vstupy ─────────────────────────────────────────────────────

@pytest.mark.parametrize('path,headers', NAME_PIN_ENDPOINTS)
@pytest.mark.parametrize('field', ['name', 'pin'])
@pytest.mark.parametrize('bad', [1234, 12.5, True, False, ['9711'], {'a': '9711'}])
def test_netextove_name_pin_400_bez_db_a_limitu(client, db, path, headers, field, bad):
    body = {'name': NAME, 'pin': '9711', 'items': []}
    body[field] = bad
    res = client.post(path, json=body, headers=headers)
    assert res.status_code == 400
    assert res.get_json()['error'] == 'Neplatný požadavek.'
    assert db.executed == []
    assert not ba._rate_limit_attempts
    assert not ba._name_failed_attempts


@pytest.mark.parametrize('path,headers', NAME_PIN_ENDPOINTS)
@pytest.mark.parametrize('payload', [
    {'json': ['9711']},
    {'json': '9711'},
    {'json': 42},
    {'json': None},
    {'data': 'tohle není JSON', 'content_type': 'application/json'},
    {'data': 'name=x&pin=1', 'content_type': 'application/x-www-form-urlencoded'},
    {},
])
def test_telo_neni_json_objekt_400(client, db, path, headers, payload):
    res = client.post(path, headers=headers, **payload)
    assert res.status_code == 400
    assert res.get_json()['error'] == 'Neplatný požadavek.'
    assert db.executed == []
    assert not ba._rate_limit_attempts


def test_verify_a_ceny_maji_pri_400_success_false(client, db):
    for path in ('/api/registrations/verify', '/api/catalog/prices'):
        assert client.post(path, json={'name': NAME, 'pin': 9711}).get_json()['success'] is False


@pytest.mark.parametrize('body', [{'name': NAME, 'pin': None}, {'name': NAME}])
def test_chybejici_nebo_null_pin_je_neplatne_prihlaseni_ne_400(client, db, body):
    # Appka po smazání odmítnutého PINu posílá pin: null a na 401
    # "Neplatné přihlášení prodejny" reaguje výzvou k novému přihlášení.
    res = client.post('/api/orders/sync', json={**body, 'items': []}, headers=AUTH)
    assert (res.status_code, res.get_json()) == (401, {'error': 'Neplatné přihlášení prodejny'})
    res = client.post('/api/catalog/prices', json=body)
    assert (res.status_code, res.get_json()) == (401, {'success': False})
    res = client.post('/api/registrations/verify', json=body)
    assert (res.status_code, res.get_json()) == (200, {'success': False})


def test_platne_prihlaseni_dal_funguje(client, db):
    assert client.post('/api/registrations/verify', json={'name': NAME, 'pin': '9711'}).get_json()['success'] is True
    res = client.post('/api/catalog/prices', json={'name': NAME, 'pin': '9711'})
    assert res.status_code == 200 and res.get_json()['success'] is True and res.get_json()['prices']


# ── pád databáze / interní chyba -> obecná 500 ───────────────────────────

def _boom(*a, **kw):
    raise RuntimeError(SECRET)


CRASH_CASES = [
    ('POST', '/api/registrations/verify', {'name': NAME, 'pin': '9711'}, {}),
    ('POST', '/api/catalog/prices', {'name': NAME, 'pin': '9711'}, {}),
    ('POST', '/api/orders/sync', {'name': NAME, 'pin': '9711', 'items': []}, AUTH),
    ('POST', '/api/registrations/change-pin', {'name': NAME, 'pin': '9711', 'newPin': '2468'}, {}),
    ('POST', '/api/registrations', {'name': NAME, 'ico': '1', 'phone': '1'}, {}),
    ('GET', '/api/stores/public', None, {}),
    ('GET', '/api/notifications/active', None, {}),
]


@pytest.mark.parametrize('method,path,body,headers', CRASH_CASES)
def test_pad_databaze_vraci_obecnou_500_bez_interniho_textu(client, db, monkeypatch, caplog, method, path, body, headers):
    monkeypatch.setattr(ba, 'get_db', _boom)
    with caplog.at_level(logging.ERROR):
        res = client.open(path, method=method, json=body, headers=headers)
    assert res.status_code == 500
    assert res.get_json() == {'error': ba.INTERNAL_ERROR_MESSAGE}
    assert 'TAJNY' not in res.get_data(as_text=True)
    # do logu jde typ výjimky a místo v kódu, ale ne její text (může obsahovat PIN)
    assert 'RuntimeError' in caplog.text
    assert 'TAJNY' not in caplog.text and '9711' not in caplog.text and '2468' not in caplog.text


def test_pad_katalogu_vraci_obecnou_500(client, db, monkeypatch, caplog):
    monkeypatch.setattr(ba.os.path, 'exists', _boom)
    with caplog.at_level(logging.ERROR):
        res = client.get('/api/catalogs/sync')
    assert res.status_code == 500
    assert res.get_json() == {'error': ba.INTERNAL_ERROR_MESSAGE}
    assert 'TAJNY' not in res.get_data(as_text=True) and 'TAJNY' not in caplog.text


def test_pad_v_dotazu_cursoru_neprozradi_text(client, db, monkeypatch, caplog):
    # chyba až při SQL dotazu (ne při připojení), s pgcode jako u psycopg2
    class PgError(Exception):
        pgcode = '42P01'

    class BadCursor:
        def execute(self, *a):
            raise PgError(SECRET)

    class BadConn:
        def cursor(self):
            return BadCursor()

        def close(self):
            pass

    monkeypatch.setattr(ba, 'get_db', lambda: BadConn())
    with caplog.at_level(logging.ERROR):
        res = client.post('/api/registrations/verify', json={'name': NAME, 'pin': '9711'})
    assert res.get_json() == {'error': ba.INTERNAL_ERROR_MESSAGE}
    assert 'PgError (pgcode 42P01)' in caplog.text
    assert 'TAJNY' not in caplog.text and '9711' not in caplog.text
