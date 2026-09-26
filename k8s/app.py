"""Soru öneri servisi için basit bir model sunucusu taslağı.

Model ağırlıkları yüklenirken servis ayağa kalkar ama istek alamaz;
yükleme bitince /healthz ve /ready uçları 200 döner.
"""
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STARTUP_SECONDS = int(os.getenv("STARTUP_SECONDS", "25"))
state = {"model_loaded": False}


def load_model():
    print(f"model yükleniyor... (~{STARTUP_SECONDS} sn)", flush=True)
    time.sleep(STARTUP_SECONDS)  # ağırlıkların belleğe alınmasını temsil ediyor
    state["model_loaded"] = True
    print("model hazır", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/healthz", "/ready"):
            ok = state["model_loaded"]
            self.send_response(200 if ok else 503)
            self.end_headers()
            self.wfile.write(b"ok" if ok else b"loading")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def handle_sigterm(signum, frame):
    # Konteynerde PID 1 olarak çalışıyoruz: işleyicisi olmayan SIGTERM çekirdek
    # tarafından yok sayılıyor ve kubelet 30 sn bekleyip SIGKILL gönderiyordu.
    print("SIGTERM alındı, kapanıyor", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    threading.Thread(target=load_model, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
