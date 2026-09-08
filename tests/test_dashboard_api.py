import json
import threading
import urllib.request
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.dashboard_server import DashboardHandler


def start_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def request_json(server, path, method="GET", payload=None):
    url = f"http://127.0.0.1:{server.server_port}{path}"
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_dashboard_read_endpoints_return_operational_data():
    server, thread = start_server()
    try:
        status, requests_payload = request_json(server, "/api/requests")
        assert status == 200
        assert "requests" in requests_payload

        status, teams_payload = request_json(server, "/api/teams")
        assert status == 200
        assert teams_payload["teams"]
        assert {"id", "status"}.issubset(teams_payload["teams"][0])

        status, dispatch_payload = request_json(server, "/api/dispatch")
        assert status == 200
        assert "assignments" in dispatch_payload
        assert "teams" in dispatch_payload
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_dashboard_can_create_request():
    server, thread = start_server()
    request_id = f"REQ-API-{uuid.uuid4().hex[:8]}"
    try:
        status, payload = request_json(
            server,
            "/api/requests",
            method="POST",
            payload={
                "id": request_id,
                "reporter": "Dashboard test",
                "latitude": 37.1,
                "longitude": 37.3,
                "people_affected": 4,
                "injured_people": 1,
                "urgency": 5,
                "needs": "medical, water",
            },
        )

        assert status == 200
        assert payload["request"]["id"] == request_id
        created = next(item for item in payload["requests"] if item["id"] == request_id)
        assert created["needs"] == ["medical", "water"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
