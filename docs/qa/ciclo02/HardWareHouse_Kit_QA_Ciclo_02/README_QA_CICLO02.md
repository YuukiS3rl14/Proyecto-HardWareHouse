# HardWareHouse — Kit QA Ciclo 02 · 20 de noviembre de 2026

## Estado de las evidencias

**La suite funcional completa NO se ha ejecutado sobre la aplicación.**
Se registró una observación pública de Inicio y Contacto mediante consulta web y una inspección parcial del código conectado a GitHub. No se verificaron pagos, permisos, ORM en ejecución, seguridad activa, formularios enviados ni carga. El dominio Railway no fue recuperable desde las herramientas de consulta de esta sesión, lo cual **no prueba una caída del servicio**.

El instrumento HTTP se comprobó con un servidor local simulado (8/8 simulaciones), que no debe confundirse con resultados de HardWareHouse.

## Archivos incluidos

- `HardWareHouse_QA_Ciclo_02_Informe_y_Resultados.docx`: plan, observaciones y clasificación.
- `HardWareHouse_QA_Ciclo_02_Matriz_de_Pruebas.docx`: 78 casos con entradas, criterios y espacios de evidencia.
- `HardWareHouse_QA_Ciclo_02_Guia_Cursor_y_Ejecucion.docx`: comandos, orden de aplicación y acta de cierre.
- `scripts/hwh_http_smoke.py`: consulta HTTP de sólo lectura, con modo previsualización.
- `scripts/hwh_ui_responsive.py`: inspección no destructiva de viewports y screenshots con Playwright.
- `scripts/locustfile_hwh.py`: escenario Locust sólo GET, recomendación staging.
- `scripts/test_smoke_script.py`: autoprueba LOCAL del instrumento HTTP.

## Orden recomendado

1. Revisar los tres documentos y confirmar ambiente; anotar SHA y Deployment ID.
2. Desde Cursor, preparar la BD de test aislada; ejecutar `python manage.py check --deploy` y `python manage.py test --verbosity 2` con mocks externos.
3. Para ver las rutas antes de hacer solicitudes:
   `python scripts/hwh_http_smoke.py --base-url https://proyecto-hardwarehouse-production.up.railway.app/`
4. Sólo tras autorizar la comprobación leve de producción:
   `python scripts/hwh_http_smoke.py --base-url https://proyecto-hardwarehouse-production.up.railway.app/ --run --allow-production --delay 2 --output evidencias/humo.json`
5. Para la UI:
   - `pip install playwright`
   - `python -m playwright install chromium`
   - `python scripts/hwh_ui_responsive.py --base-url https://STAGING_APROBADO --run --output evidencias/ui.json`
   - Acompañar con revisión manual WCAG 2.2 AA (teclado, foco, contrastes, mensajes).
6. Carga SOLO sobre staging, desde una máquina de pruebas autorizada:
   - `pip install locust`
   - `locust -f scripts/locustfile_hwh.py --headless --host https://STAGING_APROBADO --users 1 --spawn-rate 1 --run-time 60s --csv evidencias/locust_baseline`
   - Analizar latencias p50/p95, errores, CPU/RAM y RPS. Ampliar sólo tras evaluar la etapa anterior.
7. Documentar todo resultado observado. Corregir en lotes, desplegar y reejecutar regresión.

## Advertencias operativas

- **Nunca conectar tests de Django a la BD PostgreSQL de producción.** Las pruebas pueden crear/borrar tablas de test.
- Los endpoints de checkout, carrito, contacto y chatbot NO se invocan con POST en las pruebas externas del kit.
- Una prueba de estrés significativa requiere entorno staging, autorización, monitoreo y criterio de parada.
- No incorporar secretos reales, claves de PayPal ni credenciales en logs, capturas o documentos.
- No presentar una observación estática o un test del script como resultado de aceptación de HardWareHouse.

## Base de referencia

Documento previo: `HardWareHouse_Registro_QA_Ciclo_01_Formato_Academico.docx` (2026-10-30).
Técnicas: Django `TestCase` y `assertNumQueries`, WCAG 2.2, OWASP ASVS 5.0 y Locust.
