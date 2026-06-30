"""
UI Server - A lightweight HTTP server to serve the static frontend and REST APIs.
"""
import http.server
import json
import logging
import os
import sys
import socketserver
from typing import Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.main import run_etl

logger = logging.getLogger("ui_server")
logging.basicConfig(level=logging.INFO)

PORT = 8000
STATIC_DIR = os.path.join(PROJECT_ROOT, "src", "static")
os.makedirs(STATIC_DIR, exist_ok=True)


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """
    HTTP Request Handler that serves UI files and provides simple REST endpoints.
    """

    def __init__(self, *args, **kwargs):
        # Override the directory to point to our static folder
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        # API: get list of processed candidates
        if self.path == "/api/candidates":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            output_file = os.path.join(PROJECT_ROOT, "output", "candidates_output.json")
            if os.path.exists(output_file):
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.wfile.write(json.dumps(data).encode("utf-8"))
                except Exception as e:
                    self.wfile.write(json.dumps({"error": f"Failed to read data: {str(e)}"}).encode("utf-8"))
            else:
                self.wfile.write(json.dumps([]).encode("utf-8"))
            return

        # Fallback to serving static files
        super().do_GET()

    def do_POST(self):
        # API: Trigger ETL pipeline run
        if self.path == "/api/run-etl":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            try:
                logger.info("Executing ETL pipeline via UI request...")
                run_etl()
                self.wfile.write(json.dumps({"status": "success", "message": "Pipeline completed successfully!"}).encode("utf-8"))
            except Exception as e:
                logger.error("Failed running ETL pipeline: %s", e)
                self.send_error(500, f"ETL Pipeline Error: {str(e)}")
            return
        
        self.send_error(404, "Endpoint not found")


def start_server():
    """Starts the UI server."""
    # Ensure index.html exists, if not raise warning (it will be created next)
    index_path = os.path.join(STATIC_DIR, "index.html")
    logger.info("Serving UI from: %s", STATIC_DIR)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        logger.info("Dashboard Server running at: http://localhost:%d/", PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Stopping dashboard server...")
            httpd.shutdown()


if __name__ == "__main__":
    start_server()
