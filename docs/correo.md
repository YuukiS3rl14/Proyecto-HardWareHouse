# Correo de HardWareHouse

Django envía el formulario de contacto y la confirmación de compra por la API de EmailJS en el servidor (`core/correo.py`). No hay SDK de EmailJS en el navegador y no hay envío SMTP. Publicar este repositorio en Railway no despliega el Worker de Cloudflare.

Las cuentas `manuelescool11@gmail.com` y `yxds3rl14@gmail.com` no deben quedar como destinatarios. No están en el código; si siguen en EmailJS, Cloudflare o Railway, hay que quitarlas en esos paneles.

## Recorrido

1. El formulario hace POST a Django. Django llama a EmailJS con la plantilla de contacto y `reply_to` igual al correo de quien escribió.
2. El destino público sale de la variable `CONTACT_EMAIL` y viaja en `contacto_destino` y `destino` como `contacto@hardwarehouse.cl`.
3. Cloudflare Email Routing recibe esa dirección y ejecuta `cloudflare/email-worker/contacto-router.js`.
4. El Worker reenvía el mismo mensaje a `trabajadorhardwarehouse@gmail.com` y `administradorhardwarehouse@gmail.com`.
5. Un correo escrito directo a `contacto@hardwarehouse.cl` sigue el mismo Worker y los mismos dos buzones.
6. La confirmación de compra usa la plantilla de pedido y `cliente_email`: primero el correo válido de la cuenta y, si no lo hay, el del pagador de PayPal. No se copia al equipo.

## Variables

| Variable | Dónde | Valor |
|---|---|---|
| `CONTACT_EMAIL` | Railway y `.env` | `contacto@hardwarehouse.cl` |
| `WORKER_EMAIL` | Solo Cloudflare, no Django | `trabajadorhardwarehouse@gmail.com` |
| `ADMIN_EMAIL` | Solo Cloudflare, no Django | `administradorhardwarehouse@gmail.com` |
| `EMAILJS_SERVICE_ID` | Railway | `service_jrqdng2` |
| `EMAILJS_TEMPLATE_CONTACTO` | Railway | `template_aldusli` |
| `EMAILJS_TEMPLATE_PEDIDO` | Railway | `template_fh7t9jw` |
| `EMAILJS_PUBLIC_KEY` | Railway | la clave pública ya existente |
| `EMAILJS_PRIVATE_KEY` | Railway | la clave privada ya existente |

No definas `EMAIL_HOST`. Django no tiene un caso de uso SMTP.

## EmailJS, cambio manual

Estos campos están en el dashboard. El código no los modifica.

Plantilla de contacto `template_aldusli`:

- To Email: `contacto@hardwarehouse.cl`, o `{{contacto_destino}}`.
- Reply To: `{{reply_to}}`.
- Quita `manuelescool11@gmail.com` y `yxds3rl14@gmail.com` de To, Cc y Cco.
- El cuerpo puede seguir mostrando `{{from_name}}`, `{{email}}`, `{{from_email}}`, `{{correo}}`, `{{asunto}}`, `{{mensaje}}` y `{{telefono}}`. Esos campos son de quien escribió.
- To Email no puede ser `{{email}}`, `{{from_email}}`, `{{correo}}` ni `{{reply_to}}`.

Plantilla de compra `template_fh7t9jw`:

- To Email: `{{cliente_email}}`.
- Sin Cc ni Cco al equipo ni a las cuentas personales.
- No cambies el resto de variables de pedido.

Servicio `service_jrqdng2`:

- Revisa la cuenta conectada al servicio. Si el remitente sigue siendo un Gmail personal, eso se cambia en EmailJS, no en Django. El destinatario del formulario debe ser `contacto@hardwarehouse.cl` aunque el remitente del servicio todavía sea otra cuenta.

## Cloudflare, cambio manual

1. Activa Email Routing en `hardwarehouse.cl`. No cambies los registros DNS del sitio web ni de R2.
2. Verifica como destinos solo `trabajadorhardwarehouse@gmail.com` y `administradorhardwarehouse@gmail.com`.
3. No verifiques ni dejes activas las dos cuentas personales antiguas.
4. Publica el Worker aparte, desde `cloudflare/email-worker/`, con Wrangler. Railway no lo hace.
5. Crea una regla de dirección personalizada, no un catch-all: `contacto@hardwarehouse.cl` → Send to Worker → este Worker.
6. Un mensaje externo a esa misma dirección debe usar la misma regla.

## Responder como contacto@hardwarehouse.cl

La respuesta la escribe el trabajador desde su cliente de correo, con una identidad autenticada del dominio. Django no interviene.

La opción Enviar como de una cuenta personal de Gmail dejará de admitir direcciones externas en enero de 2027. No la uses como solución permanente.

Si más adelante el cliente de correo, o un envío nuevo del backend, usa el SMTP de Cloudflare, los datos son `smtp.mx.cloudflare.net`, puerto `465`, SSL activo, TLS desactivado, usuario el token de API y remitente `contacto@hardwarehouse.cl`. La contraseña queda solo en ese cliente o en el entorno que realmente envíe. Hoy esa vía no está configurada en Django.
