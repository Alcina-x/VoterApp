from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_has_required_dataset_size():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['synthetic_records'] == 25000

def test_voter_lookup_is_deterministic():
    response = client.get('/api/voters/VOTER001000')
    assert response.status_code == 200
    assert response.json()['voter_id'] == 'VOTER001000'

def test_chat_uses_station_tool():
    response = client.post('/api/chat', json={'message': 'How is PS-014 performing?'})
    assert response.status_code == 200
    assert response.json()['tool_used'] == 'get_station_statistics'

def test_invalid_voter_does_not_invent_record():
    response = client.post('/api/chat', json={'message': 'Check VOTER999999'})
    assert response.status_code == 200
    assert response.json()['data'] is None
