#!/usr/bin/env python3
"""HardWareHouse - verificación HTTP superficial, de solo lectura.

No prueba formularios, pagos ni permisos. Debe ejecutarse solo con autorización
sobre el ambiente correcto; nunca envía POST ni credenciales.
"""
from __future__ import annotations
import argparse
import json
import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROUTES = [
    ('HW-SM-01', '/', 'Inicio'),
    ('HW-SM-02', '/tienda/', 'Tienda'),
    ('HW-SM-03', '/armado/', 'Armado de PC'),
    ('HW-SM-04', '/sobre-nosotros/', 'Sobre nosotros'),
    ('HW-SM-05', '/contacto/', 'Contacto'),
    ('HW-SM-06', '/registro/', 'Registro'),
    ('HW-SM-07', '/login/', 'Login'),
    ('HW-SM-08', '/detalle/procesador/999999999/', '404 de producto inexistente'),
]
PROD_HOSTS = {'proyecto-hardwarehouse-production.up.railway.app', 'hardwarehouse.cl', 'www.hardwarehouse.cl'}


def run(base_url, *, allow_production=False, delay=1.5, timeout=10, case_ids=None):
    base_url = base_url.rstrip('/')
    parsed = urlsplit(base_url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('Debe indicar una URL http(s) válida mediante --base-url')
    if parsed.hostname in PROD_HOSTS and not allow_production:
        raise ValueError('Se detectó producción. Se requiere --allow-production para cualquier sondeo.')
    rows = []
    selected = [x for x in ROUTES if not case_ids or x[0] in case_ids]
    for i, (case_id, path, title) in enumerate(selected):
        if i:
            time.sleep(delay)
        url = base_url + path
        start = time.perf_counter()
        status = None
        redirect = ''
        error = ''
        length = 0
        hdr = {}
        try:
            req = Request(url, method='GET', headers={'User-Agent': 'HWH-QA-readonly/1.0', 'Accept': 'text/html'})
            try:
                resp = urlopen(req, timeout=timeout)
            except HTTPError as exc:
                resp = exc
            with resp:
                status = resp.status
                redirect = resp.url if resp.url != url else ''
                body = resp.read(256*1024)  # máximo de 256 KiB por página
                length = len(body)
                for key in ('Content-Type','Strict-Transport-Security','X-Content-Type-Options','X-Frame-Options','Content-Security-Policy'):
                    if resp.headers.get(key):
                        hdr[key] = resp.headers[key][:300]
        except (URLError, TimeoutError, OSError) as exc:
            error = type(exc).__name__ + ': ' + str(exc)[:150]
        elapsed_ms = round((time.perf_counter()-start)*1000, 1)
        expected = '404' if case_id == 'HW-SM-08' else '200 o redirección esperada (sin 5xx)'
        outcome = ('NO_EJECUTABLE' if status is None else 'FALLIDA' if status >= 500 else 'OBSERVADA' if ((case_id == 'HW-SM-08' and status == 404) or (case_id != 'HW-SM-08' and 200 <= status < 400)) else 'REVISAR')
        rows.append({'id':case_id,'titulo':title,'path':path,'status_http':status,'tiempo_ms':elapsed_ms,'bytes_leidos':length,'url_final':redirect,'esperado':expected,'estado':outcome,'error':error,'cabeceras':hdr})
    return {'fecha_utc':datetime.now(timezone.utc).isoformat(),'base_url':base_url,'ambito':'HTTP GET, sin autenticación, sin cambios en la aplicación','resultados':rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url', required=True)
    p.add_argument('--allow-production', action='store_true', help='Autorización explícita para sondeos leves de solo lectura en producción')
    p.add_argument('--run', action='store_true', help='Sin --run no se envían solicitudes')
    p.add_argument('--delay', type=float, default=1.5)
    p.add_argument('--timeout', type=float, default=10)
    p.add_argument('--output', default='evidencias/smoke_http.json')
    p.add_argument('--case-id', action='append', dest='ids', help='Filtrar por ID; repetible')
    args = p.parse_args()
    if not args.run:
        print('MODO PREVISUALIZACIÓN: no se han enviado solicitudes HTTP. Añade --run cuando el entorno esté aprobado.')
        for x in ROUTES:
            if not args.ids or x[0] in args.ids:
                print(*x, sep=' | ')
        return
    if args.delay < 1:
        p.error('El retardo mínimo permitido por este script es 1 segundo.')
    result = run(args.base_url, allow_production=args.allow_production, delay=args.delay, timeout=args.timeout, case_ids=args.ids)
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    csvpath=dest.with_suffix('.csv')
    with csvpath.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=['id','titulo','path','status_http','tiempo_ms','bytes_leidos','esperado','estado','error'])
        writer.writeheader(); writer.writerows([{k:x[k] for k in writer.fieldnames} for x in result['resultados']])
    for row in result['resultados']:
        print(f"{row['id']} {row['titulo']}: HTTP {row['status_http']} | {row['tiempo_ms']}ms | {row['estado']}")
    print('Evidencia:',dest,'y',csvpath)

if __name__ == '__main__':
    main()
