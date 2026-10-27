"""Sincroniza solo filas demo del catálogo. No toca pedidos ni registros reales."""
from __future__ import annotations

from decimal import Decimal

from django.db import connection, transaction

from core.catalogo.registry import MODEL_BY_API_NAME
from core.models import Proveedor

HOSTS_LOCALES = {"", "localhost", "127.0.0.1", "::1"}


class CatalogoDemoError(Exception):
    pass


def exigir_base_local() -> tuple[str, str]:
    if connection.vendor != "postgresql":
        raise CatalogoDemoError(
            "La sincronización del catálogo demo requiere PostgreSQL. "
            f"La base actual es {connection.vendor!r}."
        )
    config = connection.settings_dict
    host = (config.get("HOST") or "").strip().lower()
    nombre = str(config.get("NAME") or "")
    if host not in HOSTS_LOCALES or "railway" in host or "rlwy.net" in host:
        raise CatalogoDemoError(
            "La base configurada no es la PostgreSQL local de prueba "
            f"({host or 'sin host'} / {nombre}). No se modifica."
        )
    return host or "socket local", nombre


def es_fila_demo(nombre: str, descripcion: str, nombre_destino: str) -> bool:
    if (nombre or "") == nombre_destino:
        return True
    texto = f" {(nombre or '').lower()} {(descripcion or '').lower()} "
    return (
        "serie test" in texto
        or " de prueba" in texto
        or " test " in texto
        or "sintéticos de demostración" in texto
        or "sinteticos de demostracion" in texto
    )


def _mismo(actual, esperado) -> bool:
    if isinstance(esperado, Decimal):
        if actual is None:
            return False
        return Decimal(actual) == Decimal(esperado)
    return actual == esperado


def _igual(obj, fila: dict) -> bool:
    if obj.proveedor.nombre != fila["marca"]:
        return False
    if obj.categoria != fila["categoria"] or obj.nombre != fila["nombre"]:
        return False
    if (obj.descripcion or "") != fila["descripcion"] or obj.stock != fila["stock"]:
        return False
    if not _mismo(obj.precio, fila["precio"]):
        return False
    for campo, valor in fila["campos"].items():
        if not _mismo(getattr(obj, campo), valor):
            return False
    return True


def _asignar(obj, fila: dict, proveedor: Proveedor) -> None:
    obj.proveedor = proveedor
    obj.categoria = fila["categoria"]
    obj.nombre = fila["nombre"]
    obj.descripcion = fila["descripcion"]
    obj.precio = fila["precio"]
    obj.stock = fila["stock"]
    for campo, valor in fila["campos"].items():
        setattr(obj, campo, valor)


def sincronizar_filas(filas: list[dict], *, apply: bool) -> dict:
    host, base = exigir_base_local()
    resumen = {
        "apply": apply,
        "host": host,
        "base": base,
        "proveedores_creados": [],
        "insertados": 0,
        "actualizados": 0,
        "sin_cambios": 0,
        "omitidos": [],
    }

    def _trabajo():
        marcas = sorted({fila["marca"] for fila in filas})
        existentes = set(
            Proveedor.objects.filter(nombre__in=marcas).values_list("nombre", flat=True)
        )
        faltantes = [marca for marca in marcas if marca not in existentes]
        resumen["proveedores_creados"] = faltantes
        if apply:
            for marca in faltantes:
                Proveedor.objects.create(nombre=marca)
        proveedores = {
            proveedor.nombre: proveedor
            for proveedor in Proveedor.objects.filter(nombre__in=marcas)
        }

        for fila in filas:
            modelo = MODEL_BY_API_NAME[fila["modelo"]]
            consulta = modelo.objects.select_for_update() if apply else modelo.objects.all()
            obj = consulta.filter(pk=fila["pk"]).first()
            if obj is None:
                resumen["insertados"] += 1
                if apply:
                    nuevo = modelo(pk=fila["pk"])
                    _asignar(nuevo, fila, proveedores[fila["marca"]])
                    nuevo.full_clean()
                    nuevo.save(force_insert=True)
                continue
            if not es_fila_demo(obj.nombre, obj.descripcion, fila["nombre"]):
                resumen["omitidos"].append(
                    {"modelo": fila["modelo"], "pk": fila["pk"], "nombre": obj.nombre}
                )
                continue
            if apply and fila["marca"] not in proveedores:
                raise CatalogoDemoError(f"No existe el proveedor {fila['marca']}.")
            if obj is not None and fila["marca"] in proveedores and _igual(obj, fila):
                resumen["sin_cambios"] += 1
                continue
            if not apply and fila["marca"] not in proveedores:
                resumen["actualizados"] += 1
                continue
            resumen["actualizados"] += 1
            if apply:
                _asignar(obj, fila, proveedores[fila["marca"]])
                obj.full_clean()
                obj.save(
                    update_fields=[
                        "proveedor",
                        "categoria",
                        "nombre",
                        "descripcion",
                        "precio",
                        "stock",
                        *fila["campos"].keys(),
                    ]
                )

        if apply:
            _actualizar_secuencias()
            _auditar(filas, resumen["omitidos"])

    if apply:
        with transaction.atomic():
            _trabajo()
    else:
        _trabajo()
    return resumen


def _nombre_de_prueba(nombre: str) -> bool:
    texto = f" {(nombre or '').lower()} "
    return "serie test" in texto or " test " in texto


def _actualizar_secuencias() -> None:
    from core.demo_catalog import TABLAS

    tablas = ["core_proveedor", *TABLAS.values()]
    with connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                f"(SELECT COALESCE(MAX(id), 1) FROM {tabla}))"
            )


def _auditar(filas: list[dict], omitidos: list[dict]) -> None:
    omitidos_clave = {(item["modelo"], item["pk"]) for item in omitidos}
    problemas = []
    for fila in filas:
        clave = (fila["modelo"], fila["pk"])
        if clave in omitidos_clave:
            continue
        obj = MODEL_BY_API_NAME[fila["modelo"]].objects.select_related("proveedor").get(pk=fila["pk"])
        if _nombre_de_prueba(obj.nombre):
            problemas.append(f"{clave[0]}:{clave[1]} conserva un nombre de prueba.")
        elif obj.proveedor.nombre != fila["marca"] or not _igual(obj, fila):
            problemas.append(f"{clave[0]}:{clave[1]} no quedó alineado con la fuente.")
    if problemas:
        raise CatalogoDemoError("La sincronización no quedó consistente: " + " ".join(problemas[:8]))
