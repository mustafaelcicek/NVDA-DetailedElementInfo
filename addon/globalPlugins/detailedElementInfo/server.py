import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

latest_dom_data = {}

poll_event = threading.Event()
target_info_cache = None

class BridgeRequestHandler(BaseHTTPRequestHandler):
    def _originIsAllowed(self):
        origin = self.headers.get('Origin')
        return not origin or origin.startswith('chrome-extension://')

    def _sendCorsHeaders(self):
        origin = self.headers.get('Origin')
        if origin and origin.startswith('chrome-extension://'):
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        if self.headers.get('Access-Control-Request-Private-Network') == 'true':
            self.send_header('Access-Control-Allow-Private-Network', 'true')

    def _rejectDisallowedOrigin(self):
        if self._originIsAllowed():
            return False
        self.send_response(403)
        self.end_headers()
        return True

    def do_OPTIONS(self):
        if self._rejectDisallowedOrigin():
            return
        self.send_response(200)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self._sendCorsHeaders()
        self.end_headers()

    def do_GET(self):
        if self._rejectDisallowedOrigin():
            return
        if self.path == '/poll':
            event_triggered = poll_event.wait(timeout=10.0)
            
            response_data = {"action": "none"}
            if event_triggered:
                response_data["action"] = "get_dom"
                if target_info_cache:
                    response_data["target"] = target_info_cache
                poll_event.clear() 
                
            try:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._sendCorsHeaders()
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self._rejectDisallowedOrigin():
            return
        if self.path == '/update':
            global latest_dom_data
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body)
                    latest_dom_data = data
                except json.JSONDecodeError:
                    logger.error("Received invalid JSON data.")
            
            self.send_response(200)
            self._sendCorsHeaders()
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server():
    server_address = ('127.0.0.1', 63333)
    httpd = ThreadingHTTPServer(server_address, BridgeRequestHandler)
    logger.info("HTTP long-polling server started at 127.0.0.1:63333.")
    httpd.serve_forever()

def start_server_in_background():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

def get_latest_dom_data():
    return latest_dom_data

def request_dom_data_from_clients(target_info=None):
    global target_info_cache
    target_info_cache = target_info
    poll_event.set()

def get_ai_analysis():
    if not latest_dom_data:
        return _("No DOM data has been received from the Chrome extension yet.")
    
    from . import ai_handler
    dom_text = json.dumps(latest_dom_data, indent=2, ensure_ascii=False)
    return ai_handler.analyze_dom_with_gemini(dom_text)

if __name__ == "__main__":
    run_server()
