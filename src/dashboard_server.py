import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_store import fetch_teams
from src.dispatch_dashboard import build_dispatch_plan
from src.priority_route_integration import build_priority_route, load_ranked_requests, main as refresh_priority_route

RESULTS_DIR = ROOT / "results"


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=str(RESULTS_DIR), **kwargs):
        super().__init__(*args, directory=str(RESULTS_DIR), **kwargs)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/requests":
            self._send_json({"requests": load_ranked_requests()})
            return

        if parsed.path == "/api/teams":
            self._send_json({"teams": fetch_teams()})
            return

        if parsed.path == "/api/dispatch":
            self._send_json({"assignments": build_dispatch_plan(), "teams": fetch_teams()})
            return

        if parsed.path == "/api/refresh":
            refresh_priority_route()
            self._send_json({
                "status": "ok",
                "requests": load_ranked_requests(),
                "assignments": build_dispatch_plan(),
                "teams": fetch_teams(),
            })
            return

        if parsed.path in {"/", "/index.html", "/priority_dashboard.html"}:
            self.path = "/priority_dashboard.html"

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length)
            data = json.loads(payload.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid request JSON")
            return

        if parsed.path == "/api/requests":
            try:
                request = {
                    "id": data.get("id") or f"REQ-{len(load_ranked_requests()) + 1:03d}",
                    "reporter": data.get("reporter", "Saha koordinasyonu"),
                    "latitude": float(data.get("latitude", 0) or 0),
                    "longitude": float(data.get("longitude", 0) or 0),
                    "people_affected": int(data.get("people_affected", 0) or 0),
                    "injured_people": int(data.get("injured_people", 0) or 0),
                    "urgency": int(data.get("urgency", 0) or 0),
                    "needs": data.get("needs", []) or [],
                    "status": data.get("status", "waiting"),
                    "message": data.get("message", ""),
                }
                if isinstance(request["needs"], str):
                    request["needs"] = [item.strip() for item in request["needs"].split(",") if item.strip()]
                from src.data_store import save_request
                save_request(request)
                self._send_json({"status": "ok", "request": request, "requests": load_ranked_requests()})
                return
            except (TypeError, ValueError) as exc:
                self.send_error(400, f"Invalid request payload: {exc}")
                return

        if parsed.path == "/api/requests/status":
            try:
                request_id = data.get("request_id")
                status = data.get("status", "waiting")
                from src.data_store import update_request_status
                update_request_status(request_id, status)
                self._send_json({"status": "ok", "requests": load_ranked_requests()})
                return
            except Exception as exc:  # pragma: no cover - network-layer safety
                self.send_error(400, f"Invalid request status payload: {exc}")
                return

        if parsed.path == "/api/teams/status":
            try:
                team_id = data.get("team_id")
                status = data.get("status", "ready")
                from src.data_store import update_team_status
                update_team_status(team_id, status)
                self._send_json({"status": "ok", "teams": fetch_teams()})
                return
            except Exception as exc:  # pragma: no cover - network-layer safety
                self.send_error(400, f"Invalid team status payload: {exc}")
                return

        if parsed.path != "/api/route":
            self.send_error(404, "Endpoint not found")
            return

        request_id = data.get("request_id")
        requests = load_ranked_requests()
        request = next((item for item in requests if item["id"] == request_id), requests[0] if requests else None)

        if request is None:
            self.send_error(404, "No request found")
            return

        try:
            destination_lat = float(data.get("destination_lat", 37.09))
            destination_lon = float(data.get("destination_lon", 37.35))
            route = build_priority_route(
                float(request.get("longitude", destination_lon)),
                float(request.get("latitude", destination_lat)),
                destination_lon,
                destination_lat,
            )
        except (TypeError, ValueError) as exc:
            self.send_error(400, f"Invalid coordinates: {exc}")
            return

        self._send_json({"request": request, "route": route})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), DashboardHandler)
    print("AI-DLRC dashboard running on http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
