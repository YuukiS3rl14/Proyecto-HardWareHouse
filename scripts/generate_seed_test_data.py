#!/usr/bin/env python
"""
Genera data/seed_test_data.sql con regiones/comunas de Chile, proveedores y
el catálogo demo (100 modelos comerciales por categoría).

El archivo generado hace TRUNCATE de pedidos. Para actualizar un catálogo ya
cargado sin borrar pedidos, usa manage.py sincronizar_catalogo_demo.
"""
from __future__ import annotations

import json
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.demo_catalog_io import render_product_inserts

OUT = ROOT / "data" / "seed_test_data.sql"
PRODUCTS_PER_CATEGORY = 100

REGION_NUMERO_BY_KEY = {
    "arica": (15, "Arica y Parinacota"),
    "tarapac": (1, "Tarapacá"),
    "antofagasta": (2, "Antofagasta"),
    "atacama": (3, "Atacama"),
    "coquimbo": (4, "Coquimbo"),
    "valpara": (5, "Valparaíso"),
    "higgins": (6, "Libertador General Bernardo O'Higgins"),
    "maule": (7, "Maule"),
    "uble": (16, "Ñuble"),
    "biob": (8, "Biobío"),
    "araucan": (9, "La Araucanía"),
    "los rios": (14, "Los Ríos"),
    "los lagos": (10, "Los Lagos"),
    "aisen": (11, "Aysén del General Carlos Ibáñez del Campo"),
    "ays": (11, "Aysén del General Carlos Ibáñez del Campo"),
    "magallanes": (12, "Magallanes y de la Antártica Chilena"),
    "metropolitana": (13, "Región Metropolitana de Santiago"),
}


PROVEEDORES = [
    "Intel",
    "AMD",
    "NVIDIA",
    "ASUS",
    "Gigabyte",
    "MSI",
    "ASRock",
    "EVGA",
    "Zotac",
    "PNY",
    "Palit",
    "Gainward",
    "Sapphire",
    "PowerColor",
    "XFX",
    "Corsair",
    "G.Skill",
    "Kingston",
    "Crucial",
    "Samsung",
    "Western Digital",
    "Seagate",
    "SanDisk",
    "ADATA",
    "TeamGroup",
    "Patriot",
    "HyperX",
    "Thermaltake",
    "Cooler Master",
    "NZXT",
    "be quiet!",
    "Seasonic",
    "FSP",
    "Lian Li",
    "Fractal Design",
    "Phanteks",
    "Silverstone",
    "Antec",
    "Montech",
    "Noctua",
    "Arctic",
    "Deepcool",
    "ID-COOLING",
    "Scythe",
    "Logitech",
    "Razer",
    "SteelSeries",
    "BenQ",
    "LG",
    "AOC",
    "Dell",
    "HP",
    "Lenovo",
    "Acer",
    "Apple",
    "Qualcomm",
    "MediaTek",
    "Broadcom",
    "Realtek",
    "TP-Link",
    "D-Link",
    "Netgear",
    "Ubiquiti",
    "Synology",
    "QNAP",
    "ASUSTOR",
    "Toshiba",
    "Hitachi",
    "Lexar",
    "PNY Technologies",
    "Inno3D",
    "Colorful",
    "Biostar",
    "ECS",
    "Supermicro",
    "Tyan",
    "GALAX",
    "KFA2",
    "Club 3D",
    "VisionTek",
    "Matrox",
    "Intel Arc",
    "Sparkle",
]


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def fetch_chile_regions():
    url = (
        "https://raw.githubusercontent.com/juanbrujo/chile-regiones-comunas/"
        "main/data/original-simple.json"
    )
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    return payload["regiones"]


def _normalize_region_name(raw_name: str) -> str:
    text = unicodedata.normalize("NFKD", raw_name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def resolve_region(raw_name: str) -> tuple[int, str]:
    lowered = _normalize_region_name(raw_name)
    for key, pair in REGION_NUMERO_BY_KEY.items():
        if key in lowered:
            return pair
    raise ValueError(f"No se pudo mapear la región: {raw_name}")


def write_lines(handle, lines: list[str]) -> None:
    for line in lines:
        handle.write(line)
        if not line.endswith("\n"):
            handle.write("\n")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    chile = fetch_chile_regions()

    lines: list[str] = [
        "-- HardWareHouse: datos de prueba (regiones, comunas, proveedores, productos)\n",
        "-- Regenerar: python scripts/generate_seed_test_data.py\n",
        "-- Precios y stock de productos son sintéticos; no son un precio de mercado verificado.\n",
        "-- Este archivo hace TRUNCATE de pedidos, carritos y catálogo. No ejecutarlo en producción.\n",
        "-- Para corregir solo el catálogo demo sin borrar pedidos:\n",
        "--   python manage.py sincronizar_catalogo_demo --dry-run\n",
        "--   python manage.py sincronizar_catalogo_demo --apply\n",
        "SET client_encoding = 'UTF8';\n",
        "BEGIN;\n",
        "\n",
        "-- Este TRUNCATE borra pedidos, carritos y catálogo. No sirve para actualizar un catálogo ya cargado.\n",
        "TRUNCATE TABLE\n",
        "  core_itempedido,\n",
        "  core_pagoboleta,\n",
        "  core_pedido,\n",
        "  core_itemcarrito,\n",
        "  core_carrito,\n",
        "  core_favorito,\n",
        "  core_comentario,\n",
        "  core_ventilador,\n",
        "  core_refrigeracioncooler,\n",
        "  core_fuentedepoder,\n",
        "  core_gabinete,\n",
        "  core_almacenamientohdd,\n",
        "  core_almacenamientossd,\n",
        "  core_placamadre,\n",
        "  core_memoriaram,\n",
        "  core_tarjetagrafica,\n",
        "  core_procesador,\n",
        "  core_proveedor,\n",
        "  core_comuna,\n",
        "  core_region\n",
        "RESTART IDENTITY CASCADE;\n",
        "\n",
    ]

    region_id = 0
    comuna_id = 0
    region_rows = []
    comuna_rows = []

    seen_numeros: set[int] = set()
    for entry in chile:
        numero, nombre_oficial = resolve_region(entry["region"])
        if numero in seen_numeros:
            continue
        seen_numeros.add(numero)
        region_id += 1
        region_rows.append(
            f"({region_id}, {numero}, {sql_literal(nombre_oficial)})"
        )
        for comuna_nombre in entry["comunas"]:
            comuna_id += 1
            comuna_rows.append(
                f"({comuna_id}, {sql_literal(comuna_nombre)}, {region_id})"
            )

    lines.append(
        f"INSERT INTO core_region (id, numero, nombre) VALUES\n"
        + ",\n".join(region_rows)
        + ";\n\n"
    )
    lines.append(
        f"INSERT INTO core_comuna (id, nombre, region_id) VALUES\n"
        + ",\n".join(comuna_rows)
        + ";\n\n"
    )

    proveedor_rows = [
        f"({i + 1}, {sql_literal(nombre)}, NULL)" for i, nombre in enumerate(PROVEEDORES)
    ]
    lines.append(
        f"INSERT INTO core_proveedor (id, nombre, logo) VALUES\n"
        + ",\n".join(proveedor_rows)
        + ";\n\n"
    )

    n_prov = len(PROVEEDORES)

    lines.append(render_product_inserts())

    lines.append(
        "SELECT setval(pg_get_serial_sequence('core_region', 'id'), "
        "(SELECT COALESCE(MAX(id), 1) FROM core_region));\n"
    )
    lines.append(
        "SELECT setval(pg_get_serial_sequence('core_comuna', 'id'), "
        "(SELECT COALESCE(MAX(id), 1) FROM core_comuna));\n"
    )
    for table in [
        "core_proveedor",
        "core_procesador",
        "core_tarjetagrafica",
        "core_memoriaram",
        "core_placamadre",
        "core_almacenamientossd",
        "core_almacenamientohdd",
        "core_gabinete",
        "core_fuentedepoder",
        "core_refrigeracioncooler",
        "core_ventilador",
    ]:
        lines.append(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"(SELECT COALESCE(MAX(id), 1) FROM {table}));\n"
        )

    lines.append("\nCOMMIT;\n")

    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"Generado: {OUT}")
    print(f"Regiones: {region_id}, Comunas: {comuna_id}, Proveedores: {n_prov}")
    print(f"Productos por categoría: {PRODUCTS_PER_CATEGORY} (10 categorías)")


if __name__ == "__main__":
    main()
