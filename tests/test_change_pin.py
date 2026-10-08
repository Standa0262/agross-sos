# -*- coding: utf-8 -*-
"""
Testy změny PINu prodejnou (POST /api/registrations/change-pin) a limitu
neúspěšných pokusů podle jména. Databáze je nahrazená falešnou v paměti
(FakeDB) - testy se nikdy nepřipojují k produkčnímu Postgresu.

Spuštění:  pip install -r requirements-dev.txt  &&  python -m pytest tests
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backend_admin as ba  # noqa: E402

NAME = 'Kouba - Veselá s.r.o.'
STORE_KEY = 'test-store-key'


class FakeDB:
    """Napodobí tabulku registrations pro SQL příkazy, které endpointy posílají."""

    def __init__(self):
        self.regs = {}  # id -> {name, pin, approved}
        self.executed = []

    def add(self, reg_id, name, pin, approved=True):
        self.regs[reg_id] = {'name': name, 'pin': pin, 'approved': approved}

    def connect(self):
        return FakeConn(self)


class FakeConn:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return FakeCursor(self.db)

    def commit(self):
        pass

    def close(self):
        pass


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self.result = None

    def execute(self, sql, params=()):
        self.db.executed.append(sql)
        sql = ' '.join(sql.split())
        if sql.startswith('UPDATE registrations SET pin = %s WHERE name = %s AND pin = %s'):
            new_pin, name, pin = params
            for reg_id, r in self.db.regs.items():
                if r['name'] == name and r['pin'] == pin and r['approved']:
                    r['pin'] = new_pin
                    self.result = {'id': reg_id}
                    return
            self.result = None
        elif sql.startswith('SELECT id FROM registrations WHERE pin = %s AND name = %s'):
            pin, name = params
            self.result = next(({'id': i} for i, r in self.db.regs.items()
                                if r['name'] == name and r['pin'] == pin and r['approved']), None)
        elif sql.startswith('SELECT * FROM stores'):
            self.result = None
        else:
            raise AssertionError(f'Neočekávaný SQL příkaz v testu: {sql}')

    def fetchone(self):
        return self.result

    def close(self):
        pass


@pytest.fixture
def db(monkeypatch):
    fake = FakeDB()
    fake.add(50, NAME, '9711')
    monkeypatch.setattr(ba, 'get_db', fake.connect)
    monkeypatch.setattr(ba, 'STORE_APP_KEY', STORE_KEY)
    ba._rate_limit_attempts.clear()
    ba._name_failed_attempts.clear()
    monkeypatch.setattr(ba, '_rate_limit_last_prune', 0.0)
    return fake


@pytest.fixture
def client():
    ba.app.config['TESTING'] = True
    return ba.app.test_client()


def change(client, pin, new_pin, name=NAME, ip='10.0.0.1'):
    return client.post('/api/registrations/change-pin',
                       json={'name': name, 'pin': pin, 'newPin': new_pin},
                       headers={'X-Forwarded-For': ip})


def verify(client, pin, name=NAME, ip='10.0.0.1'):
    return client.post('/api/registrations/verify', json={'name': name, 'pin': pin},
                       headers={'X-Forwarded-For': ip})


# ── změna PINu ───────────────────────────────────────────────────────────

def test_zmena_pinu_uspech_a_pak_plati_jen_novy(client, db):
    res = change(client, '9711', '2468')
    assert res.status_code == 200
    assert res.get_json() == {'success': True}
    assert db.regs[50]['pin'] == '2468'
    assert verify(client, '2468').get_json()['success'] is True
    assert verify(client, '9711').get_json()['success'] is False


def test_spatny_soucasny_pin_vraci_401_a_pin_se_nemeni(client, db):
    res = change(client, '0000', '2468')
    assert res.status_code == 401
    assert res.get_json() == {'success': False}
    assert db.regs[50]['pin'] == '9711'


def test_neexistujici_jmeno_vypada_stejne_jako_spatny_pin(client, db):
    a = change(client, '0000', '2468')
    b = change(client, '9711', '2468', name='Neexistující prodejna')
    assert (a.status_code, a.get_json()) == (b.status_code, b.get_json()) == (401, {'success': False})


def test_neschvalena_registrace_pin_nezmeni(client, db):
    db.add(51, 'Čekající prodejna', '5555', approved=False)
    res = change(client, '5555', '2468', name='Čekající prodejna')
    assert res.status_code == 401
    assert db.regs[51]['pin'] == '5555'


@pytest.mark.parametrize('new_pin', [
    '', '123', '123456789', '12a4', ' 2 4 6 8', '1111', '00000000', '1234', '4321', '9711',
])
def test_neplatny_novy_pin_400_bez_dotazu_do_db_a_bez_spotreby_pokusu(client, db, new_pin):
    res = change(client, '9711', new_pin)
    assert res.status_code == 400
    assert res.get_json()['success'] is False
    assert res.get_json()['error']
    assert db.executed == []
    assert not ba._rate_limit_attempts
    assert db.regs[50]['pin'] == '9711'


@pytest.mark.parametrize('new_pin', [
    '２４６８',          # celošířkové číslice
    '٢٤٦٨',              # arabsko-indické číslice
    '۲۴۶۸',              # perské (východoarabské) číslice
    '24６8',             # mix ASCII a celošířkové
])
def test_ne_ascii_cislice_v_novem_pinu_400(client, db, new_pin):
    res = change(client, '9711', new_pin)
    assert res.status_code == 400
    assert db.executed == []
    assert db.regs[50]['pin'] == '9711'


@pytest.mark.parametrize('field', ['name', 'pin', 'newPin'])
@pytest.mark.parametrize('bad', [1234, 12.5, True, None, ['1234'], {'a': '1234'}])
def test_netextove_vstupy_vraci_400_ne_500(client, db, field, bad):
    body = {'name': NAME, 'pin': '9711', 'newPin': '2468'}
    body[field] = bad
    res = client.post('/api/registrations/change-pin', json=body)
    assert res.status_code == 400
    assert res.get_json()['success'] is False
    assert db.executed == []
    assert not ba._rate_limit_attempts
    assert db.regs[50]['pin'] == '9711'


@pytest.mark.parametrize('payload', [
    {'json': ['9711']},
    {'json': '9711'},
    {'json': 42},
    {'data': 'tohle není JSON', 'content_type': 'application/json'},
    {'data': 'name=x', 'content_type': 'application/x-www-form-urlencoded'},
    {},
])
def test_telo_pozadavku_neni_json_objekt_400(client, db, payload):
    res = client.post('/api/registrations/change-pin', **payload)
    assert res.status_code == 400
    assert db.executed == []


def test_osmimistny_pin_je_povoleny(client, db):
    assert change(client, '9711', '13572468').status_code == 200


def test_chybejici_jmeno_nebo_pin_400(client, db):
    assert change(client, '', '2468', name='').status_code == 400
    assert change(client, '', '2468').status_code == 400


def test_pin_se_nikde_nevypisuje(client, db, capsys, caplog):
    change(client, '9711', '2468')
    change(client, '0000', '1357')
    out = capsys.readouterr()
    logged = out.out + out.err + caplog.text
    for pin in ('9711', '2468', '0000', '1357'):
        assert pin not in logged


# ── rate limit ───────────────────────────────────────────────────────────

def test_limit_jmeno_ip_5_pokusu_vraci_429(client, db):
    for _ in range(5):
        assert change(client, '0000', '2468').status_code == 401
    res = change(client, '9711', '2468')
    assert res.status_code == 429
    assert db.regs[50]['pin'] == '9711'


def test_limit_podle_jmena_20_neuspechu_z_ruznych_ip(client, db):
    for i in range(20):
        assert change(client, '0000', '2468', ip=f'10.1.0.{i}').status_code == 401
    # 21. pokus ze zcela nové IP, i se správným PINem, je zablokovaný
    res = change(client, '9711', '2468', ip='10.9.9.9')
    assert res.status_code == 429
    assert db.regs[50]['pin'] == '9711'
    assert verify(client, '9711', ip='10.9.9.8').status_code == 429


def test_limit_podle_jmena_scita_verify_ceny_objednavky_i_change_pin(client, db):
    auth = {'Authorization': 'Bearer ' + STORE_KEY}
    for i in range(5):
        verify(client, '0000', ip=f'10.2.0.{i}')
        client.post('/api/catalog/prices', json={'name': NAME, 'pin': '0000'},
                    headers={'X-Forwarded-For': f'10.3.0.{i}'})
        res = client.post('/api/orders/sync', json={'name': NAME, 'pin': '0000', 'items': []},
                          headers={**auth, 'X-Forwarded-For': f'10.4.0.{i}'})
        assert res.status_code == 401
        assert res.get_json() == {'error': 'Neplatné přihlášení prodejny'}
        change(client, '0000', '2468', ip=f'10.5.0.{i}')
    assert verify(client, '9711', ip='10.6.0.1').status_code == 429


def test_uspesne_pokusy_limit_podle_jmena_nespotrebuji(client, db):
    for i in range(30):
        assert verify(client, '9711', ip=f'10.7.0.{i}').get_json()['success'] is True
    assert ba._name_failed_attempts.get(NAME.lower()) is None


def test_limit_podle_jmena_vyprsi_po_hodine(client, db, monkeypatch):
    now = [1_000_000.0]
    monkeypatch.setattr(ba.time, 'time', lambda: now[0])
    for i in range(20):
        change(client, '0000', '2468', ip=f'10.8.0.{i}')
    assert verify(client, '9711', ip='10.8.1.1').status_code == 429
    now[0] += ba.NAME_FAIL_WINDOW_SECONDS + 1
    assert verify(client, '9711', ip='10.8.1.1').get_json()['success'] is True


def test_cisteni_starych_zaznamu(db, monkeypatch):
    now = [1_000_000.0]
    monkeypatch.setattr(ba.time, 'time', lambda: now[0])
    ba._rate_limit_attempts[('stara', '1.1.1.1')].append(now[0])
    ba.record_failed_attempt('Stará')
    now[0] += ba.NAME_FAIL_WINDOW_SECONDS + 1
    ba._prune_rate_limits(now[0])
    assert not ba._rate_limit_attempts
    assert not ba._name_failed_attempts
