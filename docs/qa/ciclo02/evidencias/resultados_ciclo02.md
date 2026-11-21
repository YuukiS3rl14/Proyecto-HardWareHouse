# HardWareHouse — Anexo de ejecución Ciclo 02

Fecha UTC: 2026-11-20T20:06:28Z a 2026-11-20T20:09:49Z (suite) y reejecución de concurrencia a continuación.
Commit: `957b4bdae2dd881531158b81dc5557b98d1c28cd` (rama `main`).
Railway Deployment ID: no identificado. No se consultó el panel ni la URL de producción.
Python 3.13.7 · Django 4.2.25 · PostgreSQL 18.0 en `127.0.0.1:5432`, base de desarrollo `bd_hardwarehouse`.
Base de las pruebas: `test_bd_hardwarehouse`, creada y destruida por `manage.py test`. `DATABASE_URL` se dejó vacío para no usar la URL de Railway. `USE_SQLITE=False`.
Servicios externos: `OLLAMA_BASE_URL` vacío y `HARDWAREHOUSE_CHAT_INTENT_LLM=False`. PayPal y EmailJS se ejercitaron con los mocks ya existentes. No hubo correos ni cobros reales.

Este anexo no sustituye el informe Word. Sirve para copiar estados y evidencias al informe final.

## Comandos y evidencia

| Comando | Resultado | Archivo |
| --- | --- | --- |
| `python manage.py check` | Sin incidencias | `evidencias/django/check.txt` |
| `python manage.py check --deploy` | 5 advertencias en el entorno local con `DEBUG=True` | `evidencias/django/check_deploy.txt` |
| `python manage.py test --verbosity 1` | 639 pruebas: 610 correctas, 16 fallos, 12 errores, 1 omitida. 183,7 s | `evidencias/django/manage_test.txt` |
| `ConcurrenciaMismoUsuarioTests` con `ARMADO_CONCURRENCIA_PG=1` | 1 fallo. La prueba omitida de la suite era esta. | `evidencias/django/concurrencia_ultima_unidad.txt` |
| `scripts/test_smoke_script.py` | 8/8 contra un servidor HTTP simulado | No es resultado de HardWareHouse |

`check --deploy` avisó: falta `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT` no es True, cookies de sesión y CSRF no son `Secure`, y `DEBUG=True`. En `settings.py` esas banderas HTTPS se activan con `USE_HTTPS` cuando no se está corriendo `manage.py test`. Esta corrida no demuestra cómo está el proceso de Railway. No aparece `SECURE_HSTS_SECONDS` en el código leído.

La base local de desarrollo no tiene la columna `core_procesador.stock_minimo`. Por eso no se levantó el servidor de desarrollo para Playwright: un 500 ahí sería del esquema local, no de la versión migrada que sí usa la suite (`0018`, `0019` y `0020` se aplicaron en `test_bd_hardwarehouse`).

## Cierre de esta ronda

| Estado | Casos |
| --- | ---: |
| APROBADA | 20 |
| PARCIAL | 32 |
| FALLIDA | 2 |
| PENDIENTE | 9 |
| BLOQUEADA | 15 |
| Total | 78 |

Resultado del ciclo: no aprobado. Hay una carrera de stock sin evidencia de reserva correcta y fallos del armado por chat. No hay capturas de navegador, medición ORM ni carga.

## Incidencias

| ID | Severidad | Hallazgo | Estado |
| --- | --- | --- | --- |
| QA-02-06 | P1 | `test_dos_solicitudes_simultaneas_no_superan_el_stock_ni_duplican_la_linea`: las dos peticiones respondieron 400. Se esperaba una 200 y una 400. La aserción de stock no llegó a ejecutarse, así que no se observó sobreventa ni stock negativo. | FALLIDA |
| QA-02-07 | P2 | `test_la_cantidad_previa_del_mismo_usuario_cuenta`: al aceptar la segunda unidad, `precio_unitario` pasó de 1.00 a 50000.00, el precio actual del producto. El rechazo por stock sí respondió 400. | PARCIAL |
| QA-02-08 | P1 | 15 pruebas de armado y optimización del chat devolvieron `pc_build_failed` o `clarification` donde el test esperaba un armado. 2 errores adicionales por ausencia de `proposal_pending` o `build_comparison`. | FALLIDA |
| QA-02-09 | P2 | Exportación e importación de catálogo: `No se puede importar el campo creado_en` y especificaciones que no coinciden con la familia. 10 errores en `core.test_catalogo_migracion`. Queda fuera de los 78 casos, como regresión de la suite. | FALLIDA de suite |
| QA-02-10 | P2 | `pip-audit`, Playwright y Locust no están instalados. Carga y capturas no se ejecutaron. | BLOQUEADA |
| QA-02-04 | P2 | No hay conteo de consultas ni `EXPLAIN` de tienda, detalle, carrito, favoritos, alertas ni historial. | PENDIENTE |

## Matriz ejecutada

Datos de prueba: usuarios, productos y pedidos creados dentro de `test_bd_hardwarehouse`. Precios y nombres son de fixture, no del catálogo real.

| ID | Módulo | Procedimiento ejecutado | Esperado | Obtenido | Estado | Evidencia |
| --- | --- | --- | --- | --- | --- | --- |
| UI-01 | Público | Cliente Django a inicio, tienda, armado y detalle | 200 sin 5xx | 200 en `test_estaticos_publicos` | PARCIAL | Falta captura de navegador |
| UI-02 | Catálogo | Búsqueda y término sin resultados | Coincidencias y vacío | Afirmado en `test_tienda_filtros` | PARCIAL | Sin captura |
| UI-03 | Filtros | Home a categoría o proveedor y reemplazo | Reemplazo y combinación intencional | 14 pruebas de `ReemplazoDeFiltrosTests` correctas | PARCIAL | Sin captura |
| UI-04 | Registro | Alta, inválidos y grupo Cliente | Errores y grupo Cliente | `test_grupo_cliente` correcto | APROBADA | `manage_test.txt` |
| UI-05 | Sesión | Anónimo redirige a login; cliente recibe 403 en staff | Sesión y cierre | Redirecciones y 403 afirmados; cierre de sesión en navegador no recorrido | PARCIAL | `test_alertas_stock` |
| UI-06 | Contacto | Formulario y EmailJS simulado | Validación y un solo envío | Pruebas de correo y contacto estático correctas | PARCIAL | Falta aislar el mensaje de 2001 caracteres |
| UI-07 | Teléfono | Chile y otro país | E.164 sin prefijo duplicado | `test_formularios_errores` correcto | PARCIAL | Selector visual no pulsado |
| UI-08 | Reseñas | Medias estrellas, límite y anónimo | Solo pasos válidos | Mismas pruebas correctas | PARCIAL | Widget visual no recorrido |
| UI-09 | Carrito | Agregar, tope de stock y precio de línea | Totales estables | El tope responde 400; la segunda unidad reescribe el precio a 50000 | PARCIAL | QA-02-07 |
| UI-10 | Errores | 404 genérico, 404 de producto y 500 | Plantilla segura | Afirmado con `DEBUG=False` | APROBADA | `test_formularios_errores` |
| SM-01 | Humo | GET `/` por cliente de prueba | 200 | 200 en páginas públicas | PARCIAL | El script HTTP no se apuntó a la app |
| SM-02 | Humo | GET `/tienda/` | 200 | 200 en el cliente de prueba | PARCIAL | Igual que SM-01 |
| SM-03 | Humo | GET `/armado/` | 200 | 200 en el cliente de prueba | PARCIAL | Igual que SM-01 |
| SM-04 | Humo | GET `/contacto/` | 200 | Cubierto por pruebas de contacto | PARCIAL | Igual que SM-01 |
| SM-05 | Humo | GET registro y login | Sin 5xx | Cubierto de forma indirecta | PARCIAL | Igual que SM-01 |
| SM-06 | Humo | Pedidos sin sesión | Login, sin datos | 302 a `/login/` en favoritos y pedidos de prueba | PARCIAL | Sin el script HTTP |
| SM-07 | Humo | Alertas sin sesión | Protegida | 302 a login | PARCIAL | Sin el script HTTP |
| SM-08 | Humo | Producto inexistente | 404 seguro | 404 y texto de producto no encontrado | APROBADA | `test_formularios_errores` |
| UT-01 | Compatibilidad | Socket CPU y placa | Bloquea incompatibles | `test_armado_completo` correcto | APROBADA | Suite |
| UT-02 | Compatibilidad | DDR, formato y módulos | Mensajes precisos | `test_ram` correcto | APROBADA | Suite |
| UT-03 | Compatibilidad | Largo GPU y gabinete | Rechaza exceso | `test_largo` correcto | APROBADA | Suite |
| UT-04 | Carrito | Totales y precio de línea | Sin perder el precio guardado | Formato y PayPal correctos; una línea cambió de 1.00 a 50000 | PARCIAL | QA-02-07 |
| UT-05 | Carrito | Cantidad inválida y sobre stock | Rechazo | `test_validacion_ux` y tope de armado correctos | APROBADA | Suite |
| UT-06 | Stock | Umbrales y estados | Contadores coherentes | `test_alertas_stock` correcto | APROBADA | Suite |
| UT-07 | Inventario | Reponer, ajustar, vender y rollback | Movimiento o nada | `test_movimientos_stock` correcto | APROBADA | Suite |
| UT-08 | Pagos | IPN duplicado | Un descuento | `test_paypal` correcto, sin cobro real | APROBADA | Suite |
| UT-09 | Concurrencia | Dos POST con stock 1 | Una aceptación | Dos respuestas 400 | FALLIDA | `concurrencia_ultima_unidad.txt` |
| UT-10 | Cuentas | Registro público y alta staff | Solo el público entra a Cliente | `test_grupo_cliente` correcto | APROBADA | Suite |
| UT-11 | Reseñas | Pasos 0,5 a 5,0 | Promedio decimal | `test_formularios_errores` correcto | APROBADA | Suite |
| UT-12 | Correo | Éxito, error y reintento simulados | El pago no se duplica | `test_correo_emailjs` correcto | APROBADA | Suite |
| ORM-01 | ORM | Conteos de `/tienda/` | Sin N+1 medido | No se capturaron consultas de tienda | PENDIENTE | — |
| ORM-02 | ORM | Detalle y proveedor | Sin SELECT por fila | No medido | PENDIENTE | — |
| ORM-03 | ORM | Carrito y favoritos | Conteo estable | No medido | PENDIENTE | — |
| ORM-04 | ORM | Alertas | Sin cargar el catálogo entero | No medido en esta ronda | PENDIENTE | — |
| ORM-05 | ORM | Historial | `select_related` medido | No medido | PENDIENTE | — |
| ORM-06 | ORM | EXPLAIN | Plan en base de prueba | No ejecutado | PENDIENTE | — |
| ORM-07 | ORM | `select_for_update` | Bloqueo de fila | Dos ajustes simultáneos de stock 5 terminaron en 3 | PARCIAL | No se midió la duración del bloqueo |
| ORM-08 | ORM | Context processors | Sin consultas duplicadas | No medido | PENDIENTE | — |
| AX-01 | UI | 320 y 375 px | Sin desborde | Playwright no instalado; no hay capturas | BLOQUEADA | Una aserción CSS de una columna no basta |
| AX-02 | UI | 768 px | Layout usable | No ejecutado | BLOQUEADA | — |
| AX-03 | UI | 1366 y 1920 | Sin cortes | No ejecutado | BLOQUEADA | — |
| AX-04 | UI | Teclado | Operable sin mouse | No ejecutado | BLOQUEADA | — |
| AX-05 | UI | Contraste y foco | WCAG 2.2 AA | No medido | BLOQUEADA | — |
| AX-06 | UI | Labels y aria | Campos nombrados | No recorrido con lector | BLOQUEADA | — |
| AX-07 | UI | Alt e iconos | Alternativa textual | Imágenes públicas sin placeholder en el cliente | BLOQUEADA | Falta la revisión visual |
| AX-08 | UI | Zoom 200 % | Contenido visible | No ejecutado | BLOQUEADA | — |
| PF-01 | Carga | Línea base GET | p50/p95 | Locust no instalado y no hay staging | BLOQUEADA | No se apuntó a producción |
| PF-02 | Carga | 1, 5 y 10 usuarios | Métricas por etapa | No ejecutado | BLOQUEADA | — |
| PF-03 | Carga | Estrés | Punto de saturación | No ejecutado | BLOQUEADA | — |
| PF-04 | Carga | Recuperación | Vuelta al nivel base | No ejecutado | BLOQUEADA | — |
| PF-05 | Carga | Catálogo filtrado | Tiempo estable | No ejecutado | BLOQUEADA | — |
| PF-06 | Carga | Comparación de release | Sin regresión | No hay línea base previa | BLOQUEADA | — |
| IN-01 | Integración | Registro y luego login | Sesión | El grupo se asigna; el login posterior no es un caso único | PARCIAL | `test_grupo_cliente` |
| IN-02 | Integración | Filtro, ficha y volver | URL coherente | Filtros y detalle se probaron por separado | PARCIAL | Suite |
| IN-03 | Integración | Armado compatible, carrito y Excel | Archivo válido | `test_armado_completo` y `test_excel_armado` correctos | APROBADA | Suite |
| IN-04 | Integración | Checkout Sandbox simulado | Pedido pendiente, sin cobro | `test_paypal` correcto | APROBADA | Suite |
| IN-05 | Integración | Pago confirmado | Un descuento y un movimiento | PayPal y movimientos correctos | APROBADA | Suite |
| IN-06 | Integración | Aviso de compra simulado | El fallo de correo no revierte el pago | `test_correo_emailjs` correcto | APROBADA | Suite |
| IN-07 | Integración | Contacto simulado | Destino de contacto y reply-to del visitante | Misma suite correcta | APROBADA | Suite |
| IN-08 | Integración | Umbrales de staff | Persisten; el cliente recibe 403 | `test_alertas_stock` correcto | APROBADA | Suite |
| IN-09 | Integración | Pedido de A visto por B | Sin datos privados | El chat no muestra el pedido ajeno; falta la ficha HTTP de un pedido existente | PARCIAL | `test_chatbot` |
| IN-10 | Integración | Armado del chat con Ollama apagado | Degradación controlada | Varios flujos responden `pc_build_failed` | FALLIDA | QA-02-08 |
| RG-01 | Regresión | Filtros del SHA actual | Sin acumulación | Reglas de filtro correctas en cliente Django | PARCIAL | Falta navegador |
| RG-02 | Regresión | Roles y grupo | Sin cambio no previsto | Pruebas de grupo y staff correctas | PARCIAL | Falta logout visual |
| RG-03 | Regresión | Carrito a pedido | Precios estables | PayPal conserva totales; una línea de armado reescribe el precio | PARCIAL | QA-02-07 |
| RG-04 | Regresión | Compatibilidad de armado | Validación vigente | Reglas de piezas correctas; el chat no arma | PARCIAL | QA-02-08 |
| RG-05 | Regresión | Umbrales e historial | Sin cambio funcional | Alertas y movimientos correctos | PARCIAL | Falta la pantalla |
| RG-06 | Regresión | Reseñas y contacto | Sin regresión de formulario | Pruebas de formulario correctas | PARCIAL | Falta el navegador |
| SC-01 | Seguridad | Cliente, staff y panel | 403 o login | Afirmado en alertas, movimientos y dashboard | PARCIAL | No cubre todas las vistas |
| SC-02 | Seguridad | Pedido de otro usuario | 403 o 404 sin datos | Un id inexistente da 404 genérico; falta el pedido existente de otro usuario | PARCIAL | `test_formularios_errores` |
| SC-03 | Seguridad | POST sin CSRF | 403 | Chat e interpretador lo rechazan | PARCIAL | No se probó cada POST |
| SC-04 | Seguridad | HTML en una reseña | Texto escapado | No se guardó un payload de prueba | PENDIENTE | — |
| SC-05 | Seguridad | Negativos y textos largos | Rechazo en servidor | Cantidades, reseñas y teléfono correctos | PARCIAL | — |
| SC-06 | Seguridad | DEBUG, HTTPS y cookies | Endurecido | Advertencias locales de `check --deploy`; proceso Railway no inspeccionado | PARCIAL | `check_deploy.txt` |
| SC-07 | Seguridad | `pip-audit` | Inventario CVE | Herramienta ausente | BLOQUEADA | — |
| SC-08 | Seguridad | Cabeceras HSTS, nosniff, frame, CSP | Registro real | No hubo respuesta HTTP de un servidor | PENDIENTE | — |
| SC-09 | Seguridad | Límite de contacto | Corta llamadas | El test de EmailJS lo afirma; el login no | PARCIAL | Suite |
| SC-10 | Seguridad | Excepción controlada | Sin traza al cliente | 500 con «Algo salió mal»; el token solo queda en el log | APROBADA | `test_formularios_errores` |

## Pruebas manuales que quedan

1. Recorrer en el navegador Inicio, Tienda, Armado, Sobre nosotros, Contacto, registro, login y cierre de sesión. Probar búsqueda, filtros heredados, teléfono, estrellas, carrito y favoritos. Guardar capturas.
2. Repetir esas pantallas a 320, 375, 768, 1366 y 1920 px, con Tab, Escape, foco visible, contraste y zoom 200 %.
3. Autorizar el humo GET con `hwh_http_smoke.py --run` solo sobre el ambiente acordado. La autoprueba del script no cuenta.
4. Medir consultas y `EXPLAIN` en la base de prueba para tienda, detalle, carrito, favoritos, alertas, historial y el menú.
5. Instalar `pip-audit` y registrar CVE. Revisar cabeceras del servidor real.
6. Crear dos clientes de prueba y abrir el pedido de uno con la sesión del otro.
7. Publicar una reseña de prueba con símbolos HTML y comprobar que se muestran como texto.
8. En un staging autorizado, correr Locust de solo lectura: 1 usuario durante 60 s y, solo después, 5 y 10. No usar Railway de producción.
9. Anotar el Deployment ID de Railway y compararlo con el SHA `957b4bda`.
