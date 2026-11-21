#!/usr/bin/env python3
"""Prueba automatizada NO DESTRUCTIVA de páginas públicas (Playwright).

Requiere: pip install playwright && python -m playwright install chromium
No completa formularios, no inicia sesión, no envía pagos/correos.
No certifica WCAG; complementa revisión manual.
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

URLS=[('/', 'inicio'),('/tienda/', 'tienda'),('/armado/', 'armado'),('/contacto/', 'contacto')]
VIEWPORTS=[(320,568),(375,812),(768,1024),(1366,768),(1920,1080)]
PROD={'proyecto-hardwarehouse-production.up.railway.app','hardwarehouse.cl','www.hardwarehouse.cl'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url',required=True)
    p.add_argument('--run',action='store_true')
    p.add_argument('--allow-production',action='store_true')
    p.add_argument('--output',default='evidencias/ui_responsive.json')
    args=p.parse_args()
    base=args.base_url.rstrip('/')
    u=urlsplit(base)
    if u.scheme not in ('http','https') or not u.hostname:
        p.error('Se requiere una URL http(s) válida')
    if u.hostname in PROD and not args.allow_production:
        p.error('Protección para producción: añadir --allow-production después de aprobación de la prueba')
    if not args.run:
        print('PREVIEW: no se efectuaron conexiones. URL:',base)
        print('Rutas:',[x[0] for x in URLS]);print('Viewports:',VIEWPORTS)
        return
    from playwright.sync_api import sync_playwright
    report={'fecha_utc':datetime.now(timezone.utc).isoformat(),'base':base,'resultados':[],'limitacion':'No certifica WCAG ni pruebas de roles, pagos o formularios POST.'}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        try:
            for width,height in VIEWPORTS:
                page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
                for route, name in URLS:
                    rec={'ruta':route,'pantalla':f'{width}x{height}'}
                    try:
                        resp=page.goto(base+route,wait_until='domcontentloaded',timeout=15000)
                        page.wait_for_timeout(350)
                        diag=page.evaluate('''() => ({scrollWidth:document.documentElement.scrollWidth, viewport:innerWidth, imgsSinAlt:document.querySelectorAll('img:not([alt])').length, camposSinNombre:[...document.querySelectorAll('input:not([type="hidden"]), textarea, select')].filter(x=>!x.getAttribute('aria-label') && !x.getAttribute('aria-labelledby') && !(x.id && document.querySelector('label[for="'+x.id+'"]')) && !x.closest('label')).length})''')
                        rec.update(diag)
                        rec['http']=resp.status if resp else None
                        rec['overflow_horizontal']=diag['scrollWidth']>diag['viewport']+2
                        img=out.parent/f'ui_{name}_{width}x{height}.png'
                        page.screenshot(path=str(img),full_page=True)
                        rec['captura']=str(img)
                    except Exception as e:
                        rec['error']=type(e).__name__+': '+str(e)[:200]
                    report['resultados'].append(rec)
                    time.sleep(.4)
                page.close()
        finally:browser.close()
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generado:',out,'registros:',len(report['resultados']))
if __name__=='__main__':main()
