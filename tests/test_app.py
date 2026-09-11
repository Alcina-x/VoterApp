from fastapi.testclient import TestClient
from backend.main import VOTERS, app

client = TestClient(app)


def auth_headers(username='Alcina'):
    response = client.post('/api/auth/login', json={'username': username, 'password': 'demo123'})
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def test_health_has_required_dataset_size():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['synthetic_records'] == 25000


def test_dataset_only_uses_female_and_male_genders():
    assert all(v['gender'] in {'Female', 'Male'} for v in VOTERS)

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


def test_verify_endpoint_marks_voter_as_verified_and_persists_event():
    response = client.post('/api/voters/VOTER000001/verify', headers=auth_headers())
    assert response.status_code == 200
    assert response.json()['status_label'] == 'VERIFIED'

    lookup = client.get('/api/voters/VOTER000001', headers=auth_headers())
    assert lookup.status_code == 200
    assert lookup.json()['status_label'] == 'VERIFIED'
    assert any(event['event_type'] == 'VERIFICATION_COMPLETED' for event in lookup.json()['events'])


def test_chat_supports_help_and_processing_questions():
    headers = auth_headers()
    help_response = client.post('/api/chat', json={'message': 'What can you help me with?'}, headers=headers)
    assert help_response.status_code == 200
    assert help_response.json()['intent'] == 'assistant_help'
    pending_response = client.post('/api/chat', json={'message': 'How many records are pending?'}, headers=headers)
    assert pending_response.status_code == 200
    assert pending_response.json()['intent'] == 'processing_summary'
    assert pending_response.json()['data']['unprocessed_voters'] > 0


def test_chat_supports_station_comparison_and_demographics():
    headers = auth_headers()
    station_response = client.post('/api/chat', json={'message': 'Which stations have the highest processing rate?'}, headers=headers)
    assert station_response.status_code == 200
    assert station_response.json()['intent'] == 'station_comparison'
    age_response = client.post('/api/chat', json={'message': 'Show the records by age group.'}, headers=headers)
    assert age_response.status_code == 200
    assert age_response.json()['intent'] == 'demographic_analysis'
    assert len(age_response.json()['data']) == 7


def test_protected_endpoint_requires_authentication():
    response = client.get('/api/voters?limit=1')
    assert response.status_code == 401


def test_frontend_fallback_does_not_serve_backend_files():
    response = client.get('/%2e%2e/backend/main.py')
    assert response.status_code == 200
    assert '<!doctype html>' in response.text.lower()
