"""Autoprueba local del instrumento HTTP; NO es prueba de HardWareHouse."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from hwh_http_smoke import run

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/detalle/'):
            self.send_response(404)
        else:
            self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'<html><body>QA local mock</body></html>')
    def log_message(self, *args):
        pass

if __name__ == '__main__':
    srv=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=srv.serve_forever,daemon=True);thread.start()
    try:
        result=run(f'http://127.0.0.1:{srv.server_port}',delay=1,timeout=2)
        assert len(result['resultados'])==8
        assert all(r['status_http'] in (200,404) for r in result['resultados'])
        assert result['resultados'][-1]['status_http']==404
        print('AUTOPRUEBA DEL INSTRUMENTO: 8/8 respuestas simuladas coherentes. No corresponde a producción.')
    finally:
        srv.shutdown();srv.server_close()
