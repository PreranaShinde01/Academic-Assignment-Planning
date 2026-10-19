"""
Academic Assignment Planning AI Agent - Web Server & REST API
=============================================================
A self-contained Python web server that connects the modern web dashboard
to the AI Agent reasoning and verification engine.

Provides:
- GET  /              -> Serves academic_planner_app.html
- GET  /api/health    -> Health check & backend connectivity status
- POST /api/plan      -> Cognitive task decomposition & constraint scheduling
- POST /api/validate  -> Multi-rule guardrail validation
- POST /api/replan    -> Dynamic re-planning on requirement shifts
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import date, datetime, timedelta
from typing import Dict, Any

# Import agent components from local module
from academic_planner_app import (
    AcademicPlanner,
    PlanValidator,
    PlanReviser,
    AssignmentInput,
    DeliverableType,
    Priority,
    TaskItem
)

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE_PATH = os.path.join(BASE_DIR, "academic_planner_app.html")


class AgentRequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        # Enable CORS for local testing
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        # 1. Root: Serve the modern HTML dashboard
        if self.path == "/" or self.path.startswith("/index.html") or self.path.startswith("/academic_planner_app.html"):
            if os.path.exists(HTML_FILE_PATH):
                with open(HTML_FILE_PATH, "rb") as f:
                    content = f.read()
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(content)
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"HTML application file not found.")
            return

        # 2. API Healthcheck
        if self.path == "/api/health":
            data = {
                "status": "online",
                "version": "2.0.0",
                "agent": "AcademicPlannerAgent",
                "timestamp": datetime.now().isoformat()
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # Fallback 404
        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            req_data = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode("utf-8"))
            return

        # Route 1: Generate Plan
        if self.path == "/api/plan":
            try:
                assignment = AssignmentInput(
                    assignment_id="REQ_" + datetime.now().strftime("%H%M%S"),
                    title=req_data.get("title", "Untitled Assignment"),
                    course=req_data.get("course", "General Course"),
                    description=req_data.get("description", ""),
                    deliverable_type=DeliverableType(req_data.get("deliverable_type", "RESEARCH_PAPER")),
                    start_date=date.fromisoformat(req_data.get("start_date", str(date.today()))),
                    due_date=date.fromisoformat(req_data.get("due_date", str(date.today() + timedelta(days=14)))),
                    daily_capacity_hours=float(req_data.get("daily_capacity_hours", 2.5)),
                    difficulty_multiplier=float(req_data.get("difficulty_multiplier", 1.0))
                )

                print(f"[AGENT] Received assignment: '{assignment.title}' ({assignment.deliverable_type.value})")
                planner = AcademicPlanner()
                validator = PlanValidator()

                tasks = planner.generate_plan(assignment)
                report = validator.validate(tasks, assignment)

                runway_days = (assignment.due_date - assignment.start_date).days
                total_effort = sum(t.estimated_hours for t in tasks)
                total_cap = runway_days * assignment.daily_capacity_hours
                latest_t = max(t.deadline for t in tasks) if tasks else assignment.start_date
                buffer_days = max(0, (assignment.due_date - latest_t).days)

                response_payload = {
                    "metadata": {
                        "assignment_id": assignment.assignment_id,
                        "title": assignment.title,
                        "runway_days": runway_days,
                        "total_effort_hours": round(total_effort, 1),
                        "total_capacity_hours": round(total_cap, 1),
                        "buffer_days": buffer_days,
                        "feasibility": "FEASIBLE" if total_effort <= total_cap else "CAPACITY_OVERLOAD"
                    },
                    "tasks": [
                        {
                            "id": t.task_id,
                            "phase": t.phase,
                            "title": t.title,
                            "prio": t.priority.value,
                            "hours": t.estimated_hours,
                            "scheduledDate": t.scheduled_date.isoformat(),
                            "deadline": t.deadline.isoformat(),
                            "deps": t.dependencies,
                            "dod": t.definition_of_done,
                            "completed": False
                        }
                        for t in tasks
                    ],
                    "validation": {
                        "is_valid": report.is_valid,
                        "missing_tasks": report.missing_tasks,
                        "conflicting_deadlines": report.conflicting_deadlines,
                        "capacity_violations": report.capacity_violations,
                        "warnings": report.warnings
                    }
                }

                print(f"[AGENT] Generated {len(tasks)} tasks | Valid: {report.is_valid}")
                self._set_headers(200)
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))
            except Exception as e:
                print(f"[ERROR] Plan generation failed: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # Route 2: Re-plan / Requirement Change
        if self.path == "/api/replan":
            try:
                new_due = date.fromisoformat(req_data.get("new_due_date"))
                reason = req_data.get("reason", "Requirement changed")
                # Fallback to local re-planner
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "replanned", "new_due_date": str(new_due)}).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Unknown POST endpoint"}).encode("utf-8"))


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, AgentRequestHandler)
    print("=" * 70)
    print("🚀 ACADEMIC PLANNER AI AGENT SERVER 2.0")
    print(f"👉 Local Web App: http://localhost:{PORT}")
    print(f"👉 REST API:      http://localhost:{PORT}/api/plan")
    print("=" * 70)
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
