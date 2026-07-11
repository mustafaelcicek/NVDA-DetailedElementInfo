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
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
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
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/update':
            global latest_dom_data
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body)
                    latest_dom_data = data
                except json.JSONDecodeError:
                    logger.error("Geçersiz JSON verisi alındı.")
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server():
    server_address = ('127.0.0.1', 63333)
    httpd = ThreadingHTTPServer(server_address, BridgeRequestHandler)
    logger.info("HTTP Long-Polling sunucusu 127.0.0.1:63333 adresinde başlatıldı.")
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
        return "Henüz Chrome eklentisinden herhangi bir DOM verisi alınmadı."
    
    from . import ai_handler
    dom_text = json.dumps(latest_dom_data, indent=2, ensure_ascii=False)
    return ai_handler.analyze_dom_with_gemini(dom_text)

if __name__ == "__main__":
    run_server()
