from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def auth_headers(username='Alcina'):
    response = client.post('/api/auth/login', json={'username': username, 'password': 'demo123'})
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def test_health_has_required_dataset_size():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['synthetic_records'] == 25000

def test_login_accepts_demo_officer():
    response = client.post('/api/auth/login', json={'username': 'Alcina', 'password': 'demo123'})
    assert response.status_code == 200
    assert response.json()['user']['role'] == 'Simulated Polling Officer'

def test_login_accepts_all_demo_officers():
    for username in ('Alcina', 'Akshaya', 'Ajay'):
        response = client.post('/api/auth/login', json={'username': username, 'password': 'demo123'})
        assert response.status_code == 200
        assert response.json()['user']['username'] == username

def test_login_accepts_case_variation_for_alcina():
    response = client.post('/api/auth/login', json={'username': 'Alcina', 'password': 'demo123'})
    assert response.status_code == 200
    assert response.json()['user']['username'] == 'Alcina'

def test_login_rejects_invalid_password():
    response = client.post('/api/auth/login', json={'username': 'Alcina', 'password': 'wrong'})
    assert response.status_code == 401

def test_voter_lookup_is_deterministic():
    response = client.get('/api/voters/VOTER001000', headers=auth_headers())
    assert response.status_code == 200
    assert response.json()['voter_id'] == 'VOTER001000'

def test_chat_uses_station_tool():
    response = client.post('/api/chat', json={'message': 'How is PS-014 performing?'}, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()['tool_used'] == 'get_station_statistics'

def test_invalid_voter_does_not_invent_record():
    response = client.post('/api/chat', json={'message': 'Check VOTER999999'}, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()['data'] is None


def test_protected_endpoint_requires_authentication():
    response = client.get('/api/voters?limit=1')
    assert response.status_code == 401


def test_frontend_fallback_does_not_serve_backend_files():
    response = client.get('/%2e%2e/backend/main.py')
    assert response.status_code == 200
    assert '<!doctype html>' in response.text.lower()
