"""
Texto de conocimiento institucional de HardWareHouse para asistentes conversacionales.
Regenerar el .txt: python manage.py export_empresa_conocimiento_txt
"""

EMPRESA_CONOCIMIENTO_ASISTENTE = """
================================================================================
HARDWAREHOUSE — BASE DE CONOCIMIENTO INSTITUCIONAL (EMPRESA Y SERVICIOS)
================================================================================
Documento para asistentes virtuales. Describe la empresa, sus servicios, políticas
y preguntas frecuentes. No incluye listado de productos (usar CSV de catálogo).

Última alineación: información coherente con el sitio web HardWareHouse (Chile).

--------------------------------------------------------------------------------
1. IDENTIDAD DE LA EMPRESA
--------------------------------------------------------------------------------

Nombre comercial: HardWareHouse

Tipo de negocio: Pyme emergente dedicada al comercio de hardware de computación
en Chile.

Antigüedad: Cinco (5) años en el mercado.

Actividad principal:
- Comercialización de componentes de PC (piezas sueltas).
- Especialización en armado de computadores a medida.
- Venta en línea a través del sitio web propio, con catálogo por categorías,
  carrito de compras y pago con PayPal.

Propuesta de valor:
HardWareHouse combina catálogo digital, herramientas de compatibilidad para armar
PCs y atención orientada al cliente, para que las personas elijan componentes con
criterio técnico y compren con claridad.

--------------------------------------------------------------------------------
2. MISIÓN
--------------------------------------------------------------------------------

Ofrecer componentes de calidad con una atención cercana al cliente, ayudando a cada
persona a encontrar el PC que quiere o necesita —ya sea comprando piezas sueltas o
armando un equipo completo— con información clara en todo el proceso de compra.

--------------------------------------------------------------------------------
3. VISIÓN
--------------------------------------------------------------------------------

Ser la tienda número uno en Chile, o consolidarse entre el top 3 a nivel nacional,
en reconocimiento por:
- Especialización en hardware y componentes.
- Experiencia en armado de PCs.
- Confianza y satisfacción de los clientes.

--------------------------------------------------------------------------------
4. VALORES
--------------------------------------------------------------------------------

- Trato amigable y respetuoso con quienes nos visitan o nos escriben.
- Demostrar conocimiento técnico para orientar con criterio (sin presión de venta).
- Acompañar al cliente en cada etapa: elección de piezas, compra y retiro en tienda.

--------------------------------------------------------------------------------
5. UBICACIÓN Y CONTACTO (DATOS DE EJEMPLO DEL SITIO)
--------------------------------------------------------------------------------

HardWareHouse opera con un punto de referencia para retiro en tienda en la Región
Metropolitana. La dirección publicada en el sitio es de ejemplo / ficticia para
fines del proyecto web:

  Dirección de retiro (ejemplo): Av. Tecnología 123, Santiago, Región Metropolitana, Chile.

Correo de contacto (ejemplo): contacto@hardwarehouse.cl
Teléfono de contacto (ejemplo): +56 9 1234 5678

Formulario de contacto: disponible en la sección "Contacto" del sitio web.

Página "Sobre nosotros": resume misión, visión, valores y preguntas frecuentes.

IMPORTANTE: La empresa no declara múltiples sucursales en el proyecto actual. El
retiro se coordina en el punto de referencia indicado tras confirmar el pago.

--------------------------------------------------------------------------------
6. POLÍTICA DE ENTREGA: NO HAY DESPACHO NI DELIVERY
--------------------------------------------------------------------------------

HardWareHouse NO realiza:
- Despachos a domicilio.
- Envíos por courier.
- Delivery.
- Envíos "a todo Chile" ni envíos internacionales desde la web.

La entrega de productos es EXCLUSIVAMENTE mediante RETIRO EN TIENDA, una vez que
el pago del pedido queda confirmado.

En el proceso de checkout el sitio puede solicitar dirección, ciudad, región y
comuna. Esos datos forman parte de la información del pedido y facturación; NO
significan que exista envío a domicilio. El catálogo de regiones y comunas de
Chile en la base de datos sirve para registrar datos del cliente y del pedido, no
para calcular envíos.

Si un usuario pregunta por envío a su casa, la respuesta correcta es: no contamos
con ese servicio; deben retirar en tienda tras coordinar.

--------------------------------------------------------------------------------
7. CATÁLOGO Y CATEGORÍAS DE PRODUCTOS
--------------------------------------------------------------------------------

La tienda vende componentes de PC organizados en estas categorías:

- Procesadores (CPU)
- Tarjetas gráficas (GPU)
- Memoria RAM
- Placas madre
- Almacenamiento SSD
- Discos duros HDD
- Gabinetes
- Fuentes de poder (PSU)
- Refrigeración (coolers aire o líquida AIO)
- Ventiladores

Cada producto tiene marca/proveedor, nombre, descripción, precio en pesos chilenos
(CLP), stock y especificaciones técnicas según su tipo.

La tienda online permite buscar, filtrar por categoría, marca y rangos de precio,
y ver el catálogo paginado.

Para consultas de precio, stock o especificaciones de un producto concreto, el
asistente debe apoyarse en la base de conocimiento de productos (CSV/catálogo), no
solo en este documento.

--------------------------------------------------------------------------------
8. ARMADO DE PC (HERRAMIENTA DEL SITIO)
--------------------------------------------------------------------------------

HardWareHouse ofrece una sección "Armado de PC" en el sitio web donde el usuario
elige componentes paso a paso (CPU, placa madre, RAM, GPU, almacenamiento, gabinete,
fuente, refrigeración, etc.).

El sistema evalúa compatibilidad entre piezas, por ejemplo:
- Socket del procesador y la placa madre.
- Tipo y formato de memoria RAM.
- Potencia de la fuente respecto al consumo estimado.
- Largo de la GPU respecto al gabinete.
- Ranuras y capacidades de almacenamiento y RAM.

El usuario puede agregar el armado completo al carrito o exportar un presupuesto
(por ejemplo en Excel) con el detalle de piezas y precios.

HardWareHouse está especializado en orientar armados; el chat puede invitar al usuario
a usar el armador o contactar para asesoría.

--------------------------------------------------------------------------------
9. CÓMO COMPRAR EN LA WEB (FLUJO GENERAL)
--------------------------------------------------------------------------------

Paso 1: Explorar la tienda o el armador y agregar productos al carrito.
Paso 2: Iniciar sesión o registrarse (cuenta de usuario en el sitio).
Paso 3: Revisar el carrito y proceder al checkout (finalizar compra).
Paso 4: Completar datos de facturación (nombre, teléfono, dirección de referencia,
        ciudad, región; según formulario del sitio).
Paso 5: Pagar con PayPal.
Paso 6: Esperar confirmación del pago. Hasta que PayPal confirma, el pedido puede
        permanecer pendiente y el stock no se descuenta definitivamente.
Paso 7: Coordinar retiro en tienda una vez el pedido está pagado/confirmado.

Funciones adicionales para usuarios registrados:
- Lista de favoritos (guardar productos).
- Mis pedidos (historial y estados).
- Perfil de usuario.
- Comentarios y calificaciones en fichas de producto.

--------------------------------------------------------------------------------
10. PAGOS
--------------------------------------------------------------------------------

Método de pago en línea: PayPal.

El sitio puede operar en modo prueba (sandbox) o producción según configuración;
en ambos casos el flujo es a través de PayPal.

El pago debe quedar confirmado antes de preparar el pedido para retiro.

Tras el pago exitoso, el usuario puede ver el pedido en "Mis pedidos" y, cuando
corresponda, la boleta o comprobante asociado al pago.

--------------------------------------------------------------------------------
11. ESTADOS DE UN PEDIDO
--------------------------------------------------------------------------------

Los pedidos en el sistema pueden tener estados como:
- Pendiente de pago
- Pago confirmado
- Enviado
- Entregado
- Cancelado

En el contexto de HardWareHouse sin despacho a domicilio, "Enviado" y "Entregado"
se interpretan en el flujo administrativo del pedido (por ejemplo, preparación
lista o retiro completado en tienda), NO como envío por correo. Si el usuario
pregunta por seguimiento de un courier, aclarar que no hay envíos a domicilio.

Los pedidos cancelados o con pago fallido no generan retiro de productos.

--------------------------------------------------------------------------------
12. STOCK Y DISPONIBILIDAD
--------------------------------------------------------------------------------

El sitio muestra stock por producto en el catálogo.

Si un producto se agota durante el proceso de compra, el equipo puede contactar al
cliente al confirmar el pedido.

Se recomienda al cliente verificar stock o escribir por contacto antes de pagar si
tiene dudas sobre disponibilidad de piezas concretas.

--------------------------------------------------------------------------------
13. ASESORÍA Y CANALES DE AYUDA
--------------------------------------------------------------------------------

El cliente puede obtener ayuda mediante:
- Asistente conversacional en el sitio (cuando esté integrado).
- Formulario de contacto.
- Uso del armador de PC con validaciones de compatibilidad.
- Navegación por categorías y fichas de detalle de cada producto.

El tono de HardWareHouse es amigable, técnico cuando hace falta, y enfocado en
ayudar a elegir, no solo en vender.

--------------------------------------------------------------------------------
14. PREGUNTAS FRECUENTES (FAQ)
--------------------------------------------------------------------------------

P: ¿Dónde están ubicados?
R: Punto de retiro de referencia en Av. Tecnología 123, Santiago, Región Metropolitana
   (dirección de ejemplo del sitio). Horario y coordinación se confirman al gestionar
   el pedido vía contacto.

P: ¿Hacen despachos o envíos?
R: No. Solo retiro en tienda. No hay delivery ni envío a domicilio.

P: ¿Por qué piden región y comuna si no envían?
R: Son datos del pedido y facturación en Chile; no implican envío.

P: ¿Cómo compro?
R: Tienda o armador → carrito → login/registro → checkout → PayPal → retiro en tienda.

P: ¿Qué es el armado de PC?
R: Herramienta web para elegir piezas compatibles y comprar el conjunto o exportar
   presupuesto.

P: ¿Aceptan transferencia o efectivo en la web?
R: El flujo de compra online documentado en el proyecto usa PayPal. Para otros medios,
   el cliente debe consultar por contacto (fuera del alcance automático del sitio).

P: ¿Tienen soporte 24/7?
R: El sitio puede mostrar mensajes de soporte; para tiempos reales de respuesta,
   indicar que puede usar contacto o chat y que el equipo responderá a la brevedad.

P: ¿Puedo cancelar un pedido?
R: Los usuarios registrados pueden gestionar pedidos desde "Mis pedidos" según las
   opciones disponibles en el sitio (por ejemplo cancelar si aún está pendiente).

P: ¿Los precios incluyen IVA?
R: Los precios se muestran en CLP en el catálogo; para detalle tributario formal,
   referir a la boleta del pedido o contacto.

P: ¿Venden laptops o periféricos completos?
R: El catálogo del proyecto se centra en componentes de PC listados en las categorías
   de hardware (CPU, GPU, RAM, etc.). No es una tienda general de electrónica.

P: ¿Puedo retirar otra persona por mí?
R: Coordinar con el equipo vía contacto al confirmar el pedido; no hay procedimiento
   automatizado en el sitio para terceros.

--------------------------------------------------------------------------------
15. LO QUE EL ASISTENTE NO DEBE AFIRMAR
--------------------------------------------------------------------------------

- No inventar direcciones distintas a la de ejemplo sin indicar que es referencial.
- No prometer envío, delivery, plazos de courier ni cobertura geográfica de despacho.
- No inventar precios o stock de productos (usar base de productos).
- No prometer stock infinito ni garantías no mencionadas en el sitio.
- No confundir el registro de comuna en checkout con envío a esa comuna.

--------------------------------------------------------------------------------
16. RUTAS ÚTILES DEL SITIO WEB (REFERENCIA)
--------------------------------------------------------------------------------

Inicio: /
Tienda: /tienda/
Armado de PC: /armado/
Carrito: /carrito/
Checkout: /checkout/
Contacto: /contacto/
Sobre nosotros: /sobre-nosotros/
Registro y login: /registro/ y /login/
Mis pedidos: /pedidos/ (usuario autenticado)
Favoritos: /favoritos/ (usuario autenticado)
Catálogo CSV productos (exportación): /catalogo/productos.csv

================================================================================
FIN DEL DOCUMENTO INSTITUCIONAL HARDWAREHOUSE
================================================================================
""".strip()
