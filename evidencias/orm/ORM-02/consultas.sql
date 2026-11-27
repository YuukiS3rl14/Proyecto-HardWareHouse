-- detalle
-- consulta 1
SELECT "core_procesador"."id", "core_procesador"."creado_en", "core_procesador"."actualizado_en", "core_procesador"."stock_minimo", "core_procesador"."stock_advertencia", "core_procesador"."en_oferta", "core_procesador"."precio_oferta", "core_procesador"."categoria", "core_procesador"."proveedor_id", "core_procesador"."nombre", "core_procesador"."descripcion", "core_procesador"."precio", "core_procesador"."stock", "core_procesador"."imagen", "core_procesador"."socket", "core_procesador"."nucleos", "core_procesador"."frecuencia_base", "core_procesador"."potencia_referencia_watts", "core_procesador"."incluye_cooler", "core_procesador"."potencia_termica_referencia_watts", "core_procesador"."graficos_integrados", "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_procesador" INNER JOIN "core_proveedor" ON ("core_procesador"."proveedor_id" = "core_proveedor"."id") WHERE "core_procesador"."id" = 161 ORDER BY "core_procesador"."id" ASC LIMIT 1;

-- consulta 2
SELECT AVG("core_comentario"."calificacion") AS "promedio", COUNT("core_comentario"."id") AS "total" FROM "core_comentario" WHERE "core_comentario"."procesador_id" = 161;

-- consulta 3
SELECT "core_comentario"."id", "core_comentario"."usuario_id", "core_comentario"."titulo", "core_comentario"."texto", "core_comentario"."calificacion", "core_comentario"."fecha_creacion", "core_comentario"."procesador_id", "core_comentario"."tarjeta_grafica_id", "core_comentario"."memoria_ram_id", "core_comentario"."placa_madre_id", "core_comentario"."almacenamiento_ssd_id", "core_comentario"."almacenamiento_hdd_id", "core_comentario"."gabinete_id", "core_comentario"."fuente_de_poder_id", "core_comentario"."refrigeracion_id", "core_comentario"."ventilador_id" FROM "core_comentario" WHERE "core_comentario"."procesador_id" = 161 ORDER BY "core_comentario"."fecha_creacion" DESC;

-- contraste
-- consulta 1
SELECT "core_procesador"."id", "core_procesador"."creado_en", "core_procesador"."actualizado_en", "core_procesador"."stock_minimo", "core_procesador"."stock_advertencia", "core_procesador"."en_oferta", "core_procesador"."precio_oferta", "core_procesador"."categoria", "core_procesador"."proveedor_id", "core_procesador"."nombre", "core_procesador"."descripcion", "core_procesador"."precio", "core_procesador"."stock", "core_procesador"."imagen", "core_procesador"."socket", "core_procesador"."nucleos", "core_procesador"."frecuencia_base", "core_procesador"."potencia_referencia_watts", "core_procesador"."incluye_cooler", "core_procesador"."potencia_termica_referencia_watts", "core_procesador"."graficos_integrados" FROM "core_procesador" WHERE "core_procesador"."id" IN (161, 162, 163, 164, 165, 166, 167, 168, 169, 170);

-- consulta 2
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 2 LIMIT 21;

-- consulta 3
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 3 LIMIT 21;

-- consulta 4
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 4 LIMIT 21;

-- consulta 5
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 5 LIMIT 21;

-- consulta 6
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 6 LIMIT 21;

-- consulta 7
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 7 LIMIT 21;

-- consulta 8
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 8 LIMIT 21;

-- consulta 9
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 9 LIMIT 21;

-- consulta 10
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 10 LIMIT 21;

-- consulta 11
SELECT "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_proveedor" WHERE "core_proveedor"."id" = 11 LIMIT 21;

-- consulta 1
SELECT "core_procesador"."id", "core_procesador"."creado_en", "core_procesador"."actualizado_en", "core_procesador"."stock_minimo", "core_procesador"."stock_advertencia", "core_procesador"."en_oferta", "core_procesador"."precio_oferta", "core_procesador"."categoria", "core_procesador"."proveedor_id", "core_procesador"."nombre", "core_procesador"."descripcion", "core_procesador"."precio", "core_procesador"."stock", "core_procesador"."imagen", "core_procesador"."socket", "core_procesador"."nucleos", "core_procesador"."frecuencia_base", "core_procesador"."potencia_referencia_watts", "core_procesador"."incluye_cooler", "core_procesador"."potencia_termica_referencia_watts", "core_procesador"."graficos_integrados", "core_proveedor"."id", "core_proveedor"."nombre", "core_proveedor"."logo" FROM "core_procesador" INNER JOIN "core_proveedor" ON ("core_procesador"."proveedor_id" = "core_proveedor"."id") WHERE "core_procesador"."id" IN (161, 162, 163, 164, 165, 166, 167, 168, 169, 170);
