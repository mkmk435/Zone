import json, subprocess, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

mock = open("tmp/mock_eq.txt", encoding="utf-8").read()

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = json.dumps({
            "choices": [{"message": {"content": mock}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args): pass

server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    env = dict(__import__("os").environ, DEEPSEEK_API_KEY="test-key")
    command = [sys.executable, "pobf.py",
               "original_pl\\x64\\windows_x64_messagebox.bin",
               "--llm", "-eq",
               "--llm-base-url", f"http://127.0.0.1:{server.server_port}/v1",
               "--llm-model", "test-model",
               "--llm-verify", "messagebox",
               "-o", "tmp\\http_e2e.bin"]
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    print(result.stdout)
    print("RC", result.returncode)
finally:
    server.shutdown(); server.server_close(); thread.join(timeout=2)

