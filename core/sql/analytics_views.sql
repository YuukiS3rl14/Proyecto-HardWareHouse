-- Vistas de solo lectura para Power BI. El ingreso vive en fact_venta_item
-- (una fila por ítem). pedido_pagado conserva el total del pedido una sola vez.
-- No incluyen correo, nombre, dirección ni usuario.

CREATE SCHEMA IF NOT EXISTS analytics;

DROP VIEW IF EXISTS analytics.metodo_pago;
DROP VIEW IF EXISTS analytics.producto_top;
DROP VIEW IF EXISTS analytics.ingreso_por_categoria;
DROP VIEW IF EXISTS analytics.componente_comprado;
DROP VIEW IF EXISTS analytics.venta_por_fecha;
DROP VIEW IF EXISTS analytics.pedido_pagado;
DROP VIEW IF EXISTS analytics.fact_venta_item;
DROP VIEW IF EXISTS analytics.inventario_actual;

CREATE VIEW analytics.inventario_actual
WITH (security_barrier = true) AS
SELECT 'procesador'::text AS producto_modelo, p.id AS producto_pk, p.categoria, m.nombre AS marca,
       p.nombre, p.precio, p.stock, (p.precio * p.stock) AS valor_inventario
FROM core_procesador p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'tarjeta_grafica', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_tarjetagrafica p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'memoria_ram', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_memoriaram p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'placa_madre', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_placamadre p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'almacenamiento_ssd', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_almacenamientossd p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'almacenamiento_hdd', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_almacenamientohdd p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'gabinete', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_gabinete p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'fuente_de_poder', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_fuentedepoder p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'refrigeracion', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_refrigeracioncooler p
JOIN core_proveedor m ON m.id = p.proveedor_id
UNION ALL
SELECT 'ventilador', p.id, p.categoria, m.nombre, p.nombre, p.precio, p.stock, p.precio * p.stock
FROM core_ventilador p
JOIN core_proveedor m ON m.id = p.proveedor_id;

COMMENT ON VIEW analytics.inventario_actual IS
    'Stock y precio actuales del catálogo. No es historia de ventas.';

CREATE VIEW analytics.fact_venta_item
WITH (security_barrier = true) AS
SELECT
    i.id AS item_id,
    p.id AS pedido_id,
    b.id AS boleta_id,
    b.transaccion_id,
    b.fecha_pago,
    p.fecha_pedido,
    (b.fecha_pago AT TIME ZONE 'America/Santiago')::date AS fecha,
    p.estado AS estado_pedido,
    b.metodo_pago,
    (
        b.transaccion_id LIKE 'DEMO-PBI-%'
        OR COALESCE(p.paypal_transaccion_id, '') LIKE 'DEMO-PBI-%'
        OR b.metodo_pago = 'DEMO-PBI'
    ) AS es_demo,
    i.producto_nombre,
    i.producto_tipo AS categoria,
    NULLIF(i.producto_modelo, '') AS producto_modelo,
    i.producto_pk,
    i.cantidad,
    i.precio_unitario,
    ROUND(i.precio_unitario * i.cantidad, 2) AS total_linea,
    inv.marca AS marca_catalogo
FROM core_itempedido i
JOIN core_pedido p ON p.id = i.pedido_id
JOIN core_pagoboleta b ON b.pedido_id = p.id
LEFT JOIN analytics.inventario_actual inv
    ON inv.producto_modelo = i.producto_modelo
   AND inv.producto_pk = i.producto_pk
WHERE p.estado IN ('PAGADO', 'ENVIADO', 'ENTREGADO');

COMMENT ON VIEW analytics.fact_venta_item IS
    'Una fila por ítem pagado. El ingreso es total_linea. Nombre y precio son la copia histórica del ítem. marca_catalogo es la marca actual de esa clave de catálogo y queda nula si el producto ya no existe.';

CREATE VIEW analytics.pedido_pagado
WITH (security_barrier = true) AS
SELECT
    p.id AS pedido_id,
    b.id AS boleta_id,
    b.transaccion_id,
    b.fecha_pago,
    p.fecha_pedido,
    (b.fecha_pago AT TIME ZONE 'America/Santiago')::date AS fecha,
    p.estado AS estado_pedido,
    b.metodo_pago,
    p.total_monto AS total_pedido,
    b.monto_pagado,
    (
        b.transaccion_id LIKE 'DEMO-PBI-%'
        OR COALESCE(p.paypal_transaccion_id, '') LIKE 'DEMO-PBI-%'
        OR b.metodo_pago = 'DEMO-PBI'
    ) AS es_demo,
    COALESCE(items.lineas, 0) AS lineas,
    COALESCE(items.unidades, 0) AS unidades
FROM core_pedido p
JOIN core_pagoboleta b ON b.pedido_id = p.id
LEFT JOIN (
    SELECT pedido_id, COUNT(*)::integer AS lineas, COALESCE(SUM(cantidad), 0)::integer AS unidades
    FROM core_itempedido
    GROUP BY pedido_id
) items ON items.pedido_id = p.id
WHERE p.estado IN ('PAGADO', 'ENVIADO', 'ENTREGADO');

COMMENT ON VIEW analytics.pedido_pagado IS
    'Una fila por pedido pagado. total_pedido no debe sumarse junto con total_linea.';

CREATE VIEW analytics.venta_por_fecha
WITH (security_barrier = true) AS
SELECT
    fecha,
    COUNT(DISTINCT pedido_id) AS pedidos,
    COALESCE(SUM(cantidad), 0)::bigint AS unidades,
    COALESCE(SUM(total_linea), 0) AS ingresos
FROM analytics.fact_venta_item
GROUP BY fecha;

COMMENT ON VIEW analytics.venta_por_fecha IS
    'Ingresos por fecha de pago en America/Santiago, sumando cada ítem una vez.';

CREATE VIEW analytics.componente_comprado
WITH (security_barrier = true) AS
SELECT
    item_id,
    pedido_id,
    fecha,
    es_demo,
    categoria,
    producto_nombre,
    producto_modelo,
    producto_pk,
    marca_catalogo,
    cantidad,
    precio_unitario,
    total_linea
FROM analytics.fact_venta_item;

COMMENT ON VIEW analytics.componente_comprado IS
    'Componentes vendidos, con el nombre y el precio guardados en el ítem.';

CREATE VIEW analytics.ingreso_por_categoria
WITH (security_barrier = true) AS
SELECT
    categoria,
    COUNT(DISTINCT pedido_id) AS pedidos,
    COALESCE(SUM(cantidad), 0)::bigint AS unidades,
    COALESCE(SUM(total_linea), 0) AS ingresos
FROM analytics.fact_venta_item
GROUP BY categoria;

COMMENT ON VIEW analytics.ingreso_por_categoria IS
    'Ingreso por la categoría copiada en el ítem, no por el catálogo actual.';

CREATE VIEW analytics.producto_top
WITH (security_barrier = true) AS
SELECT
    categoria,
    producto_nombre,
    producto_modelo,
    producto_pk,
    MAX(marca_catalogo) AS marca_catalogo,
    COUNT(DISTINCT pedido_id) AS pedidos,
    COALESCE(SUM(cantidad), 0)::bigint AS unidades,
    COALESCE(SUM(total_linea), 0) AS ingresos,
    RANK() OVER (ORDER BY COALESCE(SUM(total_linea), 0) DESC, producto_nombre) AS ranking_ingresos,
    RANK() OVER (
        PARTITION BY categoria
        ORDER BY COALESCE(SUM(total_linea), 0) DESC, producto_nombre
    ) AS ranking_categoria
FROM analytics.fact_venta_item
GROUP BY categoria, producto_nombre, producto_modelo, producto_pk;

COMMENT ON VIEW analytics.producto_top IS
    'Ranking por ingreso usando el nombre histórico. Filtra ranking_ingresos en Power BI para un top N.';

CREATE VIEW analytics.metodo_pago
WITH (security_barrier = true) AS
SELECT
    metodo_pago,
    COUNT(*) AS pedidos,
    COALESCE(SUM(unidades), 0)::bigint AS unidades,
    COALESCE(SUM(total_pedido), 0) AS ingresos
FROM analytics.pedido_pagado
GROUP BY metodo_pago;

COMMENT ON VIEW analytics.metodo_pago IS
    'Ingreso por método de pago, sumando cada pedido una sola vez.';

-- Índices que apoyan estas lecturas (migración Django):
-- core_pedido (estado, fecha_pedido): filtra pedidos pagados.
-- core_pagoboleta (fecha_pago): agrupa por fecha de pago.
-- core_itempedido (producto_modelo, producto_pk): enlaza la marca vigente.
-- core_itempedido.pedido_id y core_pagoboleta.pedido_id ya están indexados
-- por la clave foránea y la relación uno a uno.
