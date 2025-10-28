from fastapi.testclient import TestClient
from src.api.conway_server import app

def test_root_endpoint():
    """Test that root endpoint returns HTML placeholder"""
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard not found" in response.text  # Since no dashboard.html

def test_websocket_endpoint_exists():
    """Test that WebSocket route is configured (basic test)"""
    # FastAPI app has websocket routes, this is more of a structure check
    routes = [route for route in app.routes]
    ws_routes = [route for route in routes if hasattr(route, 'endpoint') and 'websocket' in str(route.endpoint).lower()]
    assert len(ws_routes) > 0
