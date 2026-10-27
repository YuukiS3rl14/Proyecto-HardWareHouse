# Power BI Desktop y PostgreSQL local

Las vistas están en el esquema `analytics` de la base local `bd_hardwarehouse`. El ingreso de una venta es `total_linea` en `fact_venta_item` (una fila por ítem). `pedido_pagado.total_pedido` es el total del pedido y no debe sumarse en un visual que también muestre ítems.

Los precios y nombres de `fact_venta_item` son la copia guardada en `ItemPedido`. `marca_catalogo` es la marca actual de `producto_modelo` + `producto_pk`; queda vacía si ese producto ya no existe. Las vistas no incluyen correo, nombre, dirección ni usuario.

## Conexión

1. Abre Power BI Desktop.
2. Inicio, Obtener datos, Base de datos PostgreSQL. Si pide el conector, instala el que ofrece el propio Power BI (Npgsql).
3. Servidor: `127.0.0.1:5432`
4. Base de datos: `bd_hardwarehouse`
5. Modo de conectividad:
   - Importar: recomendado. Copia las vistas al modelo. Hay cerca de mil pedidos y el informe no depende de que PostgreSQL siga abierto.
   - DirectQuery: deja la consulta en PostgreSQL. Úsalo solo si necesitas ver filas nuevas sin volver a cargar. El rol de lectura alcanza para este modo.
6. En la ventana de credenciales elige Base de datos.
7. Usuario: `powerbi_reader`
8. Contraseña: la definida en `POWERBI_DB_PASSWORD` al ejecutar `python manage.py crear_rol_powerbi --apply`. No está en el repositorio. Si el rol ya existía y no usaste `--update-password`, conserva la clave anterior.
9. En el navegador abre el esquema `analytics` y marca:
   - `fact_venta_item`
   - `pedido_pagado`
   - `venta_por_fecha`
   - `componente_comprado`
   - `ingreso_por_categoria`
   - `producto_top`
   - `metodo_pago`
   - `inventario_actual`
10. No marques tablas de `public`. Ese rol no puede leerlas.
11. Cargar.

Para repetir la carga: Inicio, Actualizar. En Importar, eso vuelve a leer las vistas.

## Modelo

Relaciona `pedido_pagado[pedido_id]` (1) con `fact_venta_item[pedido_id]` (*), dirección de filtro simple desde el pedido hacia el ítem. No pongas `total_pedido` en un visual que baje al ítem: Power BI repetiría el total del pedido en cada línea. El ingreso se mide con `total_linea`.

`producto_top`, `ingreso_por_categoria`, `venta_por_fecha` y `metodo_pago` ya están agregadas. No las relaciones con el hecho si vas a sumar otra vez sus columnas de ingresos. Úsalas como tablas de resumen o arma las medidas sobre `fact_venta_item`.

`inventario_actual` es el catálogo de hoy. No es historia de ventas. Se puede relacionar con el hecho por `producto_modelo` y `producto_pk`, sabiendo que la marca y el precio del inventario pueden diferir del nombre y del precio guardados en la venta.

Para un calendario, crea una tabla de fechas y relaciónala con `fact_venta_item[fecha]`. `fecha` es el día de `fecha_pago` en `America/Santiago`.

## Medidas DAX

```dax
Ingresos = SUM ( fact_venta_item[total_linea] )

Unidades = SUM ( fact_venta_item[cantidad] )

Pedidos = DISTINCTCOUNT ( fact_venta_item[pedido_id] )

Ticket promedio = DIVIDE ( [Ingresos], [Pedidos] )

Ingresos demo = CALCULATE ( [Ingresos], fact_venta_item[es_demo] = TRUE () )

Ingresos reales = CALCULATE ( [Ingresos], fact_venta_item[es_demo] = FALSE () )
```

`Ingresos` y la suma de `pedido_pagado[total_pedido]` coinciden cuando cada ítem cuadra con su pedido. No uses `SUM ( pedido_pagado[total_pedido] )` dentro de un filtro de producto.

Top de productos: en `producto_top`, filtra `ranking_ingresos <= 10`. El ranking usa el nombre histórico del ítem.

## Índices

La migración `0010_analytics_powerbi` agrega:

- `pedido_estado_fecha_idx` en `core_pedido (estado, fecha_pedido)`, para quedarse con los pedidos pagados, enviados o entregados.
- `boleta_fecha_pago_idx` en `core_pagoboleta (fecha_pago)`, para las series por día.
- `itempedido_producto_idx` en `core_itempedido (producto_modelo, producto_pk)`, para la marca vigente.

`core_itempedido.pedido_id` y `core_pagoboleta.pedido_id` ya tenían índice por ser clave foránea y relación uno a uno. No hace falta otro índice para el volumen local. Conviene revisarlos de nuevo si la tabla de ítems crece por encima de unos cientos de miles de filas.

## Rol

El rol `powerbi_reader` tiene `CONNECT`, `USAGE` sobre `analytics` y `SELECT` sobre sus vistas. No tiene `INSERT`, `UPDATE` ni `DELETE`, ni permiso sobre las tablas de pedidos y clientes. Las vistas se ejecutan con el dueño de la vista, así que el rol no necesita leer `public`.

```text
$env:POWERBI_DB_PASSWORD = "<al menos 16 caracteres>"
.\venv\Scripts\python.exe manage.py crear_rol_powerbi --apply
```

`--update-password` cambia la clave. `--dry-run` solo informa si el rol existe.
