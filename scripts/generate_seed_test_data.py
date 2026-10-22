#!/usr/bin/env python
"""
Genera data/seed_test_data.sql con regiones/comunas de Chile, proveedores y
productos de prueba (100 por categoría de hardware).
"""
from __future__ import annotations

import json
import unicodedata
import urllib.request
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
        "SET client_encoding = 'UTF8';\n",
        "BEGIN;\n",
        "\n",
        "-- Limpia tablas de catálogo (y dependencias de carrito/pedidos sobre productos).\n",
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

    def prov(i: int) -> int:
        return (i % n_prov) + 1

    # --- Procesadores ---
    cpu_rows = []
    sockets = ["AM4", "AM5", "LGA1700", "LGA1200"]
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        brand = PROVEEDORES[(i - 1) % n_prov]
        socket = sockets[(i - 1) % len(sockets)]
        nucleos = 4 + (i % 17)
        ghz = Decimal("2.50") + Decimal(i % 30) / Decimal("10")
        precio = Decimal("89990") + Decimal(i * 1250)
        nombre = f"{brand} CPU Serie Test {i:03d} {nucleos}c"
        cpu_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("CPU"),
                    str(prov(i)),
                    sql_literal(nombre),
                    sql_literal(f"Procesador de prueba #{i} para catálogo HardWareHouse."),
                    str(precio),
                    str(5 + (i % 40)),
                    "NULL",
                    sql_literal(socket),
                    str(nucleos),
                    str(ghz),
                    str(65 + (i % 120)),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_procesador "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES\n"
        + ",\n".join(cpu_rows)
        + ";\n\n"
    )

    # --- GPU ---
    gpu_rows = []
    vrams = [4, 6, 8, 10, 12, 16, 24]
    mem_types = ["GDDR6", "GDDR6X", "GDDR5"]
    buses = ["PCIe 4.0", "PCIe 3.0", "PCIe 5.0"]
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        brand = PROVEEDORES[(i + 3) % n_prov]
        nombre = f"{brand} GPU Test {i:03d}"
        gpu_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Tarjeta Gráfica"),
                    str(prov(i + 1)),
                    sql_literal(nombre),
                    sql_literal(f"Tarjeta gráfica de prueba #{i}."),
                    str(Decimal("149990") + Decimal(i * 3500)),
                    str(3 + (i % 25)),
                    "NULL",
                    str(vrams[i % len(vrams)]),
                    sql_literal(mem_types[i % len(mem_types)]),
                    sql_literal(buses[i % len(buses)]),
                    str(120 + (i % 200)),
                    str(450 + (i % 400)),
                    str(240 + (i % 120)),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_tarjetagrafica "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, "
        "potencia_minima_fuente_watts, largo_mm) VALUES\n"
        + ",\n".join(gpu_rows)
        + ";\n\n"
    )

    # --- RAM ---
    ram_rows = []
    ddr = ["DDR4", "DDR5", "DDR3"]
    fmt = ["DIMM", "SO-DIMM"]
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        cap = [8, 16, 32, 64][i % 4]
        mod = [1, 2, 4][i % 3]
        mod_gb = cap // mod
        nombre = f"{PROVEEDORES[(i + 5) % n_prov]} RAM Test {cap}GB Kit {i:03d}"
        ram_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Memoria RAM"),
                    str(prov(i + 2)),
                    sql_literal(nombre),
                    sql_literal(f"Módulo RAM de prueba #{i}."),
                    str(Decimal("29990") + Decimal(i * 890)),
                    str(10 + (i % 50)),
                    "NULL",
                    str(cap),
                    sql_literal(ddr[i % len(ddr)]),
                    str(2400 + (i % 20) * 200),
                    str(mod),
                    str(mod_gb),
                    sql_literal(fmt[i % len(fmt)]),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_memoriaram "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, "
        "capacidad_modulo_gb, formato_ram) VALUES\n"
        + ",\n".join(ram_rows)
        + ";\n\n"
    )

    # --- Placa madre ---
    mb_rows = []
    chipsets = ["B550", "B650", "Z790", "X670", "Otro"]
    formatos = ["ATX", "Micro-ATX", "Mini-ITX"]
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        socket = sockets[i % len(sockets)]
        nombre = f"{PROVEEDORES[(i + 7) % n_prov]} Motherboard Test {i:03d}"
        mb_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Placa Madre"),
                    str(prov(i + 3)),
                    sql_literal(nombre),
                    sql_literal(f"Placa madre de prueba #{i}."),
                    str(Decimal("99990") + Decimal(i * 2100)),
                    str(4 + (i % 30)),
                    "NULL",
                    sql_literal(socket),
                    sql_literal(chipsets[i % len(chipsets)]),
                    sql_literal(formatos[i % len(formatos)]),
                    str(2 + (i % 3)),
                    sql_literal(ddr[i % 2]),
                    sql_literal(fmt[0]),
                    str(64 + (i % 4) * 32),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_placamadre "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, "
        "formato_ram_soportado, capacidad_maxima_ram_gb) VALUES\n"
        + ",\n".join(mb_rows)
        + ";\n\n"
    )

    # --- SSD ---
    ssd_rows = []
    ssd_if = ["NVMe PCIe 4.0", "NVMe PCIe 3.0", "SATA III"]
    ssd_fmt = ["M.2 2280", '2.5"']
    caps = [256, 512, 1024, 2048, 4096]
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        nombre = f"{PROVEEDORES[(i + 9) % n_prov]} SSD Test {i:03d}"
        ssd_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("SSD"),
                    str(prov(i + 4)),
                    sql_literal(nombre),
                    sql_literal(f"SSD de prueba #{i}."),
                    str(Decimal("39990") + Decimal(i * 1500)),
                    str(8 + (i % 60)),
                    "NULL",
                    str(caps[i % len(caps)]),
                    sql_literal(ssd_if[i % len(ssd_if)]),
                    sql_literal(ssd_fmt[i % len(ssd_fmt)]),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_almacenamientossd "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "capacidad_gb, interfaz, formato) VALUES\n"
        + ",\n".join(ssd_rows)
        + ";\n\n"
    )

    # --- HDD ---
    hdd_rows = []
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        nombre = f"{PROVEEDORES[(i + 11) % n_prov]} HDD Test {i:03d}"
        hdd_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Disco Duro HDD"),
                    str(prov(i + 5)),
                    sql_literal(nombre),
                    sql_literal(f"Disco HDD de prueba #{i}."),
                    str(Decimal("49990") + Decimal(i * 980)),
                    str(6 + (i % 35)),
                    "NULL",
                    str([1000, 2000, 4000, 8000][i % 4]),
                    str(5400 if i % 2 else 7200),
                    str(64 + (i % 256)),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_almacenamientohdd "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "capacidad_gb, velocidad_rpm, cache_mb) VALUES\n"
        + ",\n".join(hdd_rows)
        + ";\n\n"
    )

    # --- Gabinete ---
    case_rows = []
    mats = ["Acero", "Aluminio", "Vidrio Templado", "Plástico"]
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        nombre = f"{PROVEEDORES[(i + 13) % n_prov]} Case Test {i:03d}"
        case_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Gabinete"),
                    str(prov(i + 6)),
                    sql_literal(nombre),
                    sql_literal(f"Gabinete de prueba #{i}."),
                    str(Decimal("59990") + Decimal(i * 1100)),
                    str(5 + (i % 20)),
                    "NULL",
                    sql_literal(formatos[i % len(formatos)]),
                    sql_literal(i % 2 == 0),
                    sql_literal(mats[i % len(mats)]),
                    str(300 + (i % 150)),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_gabinete "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES\n"
        + ",\n".join(case_rows)
        + ";\n\n"
    )

    # --- PSU ---
    psu_rows = []
    certs = [
        "80+ White",
        "80+ Bronze",
        "80+ Silver",
        "80+ Gold",
        "80+ Platinum",
        "80+ Titanium",
    ]
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        nombre = f"{PROVEEDORES[(i + 15) % n_prov]} PSU Test {i:03d}"
        psu_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Fuente de Poder"),
                    str(prov(i + 7)),
                    sql_literal(nombre),
                    sql_literal(f"Fuente de poder de prueba #{i}."),
                    str(Decimal("69990") + Decimal(i * 1300)),
                    str(7 + (i % 25)),
                    "NULL",
                    str(450 + (i % 6) * 100),
                    sql_literal(certs[i % len(certs)]),
                    sql_literal(i % 3 != 0),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_fuentedepoder "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "potencia_watts, certificacion, modular) VALUES\n"
        + ",\n".join(psu_rows)
        + ";\n\n"
    )

    # --- Cooler ---
    cool_rows = []
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        tipo = "Aire" if i % 3 else "Líquida (AIO)"
        nombre = f"{PROVEEDORES[(i + 17) % n_prov]} Cooler Test {i:03d}"
        rad = "NULL" if tipo == "Aire" else str(120 + (i % 3) * 120)
        cool_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Refrigeración"),
                    str(prov(i + 8)),
                    sql_literal(nombre),
                    sql_literal(f"Refrigeración de prueba #{i}."),
                    str(Decimal("24990") + Decimal(i * 750)),
                    str(9 + (i % 40)),
                    "NULL",
                    sql_literal(tipo),
                    sql_literal("AM4, AM5, LGA1700"),
                    rad,
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_refrigeracioncooler "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "tipo, socket_compatibles, tamanho_radiador_mm) VALUES\n"
        + ",\n".join(cool_rows)
        + ";\n\n"
    )

    # --- Ventilador ---
    fan_rows = []
    for i in range(1, PRODUCTS_PER_CATEGORY + 1):
        nombre = f"{PROVEEDORES[(i + 19) % n_prov]} Fan Test {i:03d}"
        fan_rows.append(
            "("
            + ", ".join(
                [
                    str(i),
                    sql_literal("Ventilador"),
                    str(prov(i + 9)),
                    sql_literal(nombre),
                    sql_literal(f"Ventilador de prueba #{i}."),
                    str(Decimal("9990") + Decimal(i * 190)),
                    str(15 + (i % 80)),
                    "NULL",
                    str(120 if i % 2 else 140),
                    str(800 + (i % 12) * 100),
                    sql_literal(i % 2 == 0),
                ]
            )
            + ")"
        )
    lines.append(
        "INSERT INTO core_ventilador "
        "(id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, "
        "tamanho_mm, velocidad_rpm, rgb) VALUES\n"
        + ",\n".join(fan_rows)
        + ";\n\n"
    )

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
