# HardWareHouse — Documento maestro de contexto para Codex

> **Archivo sugerido:** `docs/CONTEXTO_HWH.md`  
> **Versión:** 1.0 — 3 de noviembre de 2026  
> **Clasificación:** documentación técnica apta para un repositorio público; **no agregar secretos ni datos de clientes**.  
> **Propósito:** entregar contexto persistente sobre arquitectura, decisiones, módulos, flujo de trabajo, riesgos y asuntos pendientes. No sustituye la inspección del código ni `AGENTS.md`.

## 1. Cómo interpretar este documento

Este documento combina información **verificada en el repositorio** y **antecedentes comunicados durante el desarrollo**. Para evitar confusiones:

- **Verificado en código:** funcionalidad, archivo o configuración observada en la rama `main` al preparar esta versión.
- **Validado en pruebas previas:** resultado informado por el equipo en su entorno local o en Railway; **no es una nueva verificación de producción**.
- **Pendiente / por verificar:** propuesta, incidencia o comportamiento cuyo estado debe comprobarse en el commit y despliegue actuales.
- **Histórico:** decisión o tecnología de una versión anterior; no debe tratarse como arquitectura vigente.

**Orden de autoridad para desarrollo:** instrucciones de seguridad y `AGENTS.md` → código, migraciones y tests del commit actual → configuración efectiva del entorno pertinente → este documento → informes académicos y notas históricas. Ante contradicciones, **informar la discrepancia y no adivinar**.

**Repositorio principal:** [`YuukiS3rl14/Proyecto-HardWareHouse`](https://github.com/YuukiS3rl14/Proyecto-HardWareHouse). **Rama de integración:** `main`. Los cambios del colaborador pueden introducir nuevos campos o migraciones; sincronizar la rama antes de analizar o modificar modelos.

## 2. Objetivo y alcance funcional

**HardWareHouse (HWH)** es un proyecto de comercio electrónico para componentes de computadores y ensamblaje personalizado de PC. Busca permitir que un cliente consulte el catálogo, compare componentes y características, arme un equipo compatible, obtenga un presupuesto, compre y consulte sus pedidos. Incluye herramientas de administración e interfaces de asistencia conversacional.

### Funcionalidades presentes en el repositorio

- Tienda y catálogo por familias de hardware; búsqueda, categorías, proveedores, rangos de precio y ordenamiento.
- Fichas de productos, precios, existencias y comentarios; favoritos.
- Registro, inicio de sesión, perfil y consultas de pedidos con autorización.
- Carrito, checkout, pedidos, pago mediante **PayPal Sandbox**, notificaciones IPN y boletas de prueba.
- Ensamblador de PC con reglas para compatibilidad de componentes, presupuesto y exportación.
- Recomendador de PC y asistente conversacional integrado con las funciones Django.
- Administración Django y datos orientados a informes / análisis; integración histórica de vistas SQL para Power BI.
- Interfaz responsive y paneles de navegación; su experiencia debe seguir evaluándose en escritorio y móvil.

**No asumir:** que existan envíos físicos reales, sucursal verificada, inventario comercial real, soporte humano 24/7, correo transaccional operativo o dominio propio comprado. La información de demostración debe presentarse como tal.

## 3. Arquitectura vigente

```text
Clientes web / móviles (HTTPS)
            |
            v
Railway — servicio web Django + Gunicorn
     |                  |                    |
     |                  |                    +--> Ollama Cloud (API HTTPS)
     |                  |                         clasificación de intenciones
     |                  |                         [fallback: reglas Django]
     |                  +--> PayPal Sandbox (flujo de pago / IPN verificado)
     |
     +--> Railway PostgreSQL (servicio de base de datos separado)
     |
     +--> Cloudflare R2 (archivos estáticos y multimedia)

GitHub (repositorio) --PR / GitHub Actions--> main
GitHub main --despliegue configurado--> Railway
```

**Tecnologías comprobadas en el código:** Python 3.13 como objetivo de CI, Django 4.2, PostgreSQL, Gunicorn, `django-paypal`, `django-storages`/API compatible S3 para Cloudflare R2, Ollama Cloud y JavaScript/CSS para la interfaz. `requirements.txt` fija las versiones instalables; inspeccionarlo antes de actualizar dependencias.

**Decisiones técnicas fundamentales:**

1. **Railway** hospeda la aplicación y PostgreSQL; no se despliega sobre AWS EC2 o Amazon RDS.
2. **Cloudflare R2** sustituye Amazon S3 para archivos; no se utiliza S3 de AWS como servicio contratado.
3. **GitHub** es el origen del código y de los cambios que desencadenan el despliegue configurado.
4. **Gunicorn** ejecuta Django; **Nginx no forma parte del despliegue documentado**.
5. El chatbot es **propio de Django**, no una aplicación Voiceflow; utiliza **Ollama Cloud para interpretación** y reglas/ORM para datos verificables.
6. PayPal se ha probado en **Sandbox**; no equivale a habilitar cobros reales en producción comercial.
7. No representar como confirmados un dominio `hardwarehouse.cl`, una IP pública fija, un servicio de respaldo automático ni garantías de disponibilidad hasta verificarlos.

### Archivos de entrada relevantes

| Área | Ruta o recurso | Para qué sirve |
|---|---|---|
| Configuración | `HardWareHouse/settings.py` | Base de datos, HTTPS, R2, PayPal, Ollama y seguridad |
| Modelos | `core/models.py` | Productos, proveedores, carrito, pedidos, pagos y favoritos |
| Rutas | `core/urls.py` | Páginas y endpoints de la aplicación |
| Plantilla común | `core/templates/core/base.html` | Navegación, buscador y accesos a carrito / favoritos |
| Catálogo y filtros | `core/tienda_filtros.py` | Bandas de precio, orden y consultas de catálogo |
| Armado / recomendación | `core/armado_servicio.py`, `core/compatibilidad.py`, `core/armado_recomendacion.py`, `core/recomendador_pc.py` | Compatibilidad y selección de equipos |
| Chatbot | `core/chatbot/` | Enrutamiento, intenciones, ORM, seguridad y estado conversacional |
| Importación selectiva | `core/catalogo_migracion.py` y `core/management/commands/` | Transferencia controlada de proveedores/productos |
| CI | `.github/workflows/django-ci.yml` | Validaciones automáticas de Pull Requests |
| Reglas de agentes | `AGENTS.md` | Restricciones obligatorias para herramientas de código |

Las rutas pueden evolucionar; buscar el archivo real antes de modificarlo.

## 4. Modelo de catálogo y compatibilidad

En `core/models.py` existen diez familias principales de componentes:

1. `Procesador`
2. `TarjetaGrafica`
3. `MemoriaRam`
4. `PlacaMadre`
5. `AlmacenamientoSSD`
6. `AlmacenamientoHDD`
7. `Gabinete`
8. `FuenteDePoder`
9. `RefrigeracionCooler`
10. `Ventilador`

También existen `Proveedor`, `Region`, `Comuna`, `Comentario`, `Carrito`, `ItemCarrito`, `Pedido`, `ItemPedido`, `PagoBoleta` y `Favorito`.

El ensamblador debe respetar los campos de compatibilidad que realmente existan en el modelo y reconocer las diferencias entre **dato conocido, dato incompatible y dato desconocido**. Revisar, entre otros: socket CPU/placa, RAM y formato, cantidad de módulos, GPU/gabinete, alimentación, disipación/altura de cooler y conectores de almacenamiento (M.2 NVMe/SATA y puertos SATA). No inferir especificaciones técnicas no presentes a partir del nombre comercial.

### Migraciones relevantes

- `core.0012_pedido_paypal_invoice`: soporte para identificación de facturas PayPal, con consideraciones de registros antiguos.
- `core.0013_refrigeracion_referencia`: campos de referencia térmica y física de cooler/CPU/gabinete.
- `core.0014_almacenamiento_placa`: ranuras de almacenamiento de la placa e interfaz/formato HDD.
- `core.0010_analytics_powerbi`: SQL de vistas de análisis solo para PostgreSQL; en motores distintos tiene operación condicionada.

**Regla crítica:** nunca reescribir migraciones históricas ya aplicadas, ni forzar cambios de IDs de productos que puedan aparecer en líneas de pedidos anteriores.

## 5. Datos: desarrollo, demostración y producción

El proyecto ha trabajado con **bases distintas**: PostgreSQL local de desarrollo, PostgreSQL de Railway y entornos de otros colaboradores. Un `git pull` **sincroniza código, no registros de PostgreSQL**. Las migraciones sincronizan esquema, no importan automáticamente productos.

### Antecedente de catálogo

En octubre de 2026 se preparó un archivo JSON de catálogo de demostración con **1.000 productos sintéticos**, distribuidos en las diez familias. El equipo informó que se importó de forma selectiva a Railway y verificó el funcionamiento de tienda, armador y recomendador. **Estos conteos son un antecedente histórico, no una lectura actual de producción.** El catálogo contiene productos, precios y existencias de demostración, no inventario comercial validado.

El flujo selectivo utiliza `exportar_catalogo` e `importar_catalogo`:

- El exportador extrae proveedores y especificaciones de productos; no traslada IDs, usuarios, pedidos, pagos ni datos privados.
- El importador **por defecto hace dry-run sin escribir**.
- Las inserciones requieren opción explícita `--apply` y una confirmación de respaldo. **La bandera de confirmación NO crea ni verifica un backup real**.
- Se conservan registros existentes; no se actualizan precios, stock, proveedores ni historial de compras.
- La equivalencia de productos y posibles ambigüedades deben revisarse antes de importar.

**Peligros de operación:** `DATABASE_URL` tiene prioridad en la configuración PostgreSQL; antes de ejecutar comandos de datos, comprobar si se apunta a local, CI o Railway. No ejecutar en producción `seed_test_data`, `sincronizar_catalogo_demo`, restauraciones completas ni cargas masivas no revisadas.

**Respaldos:** en el momento de las pruebas académicas, no se había confirmado la disponibilidad de respaldos automáticos del plan utilizado. No considerar la base protegida hasta contar con una copia independiente, un procedimiento de restauración probado y autorización para usarlo.

## 6. Pagos, órdenes y seguridad

- La integración actual ha utilizado **PayPal Sandbox** con recepción y validación de **IPN**.
- Una redirección del navegador desde PayPal **no demuestra** que el pago esté verificado. El backend debe confirmar la transacción antes de marcar pedido pagado o ajustar inventario.
- Evitar re-procesamiento de IPN, modificaciones dobles de stock o correos de confirmación duplicados ante notificaciones repetidas.
- Mantener trazabilidad histórica de `ItemPedido` y `PagoBoleta`; no reutilizar IDs de componentes eliminados o sustituidos.
- Los pedidos y sus datos deben ser accesibles únicamente al usuario autorizado o al administrador competente.
- Para cualquier cambio en carrito/checkout, validar en **servidor** cantidades enteras positivas, límites de stock, precios/total derivados de PostgreSQL y concurrencia. El HTML/JavaScript solo complementa la validación.
- No usar credenciales de pago reales en pruebas automáticas ni imprimir secretos en registros.

## 7. Chatbot propio + Ollama Cloud

### Diseño operativo

- Ollama Cloud funciona como clasificador/intérprete de intenciones. En pruebas anteriores se usó el modelo `gemma4:31b` mediante HTTPS. La selección efectiva debe leerse de `OLLAMA_MODEL`, no codificarse como constante inmutable.
- Django ORM es la **fuente de verdad** para nombre, existencia, stock, precio, pedidos y especificaciones.
- Las reglas del proyecto determinan compatibilidad y presupuestos; el LLM **no debe inventar** piezas, costos ni autorizaciones.
- Existe un modo de respaldo basado en reglas si la API falla o está deshabilitada.
- La redacción adicional de respuestas por Ollama se había dejado deshabilitada para reducir latencia y consumo; comprobar flags reales.
- El contexto conversacional debe mantenerse aislado por usuario/sesión y nunca filtrar información de pedidos ajenos.

### Incidencias corregidas previamente, sujetas a regresión

- Consultas de categoría con errores ortográficos (p. ej., «prosesador»).
- Búsquedas de GPU con tope de precio y stock sin filtrar erróneamente por palabras conversacionales.
- Preguntas de compatibilidad que antes caían en búsqueda por nombre.
- Seguimiento de una lista previa: «¿Cuál de esas es la más barata/cara?».
- Falsa detección de «tarjeta gráfica» como «tarjeta bancaria».
- Selección de CPU para armado: evitar escoger un CPU barato sin placa madre compatible.

Estas correcciones se informaron y probaron en distintas etapas; mantener pruebas de regresión y comprobar el despliegue actual antes de declarar un defecto resuelto definitivamente.

### Pruebas relevantes

- `core.test_chatbot_consultas_nl`
- `core.test_chatbot_contexto_catalogo`
- `core.test_catalogo_migracion`
- Otros archivos `core/test_chatbot_*.py` según funcionalidad cambiada.

**Escalabilidad pendiente para producción comercial:** cuotas de uso por usuario/IP, límites de concurrencia, presupuesto de IA, métricas de consumo/tokens, control de abuso y aislamiento de solicitudes lentas. No asumir que la arquitectura de demostración soporta miles de usuarios simultáneos sin pruebas de carga.

## 8. Frontend, experiencia de usuario y QA

### Comportamientos deseados

- Barra de búsqueda de productos visible solo en **Inicio y Tienda**; no mostrarla sin motivo en Armado, Contacto o Sobre nosotros.
- Accesos a pedidos (si autenticado), favoritos y carrito **siempre alineados al extremo derecho** del subencabezado, haya o no buscador.
- Filtros de tienda completos en escritorio y panel lateral accesible en móvil; mantener selección, orden y paginación.
- Formularios con límites específicos y validación Django en servidor, incluyendo contacto, registro y carrito.
- Carrito con cantidades enteras `>= 1` y `<= stock` y totales recalculados en servidor.
- Tarjetas de inicio con destinos reales; no anunciar soporte humano 24/7 si no está confirmado.
- Enlaces de «Contacto» como enlaces legibles, no rutas `/contacto/` expuestas en texto narrativo.
- No crear fechas de actualización ficticias para un filtro de «novedades»; usar un campo real o informar la limitación.

### Observaciones más recientes y estado

A comienzos de noviembre de 2026 se detectaron casos en que el carrito aceptaba texto o cantidades arbitrarias, enlaces informativos incompletos y problemas de diseño móvil. El equipo informó después haber realizado una **ronda de correcciones con Cursor**, pero **no se ha auditado aquí el diff completo ni su estado de despliegue**.

**Incidencia visual específica observada:** al ocultar el buscador en ciertas páginas, el contenedor de botones de carrito y favoritos quedaba cerca del centro o a la izquierda en vez de alinearse a la derecha. En `core/templates/core/base.html` el contenedor de iconos incluía una columna `col-auto col-lg-5 d-flex justify-content-end ...`; la corrección mínima propuesta fue usar un margen automático (`ms-auto`). **Antes de editar, confirmar si el commit actual ya lo corrigió y verificar en móvil y escritorio.**

### Proceso de calidad acordado

- Trabajar en **baterías agrupadas de pruebas**, no hacer un despliegue por cada cambio pequeño.
- Documentar: identificador de prueba, fecha, ejecutor, módulo, entrada, esperado, obtenido, evidencia, severidad, causa, corrección, commit/PR y resultado de regresión.
- Mantener un Word de QA académico con **Calibri 12, texto justificado y títulos jerarquizados en negrita**; el Word se mantiene por separado, no necesariamente en GitHub.
- Para un informe de Codex, distinguir siempre **tests ejecutados** de **validaciones pendientes en Railway**.

## 9. Configuración por entorno (solo nombres, nunca valores secretos)

Variables observadas o empleadas durante el proyecto:

| Área | Variables / ajustes relevantes | Advertencia |
|---|---|---|
| Django | `SECRET_KEY`, `DEBUG`, `USE_HTTPS`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Secretos solo en gestión segura; revisar dominio público |
| PostgreSQL | `DATABASE_URL` o `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `USE_SQLITE` | `DATABASE_URL` puede apuntar a producción; nunca reutilizar en CI |
| Railway | `RAILWAY_PUBLIC_DOMAIN`, `SITE_URL` | URLs de retorno y notificación deben coincidir con despliegue |
| Cloudflare R2 | `USE_R2`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_DOMAIN` | No publicar claves ni archivos privados |
| PayPal | `PAYPAL_TEST`, `PAYPAL_RECEIVER_EMAIL` y parámetros de IPN | Mantener Sandbox en pruebas |
| Ollama | `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `HARDWAREHOUSE_CHAT_INTENT_LLM`, `HARDWAREHOUSE_CHAT_RESPONSE_LLM` | No usar API real en tests unitarios |

**Nunca incluir valores reales** en este archivo, en PR, capturas, logs ni respuestas de un asistente. El repositorio es público.

## 10. GitHub, Codex y automatización

La rama `main` contiene `AGENTS.md` y `.github/workflows/django-ci.yml` según la revisión del repositorio. El flujo CI usa PostgreSQL temporal, Python 3.13 y pruebas selectivas de Django. Se informó una ejecución **verde** después de limitar la comprobación de migraciones a `core`:

```bash
python manage.py check
python manage.py makemigrations core --check --dry-run
python manage.py test core.test_catalogo_migracion core.test_chatbot_contexto_catalogo core.test_chatbot_consultas_nl --noinput --verbosity 1
```

El comando sobre `core` evita un aviso previo de migración en la dependencia `django-paypal`; **no resuelve automáticamente ese problema upstream**. No generar ni aplicar una migración de terceros a producción solo para silenciar CI.

### Flujo deseado de desarrollo

1. Leer `AGENTS.md`, este documento y los archivos afectados; comprobar rama y cambios pendientes.
2. Crear rama de trabajo desde la versión actual de `main`.
3. Realizar cambios enfocados, sin mezclar funcionalidades ajenas.
4. Agregar las pruebas mínimas que reproduzcan el defecto, y ejecutar `manage.py check` + tests del área.
5. Inspeccionar `git diff`, migraciones y archivos temporales.
6. Preparar Pull Request; GitHub Actions debe aprobar.
7. Revisar y aprobar antes de merge. **No hacer push/merge/deploy sin autorización explícita.**
8. Tras el despliegue aprobado, validar en Railway y añadir evidencia al registro QA.

**No confirmado aquí:** configuración efectiva de reglas de protección de `main`, staging separado y restauración de backup. Verificar en GitHub/Railway antes de asumirlos implementados.

## 11. Hoja de ruta y mejoras propuestas (no suponer implementadas)

**Prioridad inmediata — confirmar estado real del código y QA:**

- Revisar y validar la última ronda de correcciones de formularios, carrito y filtros responsive.
- Resolver/confirmar alineación derecha de iconos sin buscador; probar escritorio y móvil.
- Verificar que operaciones de carrito rechazan datos manipulados desde HTTP, no solo desde la interfaz.
- Completar pruebas de regresión agrupadas y documentarlas antes de un único despliegue.

**Mejoras de producto propuestas:**

- Dominio propio: `hardwarehouse.cl`, solo después de verificar disponibilidad y contratación.
- Correo corporativo, notificaciones de contacto, confirmación de compra y recuperación de contraseña por enlaces seguros (Django + proveedor de correo). No asumir funcionalidad activa.
- Mejorar calidad de armado por presupuesto/propósito, sin sacrificar compatibilidad.
- Fortalecer límites y observabilidad del chatbot para evitar abuso de tokens y saturación de concurrencia.
- Definir respaldos verificables, restauración, alertas y, si corresponde, entorno staging.

**Documentación académica:** los informes, diagramas y presentaciones deben reflejar Railway/R2/Ollama y evitar referencias a AWS/Voiceflow como servicios activos; documentar por separado citas o propuestas históricas.

## 12. Plantilla breve para cerrar cada tarea de Codex

```markdown
### Cambio
- Objetivo / incidencia:
- Estado previo y evidencia:
- Causa raíz confirmada:
- Archivos modificados:
- Migraciones: ninguna / propuesta / requerida

### Validación
- Comandos de prueba ejecutados:
- Resultado y limitaciones:
- Funcionalidades potencialmente afectadas:
- Estado en Railway: no desplegado / verificado

### Entrega
- Rama / Pull Request:
- Riesgos y acciones pendientes:
- Recomendación: GO / NO-GO (con justificación)
```

## 13. Mantenimiento de este documento

Actualizar este contexto cuando cambien **arquitectura, decisiones técnicas, proveedores, esquema, flujos de seguridad, comportamiento del chatbot o prioridades**. No usarlo como bitácora de cada línea de código; esa trazabilidad pertenece a PR, commits, issues y QA.

Al editar:

1. Corregir la sección pertinente y registrar la fecha.
2. Distinguir **hechos comprobados**, **resultados históricos** e **ideas futuras**.
3. Revisar que no se incluyan secretos, datos personales, conexiones privadas o resultados no reproducidos.
4. Mantener vigente el resumen de estado, sin reescribir el historial de pagos o decisiones previas.

---

**Última revisión documental:** 3 de noviembre de 2026. **Validación técnica:** lectura del repositorio GitHub y antecedentes del trabajo del equipo; **no se realizaron pruebas contra Railway ni operaciones de escritura** durante la elaboración de este documento.
