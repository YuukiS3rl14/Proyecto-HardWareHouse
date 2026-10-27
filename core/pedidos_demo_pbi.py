"""Pedidos sintéticos para analítica. No llama a PayPal ni modifica stock."""
from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.db import connection, transaction
from django.db.models import Sum
from django.utils import timezone

from core.catalogo.registry import CATALOGO_MODELOS
from core.models import Comuna, ItemPedido, PagoBoleta, Pedido

PREFIJO = "DEMO-PBI-"
ZONA = ZoneInfo("America/Santiago")
HOSTS_LOCALES = {"", "localhost", "127.0.0.1", "::1"}
VENTANA_DIAS = 548

PESO_CATEGORIA = {
    "procesador": 12,
    "tarjeta_grafica": 14,
    "memoria_ram": 16,
    "placa_madre": 10,
    "almacenamiento_ssd": 18,
    "almacenamiento_hdd": 6,
    "gabinete": 8,
    "fuente_de_poder": 8,
    "refrigeracion": 6,
    "ventilador": 10,
}

NOMBRES = (
    "Camila", "Matías", "Sofía", "Benjamín", "Isidora", "Vicente", "Amanda", "Martín",
    "Florencia", "Tomás", "Josefa", "Agustín", "Emilia", "Diego", "Antonia", "Lucas",
)
APELLIDOS = (
    "González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva",
    "Martínez", "Sepúlveda", "Morales", "Rodríguez", "López", "Fuentes", "Hernández", "Torres",
)


class PedidosDemoError(Exception):
    pass


def exigir_base_local() -> tuple[str, str]:
    if connection.vendor != "postgresql":
        raise PedidosDemoError(
            "Los pedidos sintéticos se generan solo en PostgreSQL local. "
            f"La base actual es {connection.vendor!r}."
        )
    config = connection.settings_dict
    host = (config.get("HOST") or "").strip().lower()
    nombre = str(config.get("NAME") or "")
    if host not in HOSTS_LOCALES or "railway" in host or "rlwy.net" in host:
        raise PedidosDemoError(
            "La base configurada no es la PostgreSQL local de prueba "
            f"({host or 'sin host'} / {nombre}). No se modifica."
        )
    return host or "socket local", nombre


def transaccion_demo(indice: int) -> str:
    return f"{PREFIJO}{indice:06d}"


def _elegir(rng: random.Random, opciones: list, pesos: list[float]):
    total = sum(pesos)
    tiro = rng.random() * total
    acumulado = 0.0
    for opcion, peso in zip(opciones, pesos):
        acumulado += peso
        if tiro <= acumulado:
            return opcion
    return opciones[-1]


def peso_dia(fecha: date) -> float:
    peso = (0.82, 0.90, 0.95, 1.05, 1.35, 1.55, 1.25)[fecha.weekday()]
    mes, dia = fecha.month, fecha.day
    if mes == 3 and dia <= 20:
        peso *= 1.45
    if (mes == 5 and dia >= 25) or (mes == 6 and dia <= 5):
        peso *= 2.30
    if mes == 9 and 12 <= dia <= 20:
        peso *= 1.55
    if mes == 11 and dia >= 18:
        peso *= 2.50
    if mes == 12 and 8 <= dia <= 24:
        peso *= 1.85
    if mes in (1, 2):
        peso *= 0.72
    elif mes == 7:
        peso *= 0.90
    return peso


def _fecha_de(dia: date, hora: int, minuto: int) -> datetime:
    momento = datetime.combine(dia, time(hora, minuto), tzinfo=ZONA)
    return momento.astimezone(timezone.get_current_timezone())


def planificar_pedidos(productos: list[dict], comunas: list[tuple[int, str]], *, count: int, seed: int, fecha_fin: date) -> list[dict]:
    if count < 1:
        raise PedidosDemoError("La cantidad de pedidos debe ser al menos 1.")
    por_categoria: dict[str, list[dict]] = {}
    for producto in productos:
        if producto["precio"] <= 0:
            continue
        por_categoria.setdefault(producto["modelo"], []).append(producto)
    categorias = [nombre for nombre, peso in PESO_CATEGORIA.items() if por_categoria.get(nombre) and peso > 0]
    if not categorias:
        raise PedidosDemoError("No hay productos de catálogo con precio para armar pedidos.")

    rng = random.Random(seed)
    inicio = fecha_fin - timedelta(days=VENTANA_DIAS)
    dias = [inicio + timedelta(days=desplazamiento) for desplazamiento in range((fecha_fin - inicio).days + 1)]
    pesos_dias = [peso_dia(dia) for dia in dias]
    horas = list(range(9, 23))
    pesos_horas = [1, 1, 2, 2, 2, 3, 3, 4, 5, 6, 5, 4, 3, 2]
    n_clientes = max(5, count // 3)
    pesos_clientes = [1 / (indice ** 0.75) for indice in range(1, n_clientes + 1)]
    pesos_comuna = [_peso_comuna(nombre) for _, nombre in comunas] if comunas else []

    perfiles = []
    for indice in range(1, n_clientes + 1):
        comuna_id = _elegir(rng, [item[0] for item in comunas], pesos_comuna) if comunas else None
        perfiles.append({
            "username": f"demo-pbi-{indice:04d}",
            "email": f"demo-pbi-{indice:04d}@example.com",
            "first_name": NOMBRES[(indice - 1) % len(NOMBRES)],
            "last_name": APELLIDOS[((indice - 1) // len(NOMBRES)) % len(APELLIDOS)],
            "comuna_id": comuna_id,
        })

    planes = []
    for indice in range(1, count + 1):
        dia = _elegir(rng, dias, pesos_dias)
        hora = _elegir(rng, horas, pesos_horas)
        minuto = rng.randint(0, 59)
        cliente = _elegir(rng, perfiles, pesos_clientes)
        cantidad_lineas = rng.randint(1, 5)
        usados = set()
        items = []
        for _ in range(cantidad_lineas):
            producto = _elegir_producto(rng, por_categoria, categorias, usados)
            if producto is None:
                break
            usados.add((producto["modelo"], producto["pk"]))
            cantidad = _elegir(rng, [1, 2, 3], [78, 18, 4])
            precio = Decimal(producto["precio"]).quantize(Decimal("0.01"))
            items.append({
                "modelo": producto["modelo"],
                "pk": producto["pk"],
                "nombre": producto["nombre"][:200],
                "categoria": producto["categoria"][:50],
                "precio": precio,
                "cantidad": cantidad,
            })
        if not items:
            raise PedidosDemoError(f"No se pudo armar el pedido sintético {indice}.")
        total = sum((item["precio"] * item["cantidad"] for item in items), Decimal("0.00"))
        total = total.quantize(Decimal("0.01"))
        planes.append({
            "indice": indice,
            "transaccion_id": transaccion_demo(indice),
            "fecha": _fecha_de(dia, hora, minuto),
            "cliente": cliente,
            "direccion": f"Dirección sintética {PREFIJO}{cliente['username']}",
            "items": items,
            "total": total,
        })
    return planes


def _peso_comuna(region: str) -> float:
    texto = (region or "").lower()
    if "metropolitana" in texto:
        return 4.0
    if "valpara" in texto or "biob" in texto:
        return 1.6
    return 1.0


def _elegir_producto(rng, por_categoria, categorias, usados):
    pesos = [PESO_CATEGORIA[nombre] for nombre in categorias]
    for _ in range(6):
        categoria = _elegir(rng, categorias, pesos)
        candidatos = por_categoria[categoria]
        disponibles = [item for item in candidatos if (item["modelo"], item["pk"]) not in usados]
        if not disponibles:
            continue
        pesos_producto = [1 / (posicion ** 0.65) for posicion in range(1, len(disponibles) + 1)]
        return _elegir(rng, disponibles, pesos_producto)
    return None


def cargar_productos() -> list[dict]:
    productos = []
    for modelo, api in CATALOGO_MODELOS:
        filas = modelo.objects.values_list("pk", "nombre", "categoria", "precio").order_by("pk")
        for pk, nombre, categoria, precio in filas:
            productos.append({
                "modelo": api,
                "pk": pk,
                "nombre": nombre,
                "categoria": categoria,
                "precio": Decimal(precio).quantize(Decimal("0.01")),
            })
    return productos


def firma_stock() -> tuple:
    firma = []
    for modelo, api in CATALOGO_MODELOS:
        total = modelo.objects.aggregate(total=Sum("stock"))["total"] or 0
        firma.append((api, int(total)))
    return tuple(firma)


def firma_pedidos_reales() -> tuple:
    reales = []
    consulta = Pedido.objects.exclude(paypal_transaccion_id__startswith=PREFIJO).order_by("id")
    for pedido in consulta:
        boleta = PagoBoleta.objects.filter(pedido=pedido).values_list("transaccion_id", flat=True).first()
        if boleta and str(boleta).startswith(PREFIJO):
            continue
        reales.append((pedido.id, pedido.estado, str(pedido.total_monto), pedido.paypal_transaccion_id))
    return tuple(reales)


def generar_pedidos_demo(*, count: int, seed: int, apply: bool) -> dict:
    host, base = exigir_base_local()
    fecha_fin = timezone.localdate() - timedelta(days=1)
    productos = cargar_productos()
    comunas = list(Comuna.objects.order_by("id").values_list("id", "region__nombre"))
    planes = planificar_pedidos(productos, comunas, count=count, seed=seed, fecha_fin=fecha_fin)
    existentes = set(
        PagoBoleta.objects.filter(transaccion_id__startswith=PREFIJO).values_list("transaccion_id", flat=True)
    )
    pendientes = [plan for plan in planes if plan["transaccion_id"] not in existentes]
    resumen = {
        "apply": apply,
        "host": host,
        "base": base,
        "pedidos_plan": len(planes),
        "ya_existentes": len(planes) - len(pendientes),
        "por_crear": len(pendientes),
        "creados": 0,
        "clientes_nuevos": 0,
        "desde": planes[0]["fecha"] if planes else None,
        "hasta": planes[-1]["fecha"] if planes else None,
        "total_clp": sum((plan["total"] for plan in pendientes), Decimal("0.00")),
    }
    if planes:
        fechas = [plan["fecha"] for plan in planes]
        resumen["desde"] = min(fechas)
        resumen["hasta"] = max(fechas)
    if not apply:
        return resumen
    if not pendientes:
        problemas = auditar_pedidos_demo(count)
        if problemas:
            raise PedidosDemoError("Los pedidos sintéticos quedaron inconsistentes: " + " ".join(problemas[:8]))
        return resumen

    stock_antes = firma_stock()
    reales_antes = firma_pedidos_reales()
    with transaction.atomic():
        usuarios = _asegurar_clientes(pendientes)
        resumen["clientes_nuevos"] = usuarios["nuevos"]
        _insertar(pendientes, usuarios["ids"])
        resumen["creados"] = len(pendientes)
        problemas = auditar_pedidos_demo(count)
        if problemas:
            raise PedidosDemoError("Los pedidos sintéticos quedaron inconsistentes: " + " ".join(problemas[:8]))
        if firma_stock() != stock_antes:
            raise PedidosDemoError("La generación cambió el stock del catálogo. Se revierte.")
        if firma_pedidos_reales() != reales_antes:
            raise PedidosDemoError("La generación modificó pedidos que no son DEMO-PBI. Se revierte.")
    return resumen


def _asegurar_clientes(planes: list[dict]) -> dict:
    perfiles = {}
    for plan in planes:
        perfiles[plan["cliente"]["username"]] = plan["cliente"]
    nuevos = 0
    ids = {}
    for username in sorted(perfiles):
        perfil = perfiles[username]
        usuario, creado = User.objects.get_or_create(
            username=username,
            defaults={
                "email": perfil["email"],
                "first_name": perfil["first_name"],
                "last_name": perfil["last_name"],
            },
        )
        if creado:
            usuario.set_unusable_password()
            usuario.save(update_fields=["password"])
            nuevos += 1
        ids[username] = usuario.id
    return {"ids": ids, "nuevos": nuevos}


def _insertar(planes: list[dict], usuarios: dict[str, int]) -> None:
    pedidos = [
        Pedido(
            usuario_id=usuarios[plan["cliente"]["username"]],
            fecha_pedido=plan["fecha"],
            total_monto=plan["total"],
            direccion_envio=plan["direccion"][:255],
            comuna_envio_id=plan["cliente"]["comuna_id"],
            estado="PAGADO",
            paypal_transaccion_id=plan["transaccion_id"],
        )
        for plan in planes
    ]
    pedidos = Pedido.objects.bulk_create(pedidos, batch_size=500)
    items = []
    boletas = []
    for pedido, plan in zip(pedidos, planes):
        for item in plan["items"]:
            items.append(ItemPedido(
                pedido_id=pedido.id,
                producto_nombre=item["nombre"],
                producto_tipo=item["categoria"],
                precio_unitario=item["precio"],
                cantidad=item["cantidad"],
                producto_modelo=item["modelo"],
                producto_pk=item["pk"],
            ))
        boletas.append(PagoBoleta(
            pedido_id=pedido.id,
            monto_pagado=plan["total"],
            metodo_pago="DEMO-PBI",
            transaccion_id=plan["transaccion_id"],
            nombre_comprador=f"{plan['cliente']['first_name']} {plan['cliente']['last_name']}"[:200],
            email_comprador=plan["cliente"]["email"],
        ))
    ItemPedido.objects.bulk_create(items, batch_size=1000)
    boletas = PagoBoleta.objects.bulk_create(boletas, batch_size=500)
    for boleta, plan in zip(boletas, planes):
        boleta.fecha_pago = plan["fecha"]
    PagoBoleta.objects.bulk_update(boletas, ["fecha_pago"], batch_size=500)


def auditar_pedidos_demo(count: int | None = None) -> list[str]:
    problemas = []
    boletas = list(
        PagoBoleta.objects.filter(transaccion_id__startswith=PREFIJO)
        .select_related("pedido")
        .prefetch_related("pedido__items_pedido")
    )
    existentes = {
        api: set(modelo.objects.values_list("pk", flat=True))
        for modelo, api in CATALOGO_MODELOS
    }
    if count is not None and len(boletas) < count:
        problemas.append(f"hay {len(boletas)} boletas demo y se esperaban al menos {count}.")
    vistos = set()
    for boleta in boletas:
        if boleta.transaccion_id in vistos:
            problemas.append(f"transacción duplicada {boleta.transaccion_id}.")
        vistos.add(boleta.transaccion_id)
        pedido = boleta.pedido
        if pedido is None:
            problemas.append(f"{boleta.transaccion_id} no tiene pedido.")
            continue
        if pedido.estado != "PAGADO":
            problemas.append(f"el pedido de {boleta.transaccion_id} está {pedido.estado}.")
        if pedido.paypal_transaccion_id != boleta.transaccion_id:
            problemas.append(f"{boleta.transaccion_id} no coincide con el pedido.")
        if Decimal(boleta.monto_pagado) != Decimal(pedido.total_monto):
            problemas.append(f"el monto de {boleta.transaccion_id} no coincide con el pedido.")
        if not str(boleta.transaccion_id).startswith(PREFIJO):
            problemas.append(f"transacción sin prefijo: {boleta.transaccion_id}.")
        items = list(pedido.items_pedido.all())
        if not 1 <= len(items) <= 5:
            problemas.append(f"{boleta.transaccion_id} tiene {len(items)} ítems.")
        suma = Decimal("0.00")
        for item in items:
            if item.cantidad < 1:
                problemas.append(f"cantidad inválida en {boleta.transaccion_id}.")
            subtotal = (Decimal(item.precio_unitario) * item.cantidad).quantize(Decimal("0.01"))
            suma += subtotal
            if item.producto_pk not in existentes.get(item.producto_modelo, ()):
                problemas.append(f"ítem huérfano en {boleta.transaccion_id}.")
        if suma.quantize(Decimal("0.01")) != Decimal(pedido.total_monto).quantize(Decimal("0.01")):
            problemas.append(f"los ítems de {boleta.transaccion_id} no suman el total.")
    huerfanos = Pedido.objects.filter(
        paypal_transaccion_id__startswith=PREFIJO,
        pago_boleta__isnull=True,
    ).count()
    if huerfanos:
        problemas.append(f"{huerfanos} pedidos demo no tienen boleta.")
    return problemas
