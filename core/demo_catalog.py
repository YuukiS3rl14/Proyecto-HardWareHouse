"""Catálogo demo con modelos comerciales y especificaciones coherentes.

Los precios y el stock son sintéticos. No son precios de mercado verificados.
"""
from __future__ import annotations

from decimal import Decimal

NOTA_SINTETICA = (
    "Precio y stock sintéticos de demostración; no son un precio de mercado verificado. "
)

CATEGORIAS = {
    "procesador": "CPU",
    "tarjeta_grafica": "Tarjeta Gráfica",
    "memoria_ram": "Memoria RAM",
    "placa_madre": "Placa Madre",
    "almacenamiento_ssd": "SSD",
    "almacenamiento_hdd": "Disco Duro HDD",
    "gabinete": "Gabinete",
    "fuente_de_poder": "Fuente de Poder",
    "refrigeracion": "Refrigeración",
    "ventilador": "Ventilador",
}

TABLAS = {
    "procesador": "core_procesador",
    "tarjeta_grafica": "core_tarjetagrafica",
    "memoria_ram": "core_memoriaram",
    "placa_madre": "core_placamadre",
    "almacenamiento_ssd": "core_almacenamientossd",
    "almacenamiento_hdd": "core_almacenamientohdd",
    "gabinete": "core_gabinete",
    "fuente_de_poder": "core_fuentedepoder",
    "refrigeracion": "core_refrigeracioncooler",
    "ventilador": "core_ventilador",
}

COLUMNAS = {
    "procesador": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "socket", "nucleos", "frecuencia_base", "potencia_referencia_watts",
    ),
    "tarjeta_grafica": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "vram_gb", "tipo_memoria", "interfaz", "consumo_referencia_watts",
        "potencia_minima_fuente_watts", "largo_mm",
    ),
    "memoria_ram": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "capacidad_gb", "tipo_ddr", "velocidad_mhz", "modulos_por_producto",
        "capacidad_modulo_gb", "formato_ram",
    ),
    "placa_madre": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "socket_cpu", "chipset", "formato", "ranuras_ram", "tipo_ram_soportado",
        "formato_ram_soportado", "capacidad_maxima_ram_gb",
    ),
    "almacenamiento_ssd": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "capacidad_gb", "interfaz", "formato",
    ),
    "almacenamiento_hdd": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "capacidad_gb", "velocidad_rpm", "cache_mb",
    ),
    "gabinete": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "formato_soporte", "ventiladores_incluidos", "material", "largo_max_gpu_mm",
    ),
    "fuente_de_poder": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "potencia_watts", "certificacion", "modular",
    ),
    "refrigeracion": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "tipo", "socket_compatibles", "tamanho_radiador_mm",
    ),
    "ventilador": (
        "id", "categoria", "proveedor_id", "nombre", "descripcion", "precio", "stock", "imagen",
        "tamanho_mm", "velocidad_rpm", "rgb",
    ),
}

SOCKET_POR_CHIPSET = {
    "B550": ("AM4", "DDR4", 128),
    "B650": ("AM5", "DDR5", 192),
    "X670": ("AM5", "DDR5", 192),
    "Z790": ("LGA1700", "DDR5", 192),
}

CPU_AMD = {"AMD"}
CPU_INTEL = {"Intel"}
SOCKET_AMD = {"AM4", "AM5"}
SOCKET_INTEL = {"LGA1200", "LGA1700"}


def nombre_comercial(marca: str, nombre: str) -> str:
    """Evita repetir la marca cuando el modelo ya la incluye."""
    prefijo = f"{marca} "
    if nombre.lower().startswith(prefijo.lower()):
        return nombre
    return f"{prefijo}{nombre}"


def _stock(pk: int) -> int:
    return 4 + (pk % 12)


def _precio(base: int, pk: int) -> Decimal:
    return Decimal(base + (pk % 5) * 1000).quantize(Decimal("0.01"))


def _desc(texto: str) -> str:
    return NOTA_SINTETICA + texto


def _fila(modelo: str, pk: int, marca: str, nombre: str, detalle: str, precio_base: int, campos: dict) -> dict:
    return {
        "modelo": modelo,
        "pk": pk,
        "marca": marca,
        "categoria": CATEGORIAS[modelo],
        "nombre": nombre,
        "descripcion": _desc(detalle),
        "precio": _precio(precio_base, pk),
        "stock": _stock(pk),
        "campos": campos,
    }


def _enumerar(modelo: str, filas: list[dict]) -> list[dict]:
    if len(filas) != 100:
        raise ValueError(f"{modelo} debe tener 100 productos, tiene {len(filas)}")
    salida = []
    for pk, fila in enumerate(filas, start=1):
        fila = dict(fila)
        fila["modelo"] = modelo
        fila["pk"] = pk
        fila["precio"] = _precio(int(fila.pop("precio_base")), pk)
        fila["stock"] = _stock(pk)
        fila["descripcion"] = _desc(fila.pop("detalle"))
        fila["categoria"] = CATEGORIAS[modelo]
        salida.append(fila)
    return salida


def _cpus() -> list[dict]:
    # marca, nombre, socket, nucleos, ghz, watts, precio base
    raw = [
        ("AMD", "Ryzen 3 3100", "AM4", 4, "3.60", 65, 89990),
        ("AMD", "Ryzen 3 3300X", "AM4", 4, "3.80", 65, 109990),
        ("AMD", "Ryzen 3 3200G", "AM4", 4, "3.60", 65, 99990),
        ("AMD", "Ryzen 5 3600", "AM4", 6, "3.60", 65, 129990),
        ("AMD", "Ryzen 5 3600X", "AM4", 6, "3.80", 95, 149990),
        ("AMD", "Ryzen 5 3600XT", "AM4", 6, "3.80", 95, 159990),
        ("AMD", "Ryzen 5 4500", "AM4", 6, "3.60", 65, 99990),
        ("AMD", "Ryzen 5 4600G", "AM4", 6, "3.70", 65, 119990),
        ("AMD", "Ryzen 5 5500", "AM4", 6, "3.60", 65, 109990),
        ("AMD", "Ryzen 5 5600", "AM4", 6, "3.50", 65, 129990),
        ("AMD", "Ryzen 5 5600X", "AM4", 6, "3.70", 65, 159990),
        ("AMD", "Ryzen 5 5600G", "AM4", 6, "3.90", 65, 149990),
        ("AMD", "Ryzen 7 3700X", "AM4", 8, "3.60", 65, 199990),
        ("AMD", "Ryzen 7 3800X", "AM4", 8, "3.90", 105, 229990),
        ("AMD", "Ryzen 7 3800XT", "AM4", 8, "3.90", 105, 239990),
        ("AMD", "Ryzen 7 5700", "AM4", 8, "3.70", 65, 179990),
        ("AMD", "Ryzen 7 5700X", "AM4", 8, "3.40", 65, 199990),
        ("AMD", "Ryzen 7 5700G", "AM4", 8, "3.80", 65, 189990),
        ("AMD", "Ryzen 7 5800X", "AM4", 8, "3.80", 105, 249990),
        ("AMD", "Ryzen 7 5800X3D", "AM4", 8, "3.40", 105, 299990),
        ("AMD", "Ryzen 9 3900X", "AM4", 12, "3.80", 105, 329990),
        ("AMD", "Ryzen 9 3900XT", "AM4", 12, "3.80", 105, 349990),
        ("AMD", "Ryzen 9 3950X", "AM4", 16, "3.50", 105, 449990),
        ("AMD", "Ryzen 9 5900X", "AM4", 12, "3.70", 105, 349990),
        ("AMD", "Ryzen 9 5950X", "AM4", 16, "3.40", 105, 499990),
        ("AMD", "Ryzen 5 7500F", "AM5", 6, "3.70", 65, 159990),
        ("AMD", "Ryzen 5 7600", "AM5", 6, "3.80", 65, 199990),
        ("AMD", "Ryzen 5 7600X", "AM5", 6, "4.70", 105, 229990),
        ("AMD", "Ryzen 5 7600X3D", "AM5", 6, "4.10", 65, 249990),
        ("AMD", "Ryzen 5 8400F", "AM5", 6, "4.20", 65, 139990),
        ("AMD", "Ryzen 5 8500G", "AM5", 6, "3.50", 65, 169990),
        ("AMD", "Ryzen 5 8600G", "AM5", 6, "4.30", 65, 189990),
        ("AMD", "Ryzen 5 9600X", "AM5", 6, "3.90", 65, 249990),
        ("AMD", "Ryzen 7 7700", "AM5", 8, "3.80", 65, 279990),
        ("AMD", "Ryzen 7 7700X", "AM5", 8, "4.50", 105, 319990),
        ("AMD", "Ryzen 7 7800X3D", "AM5", 8, "4.20", 120, 399990),
        ("AMD", "Ryzen 7 8700F", "AM5", 8, "4.10", 65, 219990),
        ("AMD", "Ryzen 7 8700G", "AM5", 8, "4.20", 65, 279990),
        ("AMD", "Ryzen 7 9700X", "AM5", 8, "3.80", 65, 359990),
        ("AMD", "Ryzen 7 9800X3D", "AM5", 8, "4.70", 120, 499990),
        ("AMD", "Ryzen 9 7900", "AM5", 12, "3.70", 65, 399990),
        ("AMD", "Ryzen 9 7900X", "AM5", 12, "4.70", 170, 449990),
        ("AMD", "Ryzen 9 7900X3D", "AM5", 12, "4.40", 120, 499990),
        ("AMD", "Ryzen 9 9900X", "AM5", 12, "4.40", 120, 479990),
        ("AMD", "Ryzen 9 9900X3D", "AM5", 12, "4.40", 120, 549990),
        ("AMD", "Ryzen 9 7950X", "AM5", 16, "4.50", 170, 549990),
        ("AMD", "Ryzen 9 7950X3D", "AM5", 16, "4.20", 120, 599990),
        ("AMD", "Ryzen 9 9950X", "AM5", 16, "4.30", 170, 649990),
        ("AMD", "Ryzen 9 9950X3D", "AM5", 16, "4.30", 170, 749990),
        ("AMD", "Ryzen 5 8600F", "AM5", 6, "4.30", 65, 149990),
        ("Intel", "Core i3-10100", "LGA1200", 4, "3.60", 65, 99990),
        ("Intel", "Core i3-10100F", "LGA1200", 4, "3.60", 65, 89990),
        ("Intel", "Core i3-10105", "LGA1200", 4, "3.70", 65, 109990),
        ("Intel", "Core i3-10300", "LGA1200", 4, "3.70", 65, 119990),
        ("Intel", "Core i3-10320", "LGA1200", 4, "3.80", 65, 129990),
        ("Intel", "Core i5-10400", "LGA1200", 6, "2.90", 65, 149990),
        ("Intel", "Core i5-10400F", "LGA1200", 6, "2.90", 65, 129990),
        ("Intel", "Core i5-10500", "LGA1200", 6, "3.10", 65, 169990),
        ("Intel", "Core i5-10600", "LGA1200", 6, "3.30", 65, 179990),
        ("Intel", "Core i5-10600K", "LGA1200", 6, "4.10", 125, 199990),
        ("Intel", "Core i5-11400", "LGA1200", 6, "2.60", 65, 169990),
        ("Intel", "Core i5-11400F", "LGA1200", 6, "2.60", 65, 149990),
        ("Intel", "Core i5-11500", "LGA1200", 6, "2.70", 65, 179990),
        ("Intel", "Core i5-11600K", "LGA1200", 6, "3.90", 125, 229990),
        ("Intel", "Core i7-10700", "LGA1200", 8, "2.90", 65, 249990),
        ("Intel", "Core i7-10700F", "LGA1200", 8, "2.90", 65, 229990),
        ("Intel", "Core i7-10700K", "LGA1200", 8, "3.80", 125, 279990),
        ("Intel", "Core i7-11700", "LGA1200", 8, "2.50", 65, 269990),
        ("Intel", "Core i7-11700K", "LGA1200", 8, "3.60", 125, 299990),
        ("Intel", "Core i9-10850K", "LGA1200", 10, "3.60", 125, 349990),
        ("Intel", "Core i9-10900", "LGA1200", 10, "2.80", 65, 339990),
        ("Intel", "Core i9-10900F", "LGA1200", 10, "2.80", 65, 319990),
        ("Intel", "Core i9-10900K", "LGA1200", 10, "3.70", 125, 399990),
        ("Intel", "Core i9-11900", "LGA1200", 8, "2.50", 65, 349990),
        ("Intel", "Core i9-11900K", "LGA1200", 8, "3.50", 125, 429990),
        ("Intel", "Core i3-12100", "LGA1700", 4, "3.30", 60, 129990),
        ("Intel", "Core i3-12100F", "LGA1700", 4, "3.30", 58, 109990),
        ("Intel", "Core i3-13100", "LGA1700", 4, "3.40", 60, 139990),
        ("Intel", "Core i3-14100", "LGA1700", 4, "3.50", 60, 149990),
        ("Intel", "Core i5-12400", "LGA1700", 6, "2.50", 65, 179990),
        ("Intel", "Core i5-12400F", "LGA1700", 6, "2.50", 65, 159990),
        ("Intel", "Core i5-12600K", "LGA1700", 10, "3.70", 125, 249990),
        ("Intel", "Core i5-12600KF", "LGA1700", 10, "3.70", 125, 229990),
        ("Intel", "Core i5-13400", "LGA1700", 10, "2.50", 65, 219990),
        ("Intel", "Core i5-13400F", "LGA1700", 10, "2.50", 65, 199990),
        ("Intel", "Core i5-13500", "LGA1700", 14, "2.50", 65, 239990),
        ("Intel", "Core i5-13600K", "LGA1700", 14, "3.50", 125, 299990),
        ("Intel", "Core i5-13600KF", "LGA1700", 14, "3.50", 125, 279990),
        ("Intel", "Core i5-14400", "LGA1700", 10, "2.50", 65, 229990),
        ("Intel", "Core i5-14600K", "LGA1700", 14, "3.50", 125, 319990),
        ("Intel", "Core i7-12700", "LGA1700", 12, "2.10", 65, 299990),
        ("Intel", "Core i7-12700F", "LGA1700", 12, "2.10", 65, 279990),
        ("Intel", "Core i7-12700K", "LGA1700", 12, "3.60", 125, 349990),
        ("Intel", "Core i7-13700", "LGA1700", 16, "2.10", 65, 359990),
        ("Intel", "Core i7-13700K", "LGA1700", 16, "3.40", 125, 399990),
        ("Intel", "Core i7-14700", "LGA1700", 20, "2.10", 65, 389990),
        ("Intel", "Core i7-14700K", "LGA1700", 20, "3.40", 125, 429990),
        ("Intel", "Core i9-12900K", "LGA1700", 16, "3.20", 125, 449990),
        ("Intel", "Core i9-13900K", "LGA1700", 24, "3.00", 125, 549990),
        ("Intel", "Core i9-14900K", "LGA1700", 24, "3.20", 125, 599990),
    ]
    filas = []
    for marca, nombre, socket, nucleos, ghz, watts, base in raw:
        filas.append({
            "marca": marca,
            "nombre": f"{marca} {nombre}",
            "detalle": f"Procesador {marca} {nombre} para socket {socket}.",
            "precio_base": base,
            "campos": {
                "socket": socket,
                "nucleos": nucleos,
                "frecuencia_base": Decimal(ghz),
                "potencia_referencia_watts": watts,
            },
        })
    return _enumerar("procesador", filas)


def _gpus() -> list[dict]:
    nvidia = [
        ("GeForce GTX 1650", 4, "GDDR6", "PCIe 3.0", 75, 300, 170, 149990),
        ("GeForce GTX 1660 Super", 6, "GDDR6", "PCIe 3.0", 125, 450, 230, 189990),
        ("GeForce RTX 2060", 6, "GDDR6", "PCIe 3.0", 160, 500, 240, 219990),
        ("GeForce RTX 3060", 12, "GDDR6", "PCIe 4.0", 170, 550, 242, 289990),
        ("GeForce RTX 3060 Ti", 8, "GDDR6", "PCIe 4.0", 200, 600, 245, 349990),
        ("GeForce RTX 3070", 8, "GDDR6", "PCIe 4.0", 220, 650, 270, 399990),
        ("GeForce RTX 4060", 8, "GDDR6", "PCIe 4.0", 115, 550, 240, 329990),
    ]
    amd = [
        ("Radeon RX 6600", 8, "GDDR6", "PCIe 4.0", 132, 500, 240, 219990),
        ("Radeon RX 6700 XT", 12, "GDDR6", "PCIe 4.0", 230, 650, 280, 349990),
        ("Radeon RX 7600", 8, "GDDR6", "PCIe 4.0", 165, 550, 240, 279990),
        ("Radeon RX 7800 XT", 16, "GDDR6", "PCIe 4.0", 263, 700, 320, 529990),
    ]
    arc = [
        ("Arc A750", 8, "GDDR6", "PCIe 4.0", 225, 600, 270, 229990),
        ("Arc A770", 16, "GDDR6", "PCIe 4.0", 225, 650, 280, 299990),
        ("Arc B580", 12, "GDDR6", "PCIe 4.0", 190, 600, 272, 279990),
    ]
    filas = []
    for partner in ("ASUS", "MSI", "Gigabyte", "Zotac", "PNY", "Palit", "EVGA", "GALAX", "Inno3D", "Gainward"):
        for chip, vram, mem, bus, consumo, fuente, largo, base in nvidia:
            filas.append(_gpu(partner, chip, vram, mem, bus, consumo, fuente, largo, base))
    for partner in ("Sapphire", "PowerColor", "XFX", "ASRock", "ASUS", "MSI"):
        for chip, vram, mem, bus, consumo, fuente, largo, base in amd:
            filas.append(_gpu(partner, chip, vram, mem, bus, consumo, fuente, largo, base))
    for partner in ("Sparkle", "ASRock"):
        for chip, vram, mem, bus, consumo, fuente, largo, base in arc:
            filas.append(_gpu(partner, chip, vram, mem, bus, consumo, fuente, largo, base))
    return _enumerar("tarjeta_grafica", filas)


def _gpu(partner, chip, vram, mem, bus, consumo, fuente, largo, base) -> dict:
    return {
        "marca": partner,
        "nombre": f"{partner} {chip}",
        "detalle": f"Tarjeta gráfica {partner} {chip}, {vram} GB {mem}, {bus}.",
        "precio_base": base,
        "campos": {
            "vram_gb": vram,
            "tipo_memoria": mem,
            "interfaz": bus,
            "consumo_referencia_watts": consumo,
            "potencia_minima_fuente_watts": fuente,
            "largo_mm": largo,
        },
    }


def _rams() -> list[dict]:
    ddr4_lines = [
        ("Corsair", "Vengeance LPX"),
        ("G.Skill", "Ripjaws V"),
        ("Kingston", "Fury Beast"),
        ("HyperX", "Fury"),
        ("Crucial", "Ballistix"),
        ("Patriot", "Viper Steel"),
        ("ADATA", "XPG Spectrix D50"),
        ("TeamGroup", "T-Force Vulcan Z"),
    ]
    ddr4_kits = [
        (2, 8, 3200), (2, 8, 3600), (2, 16, 3200), (2, 16, 3600),
        (1, 16, 3200), (4, 8, 3200),
    ]
    ddr5_lines = [
        ("Corsair", "Vengeance"),
        ("G.Skill", "Trident Z5"),
        ("Kingston", "Fury Beast"),
        ("ADATA", "XPG Lancer"),
        ("TeamGroup", "T-Force Delta"),
        ("Patriot", "Viper Venom"),
        ("Crucial", "Pro"),
    ]
    ddr5_kits = [(2, 16, 5600), (2, 16, 6000), (2, 32, 5600), (2, 32, 6400)]
    sodimm = [
        ("Kingston", "Fury Impact", "DDR4", 1, 16, 3200),
        ("Crucial", "DDR4 SODIMM", "DDR4", 1, 16, 3200),
        ("Corsair", "Vengeance SODIMM", "DDR4", 2, 8, 3200),
        ("Kingston", "Fury Impact", "DDR5", 1, 16, 4800),
        ("Crucial", "DDR5 SODIMM", "DDR5", 1, 16, 5600),
        ("Corsair", "Vengeance SODIMM", "DDR5", 2, 16, 5600),
        ("ADATA", "XPG Lancer SODIMM", "DDR5", 1, 16, 4800),
        ("TeamGroup", "T-Force SODIMM", "DDR5", 2, 16, 5600),
    ]
    filas = []
    for mods, gb, mhz in ddr4_kits:
        for marca, linea in ddr4_lines:
            filas.append(_ram(marca, linea, "DDR4", "DIMM", mods, gb, mhz, 39990 if gb <= 8 else 79990))
    for mods, gb, mhz in ddr5_kits:
        for marca, linea in ddr5_lines:
            filas.append(_ram(marca, linea, "DDR5", "DIMM", mods, gb, mhz, 99990 if gb <= 16 else 179990))
    for marca, linea, ddr, mods, gb, mhz in sodimm:
        filas.append(_ram(marca, linea, ddr, "SO-DIMM", mods, gb, mhz, 49990))
    # 8*6 + 7*4 + 8 = 48+28+8 = 84. Add 16 more DDR5 single-module DIMMs.
    extra_lines = [
        ("Corsair", "Vengeance"),
        ("G.Skill", "Trident Z5"),
        ("Kingston", "Fury Beast"),
        ("Crucial", "Pro"),
    ]
    for mhz in (5600, 6000):
        for gb in (16, 32):
            for marca, linea in extra_lines:
                filas.append(_ram(marca, linea, "DDR5", "DIMM", 1, gb, mhz, 69990 if gb == 16 else 129990))
    return _enumerar("memoria_ram", filas)


def _ram(marca, linea, ddr, formato, mods, gb, mhz, base) -> dict:
    total = mods * gb
    kit = f"{total}GB" if mods == 1 else f"{total}GB ({mods}x{gb})"
    sufijo = " SO-DIMM" if formato == "SO-DIMM" else ""
    return {
        "marca": marca,
        "nombre": f"{marca} {linea} {kit} {ddr}-{mhz}{sufijo}",
        "detalle": f"Memoria {ddr} {formato}. El producto trae {mods} módulo(s) de {gb} GB.",
        "precio_base": base,
        "campos": {
            "capacidad_gb": total,
            "tipo_ddr": ddr,
            "velocidad_mhz": mhz,
            "modulos_por_producto": mods,
            "capacidad_modulo_gb": gb,
            "formato_ram": formato,
        },
    }


def _placas() -> list[dict]:
    planos = [
        ("ASUS", "TUF GAMING {chip}-PLUS", "ATX", 4),
        ("ASUS", "ROG STRIX {chip}-A GAMING", "ATX", 4),
        ("ASUS", "PRIME {chip}-P", "ATX", 4),
        ("ASUS", "PRIME {chip}M-A", "Micro-ATX", 4),
        ("ASUS", "ROG STRIX {chip}-I GAMING", "Mini-ITX", 2),
        ("MSI", "MAG {chip} TOMAHAWK WIFI", "ATX", 4),
        ("MSI", "MPG {chip} CARBON WIFI", "ATX", 4),
        ("MSI", "PRO {chip}-P WIFI", "ATX", 4),
        ("MSI", "PRO {chip}M-B", "Micro-ATX", 2),
        ("MSI", "MPG {chip}I EDGE WIFI", "Mini-ITX", 2),
        ("Gigabyte", "{chip} AORUS ELITE AX", "ATX", 4),
        ("Gigabyte", "{chip} GAMING X AX", "ATX", 4),
        ("Gigabyte", "{chip} AORUS MASTER", "ATX", 4),
        ("Gigabyte", "{chip}M DS3H", "Micro-ATX", 4),
        ("Gigabyte", "{chip}I AORUS ULTRA", "Mini-ITX", 2),
        ("ASRock", "{chip} Steel Legend WiFi", "ATX", 4),
        ("ASRock", "{chip} Phantom Gaming 4", "ATX", 4),
        ("ASRock", "{chip} Pro RS", "ATX", 4),
        ("ASRock", "{chip}M Pro RS", "Micro-ATX", 4),
        ("ASRock", "{chip}I Lightning WiFi", "Mini-ITX", 2),
        ("ASUS", "ProArt {chip}-CREATOR", "ATX", 4),
        ("MSI", "MAG {chip} TOMAHAWK MAX", "ATX", 4),
        ("Gigabyte", "{chip} AORUS PRO AX", "ATX", 4),
        ("ASRock", "{chip} Taichi", "ATX", 4),
        ("ASUS", "TUF GAMING {chip}-PLUS WIFI", "ATX", 4),
    ]
    precios = {"B550": 119990, "B650": 189990, "X670": 289990, "Z790": 249990}
    filas = []
    for chip, (socket, ddr, max_ram) in SOCKET_POR_CHIPSET.items():
        for marca, patron, formato, slots in planos:
            nombre = patron.format(chip=chip)
            tope = 64 if formato == "Mini-ITX" else max_ram
            filas.append({
                "marca": marca,
                "nombre": f"{marca} {nombre}" if not nombre.startswith(marca) else nombre,
                "detalle": f"Placa {formato} con chipset {chip}, socket {socket} y RAM {ddr}.",
                "precio_base": precios[chip] + (0 if formato == "ATX" else -20000),
                "campos": {
                    "socket_cpu": socket,
                    "chipset": chip,
                    "formato": formato,
                    "ranuras_ram": slots,
                    "tipo_ram_soportado": ddr,
                    "formato_ram_soportado": "DIMM",
                    "capacidad_maxima_ram_gb": tope,
                },
            })
    for fila in filas:
        if not fila["nombre"].startswith(fila["marca"]):
            fila["nombre"] = f"{fila['marca']} {fila['nombre']}"
    return _enumerar("placa_madre", filas)


def _ssds() -> list[dict]:
    lineas = [
        ("Samsung", "990 PRO", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000, 4000), 129990),
        ("Samsung", "980", "NVMe PCIe 3.0", "M.2 2280", (250, 500, 1000), 49990),
        ("Samsung", "970 EVO Plus", "NVMe PCIe 3.0", "M.2 2280", (500, 1000, 2000), 69990),
        ("Samsung", "870 EVO", "SATA III", '2.5"', (500, 1000, 2000, 4000), 59990),
        ("Western Digital", "Black SN850X", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000, 4000), 119990),
        ("Western Digital", "Blue SN580", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000), 54990),
        ("Western Digital", "Blue SA510", "SATA III", '2.5"', (500, 1000, 2000), 49990),
        ("Crucial", "P3 Plus", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000, 4000), 49990),
        ("Crucial", "MX500", "SATA III", '2.5"', (500, 1000, 2000, 4000), 54990),
        ("Kingston", "NV2", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000), 39990),
        ("Kingston", "KC3000", "NVMe PCIe 4.0", "M.2 2280", (512, 1024, 2048), 79990),
        ("Kingston", "A400", "SATA III", '2.5"', (240, 480, 960), 24990),
        ("Seagate", "FireCuda 530", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000, 4000), 139990),
        ("ADATA", "Legend 960", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000, 4000), 99990),
        ("SanDisk", "Ultra 3D", "SATA III", '2.5"', (500, 1000, 2000, 4000), 54990),
        ("Corsair", "MP600 PRO", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000, 4000), 124990),
        ("Patriot", "P400 Lite", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000), 44990),
        ("TeamGroup", "MP44", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000), 49990),
        ("PNY", "CS3140", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000, 4000), 109990),
        ("Gigabyte", "AORUS Gen4 7300", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000), 119990),
        ("MSI", "Spatium M480", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000), 114990),
        ("ADATA", "SU650", "SATA III", '2.5"', (256, 512, 1024), 29990),
        ("Kingston", "NV3", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000, 4000), 44990),
        ("Samsung", "860 EVO", "SATA III", '2.5"', (250, 500, 1000, 2000, 4000), 44990),
        ("Samsung", "990 EVO", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000), 109990),
        ("Western Digital", "Black SN770", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000), 79990),
        ("Crucial", "P5 Plus", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000), 89990),
        ("Kingston", "Fury Renegade", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000, 4000), 89990),
        ("Corsair", "MP600 CORE", "NVMe PCIe 4.0", "M.2 2280", (1000, 2000, 4000), 99990),
        ("Seagate", "FireCuda 520", "NVMe PCIe 4.0", "M.2 2280", (500, 1000, 2000), 99990),
        ("SanDisk", "Extreme", "NVMe PCIe 3.0", "M.2 2280", (500, 1000), 69990),
        ("ADATA", "XPG SX8200 Pro", "NVMe PCIe 3.0", "M.2 2280", (512, 1024, 2048), 79990),
    ]
    filas = []
    for marca, linea, interfaz, formato, capacidades, base in lineas:
        for capacidad in capacidades:
            filas.append({
                "marca": marca,
                "nombre": f"{marca} {linea} {capacidad}GB",
                "detalle": f"SSD {interfaz} en formato {formato}.",
                "precio_base": base + max(0, (capacidad // 1000) - 1) * 40000,
                "campos": {
                    "capacidad_gb": capacidad,
                    "interfaz": interfaz,
                    "formato": formato,
                },
            })
    return _enumerar("almacenamiento_ssd", filas)


def _capacidad_texto(capacidad: int) -> str:
    if capacidad >= 1000 and capacidad % 1000 == 0:
        return f"{capacidad // 1000}TB"
    return f"{capacidad}GB"


def _hdds() -> list[dict]:
    # marca, línea, capacidad GB, rpm, caché MB, precio base
    series = [
        ("Seagate", "Barracuda", ((500, 7200), (1000, 7200), (2000, 7200), (4000, 5400), (6000, 5400), (8000, 5400)), 256, 49990),
        ("Seagate", "Barracuda Pro", ((1000, 7200), (2000, 7200), (4000, 7200), (6000, 7200), (8000, 7200), (10000, 7200)), 256, 119990),
        ("Seagate", "IronWolf", ((1000, 7200), (2000, 7200), (3000, 7200), (4000, 7200), (6000, 7200), (8000, 7200), (10000, 7200), (12000, 7200)), 256, 89990),
        ("Seagate", "IronWolf Pro", ((2000, 7200), (4000, 7200), (6000, 7200), (8000, 7200), (10000, 7200), (12000, 7200), (16000, 7200), (18000, 7200)), 256, 149990),
        ("Seagate", "SkyHawk", ((1000, 5400), (2000, 5400), (3000, 5400), (4000, 5400), (6000, 5400), (8000, 5400)), 256, 79990),
        ("Seagate", "SkyHawk AI", ((8000, 7200), (10000, 7200), (12000, 7200), (16000, 7200)), 256, 179990),
        ("Seagate", "Exos 7E8", ((1000, 7200), (2000, 7200), (4000, 7200), (6000, 7200), (8000, 7200)), 256, 99990),
        ("Seagate", "Exos X16", ((10000, 7200), (12000, 7200), (14000, 7200), (16000, 7200)), 256, 249990),
        ("Western Digital", "Blue", ((500, 7200), (1000, 7200), (2000, 7200), (3000, 5400), (4000, 5400), (6000, 5400)), 256, 49990),
        ("Western Digital", "Black", ((500, 7200), (1000, 7200), (2000, 7200), (4000, 7200), (6000, 7200), (8000, 7200), (10000, 7200)), 256, 89990),
        ("Western Digital", "Red Plus", ((1000, 5400), (2000, 5400), (3000, 5400), (4000, 5400), (6000, 5400), (8000, 5400), (10000, 5400), (12000, 5400)), 256, 99990),
        ("Western Digital", "Red Pro", ((2000, 7200), (4000, 7200), (6000, 7200), (8000, 7200), (10000, 7200), (12000, 7200)), 256, 159990),
        ("Western Digital", "Purple", ((1000, 5400), (2000, 5400), (4000, 5400), (6000, 5400), (8000, 5400), (10000, 5400)), 64, 89990),
        ("Western Digital", "Gold", ((1000, 7200), (2000, 7200), (4000, 7200), (6000, 7200), (8000, 7200), (10000, 7200), (12000, 7200)), 256, 149990),
        ("Toshiba", "P300", ((500, 7200), (1000, 7200), (2000, 7200), (3000, 7200), (4000, 7200), (6000, 7200)), 64, 49990),
        ("Toshiba", "X300", ((4000, 7200), (6000, 7200), (8000, 7200), (10000, 7200), (12000, 7200), (14000, 7200), (16000, 7200)), 256, 129990),
    ]
    filas = []
    for marca, linea, capacidades, cache, base in series:
        for capacidad, rpm in capacidades:
            texto = _capacidad_texto(capacidad)
            filas.append({
                "marca": marca,
                "nombre": f"{marca} {linea} {texto}",
                "detalle": f"Disco mecánico {rpm} RPM con {cache} MB de caché.",
                "precio_base": base + (capacidad // 1000) * 5000,
                "campos": {
                    "capacidad_gb": capacidad,
                    "velocidad_rpm": rpm,
                    "cache_mb": cache,
                },
            })
    return _enumerar("almacenamiento_hdd", filas)


def _gabinetes() -> list[dict]:
    modelos = [
        ("Corsair", "4000D Airflow", "ATX", "Acero", True, 360, 89990),
        ("Corsair", "4000D", "ATX", "Acero", True, 360, 79990),
        ("Corsair", "5000D Airflow", "ATX", "Acero", True, 400, 149990),
        ("Corsair", "5000D", "ATX", "Acero", True, 400, 139990),
        ("Corsair", "7000D Airflow", "ATX", "Acero", True, 450, 219990),
        ("Corsair", "275R Airflow", "ATX", "Acero", True, 370, 69990),
        ("Corsair", "220T RGB", "ATX", "Acero", True, 300, 89990),
        ("Corsair", "2000D Airflow", "Mini-ITX", "Acero", True, 365, 129990),
        ("Corsair", "2500D Airflow", "Micro-ATX", "Acero", True, 400, 119990),
        ("NZXT", "H5 Flow", "ATX", "Acero", True, 365, 99990),
        ("NZXT", "H5 Elite", "ATX", "Vidrio Templado", True, 365, 149990),
        ("NZXT", "H6 Flow", "ATX", "Acero", True, 365, 129990),
        ("NZXT", "H7 Flow", "ATX", "Acero", True, 400, 139990),
        ("NZXT", "H7 Elite", "ATX", "Vidrio Templado", True, 400, 179990),
        ("NZXT", "H9 Flow", "ATX", "Acero", True, 435, 169990),
        ("NZXT", "H9 Elite", "ATX", "Vidrio Templado", True, 435, 229990),
        ("NZXT", "H510", "ATX", "Acero", True, 381, 89990),
        ("NZXT", "H510 Flow", "ATX", "Acero", True, 381, 99990),
        ("NZXT", "H210", "Mini-ITX", "Acero", True, 325, 89990),
        ("Lian Li", "Lancool 215", "ATX", "Acero", True, 370, 89990),
        ("Lian Li", "Lancool 216", "ATX", "Acero", True, 392, 109990),
        ("Lian Li", "Lancool II Mesh", "ATX", "Acero", True, 384, 119990),
        ("Lian Li", "O11 Dynamic", "ATX", "Vidrio Templado", False, 420, 149990),
        ("Lian Li", "O11 Dynamic EVO", "ATX", "Vidrio Templado", False, 442, 179990),
        ("Lian Li", "O11 Air Mini", "Micro-ATX", "Acero", True, 362, 119990),
        ("Lian Li", "A4-H2O", "Mini-ITX", "Aluminio", False, 322, 149990),
        ("Fractal Design", "Meshify 2", "ATX", "Acero", True, 440, 149990),
        ("Fractal Design", "Meshify 2 Compact", "ATX", "Acero", True, 360, 129990),
        ("Fractal Design", "Meshify C", "ATX", "Acero", True, 315, 99990),
        ("Fractal Design", "Pop Air", "ATX", "Acero", True, 380, 89990),
        ("Fractal Design", "Pop Mini Air", "Micro-ATX", "Acero", True, 365, 79990),
        ("Fractal Design", "North", "ATX", "Acero", True, 355, 149990),
        ("Fractal Design", "Torrent", "ATX", "Acero", True, 423, 199990),
        ("Fractal Design", "Define 7", "ATX", "Acero", False, 440, 169990),
        ("Fractal Design", "Ridge", "Mini-ITX", "Aluminio", True, 335, 129990),
        ("Phanteks", "Eclipse G360A", "ATX", "Acero", True, 400, 89990),
        ("Phanteks", "Eclipse G500A", "ATX", "Acero", True, 435, 129990),
        ("Phanteks", "Eclipse P400A", "ATX", "Acero", True, 420, 99990),
        ("Phanteks", "Eclipse P500A", "ATX", "Acero", True, 435, 139990),
        ("Phanteks", "Evolv Shift XT", "Mini-ITX", "Acero", True, 335, 149990),
        ("Cooler Master", "TD500 Mesh", "ATX", "Acero", True, 410, 109990),
        ("Cooler Master", "NR200P", "Mini-ITX", "Acero", True, 330, 99990),
        ("Cooler Master", "NR600", "ATX", "Acero", False, 410, 69990),
        ("Cooler Master", "MB311L", "Micro-ATX", "Acero", True, 340, 49990),
        ("Cooler Master", "MasterBox Q300L", "Micro-ATX", "Acero", False, 360, 49990),
        ("Cooler Master", "HAF 500", "ATX", "Acero", True, 410, 129990),
        ("be quiet!", "Pure Base 500", "ATX", "Acero", True, 369, 99990),
        ("be quiet!", "Pure Base 500DX", "ATX", "Vidrio Templado", True, 369, 119990),
        ("be quiet!", "Shadow Base 800", "ATX", "Acero", True, 430, 149990),
        ("be quiet!", "Pure Base 600", "ATX", "Acero", True, 425, 109990),
        ("Thermaltake", "Versa H18", "Micro-ATX", "Acero", False, 350, 49990),
        ("Thermaltake", "S100 TG", "Micro-ATX", "Vidrio Templado", True, 330, 59990),
        ("Thermaltake", "View 170 TG", "Micro-ATX", "Vidrio Templado", True, 340, 69990),
        ("Thermaltake", "Core P3", "ATX", "Acero", False, 450, 149990),
        ("Thermaltake", "Versa H26", "ATX", "Acero", True, 380, 69990),
        ("Silverstone", "FARA R1", "ATX", "Acero", True, 365, 69990),
        ("Silverstone", "FARA R1 Pro", "ATX", "Acero", True, 365, 79990),
        ("Silverstone", "PS15", "Micro-ATX", "Acero", True, 350, 49990),
        ("Silverstone", "RL08", "Mini-ITX", "Aluminio", True, 330, 129990),
        ("Silverstone", "SETA H1", "ATX", "Acero", True, 392, 119990),
        ("Montech", "AIR 100", "Micro-ATX", "Acero", True, 330, 59990),
        ("Montech", "AIR 100 ARGB", "Micro-ATX", "Acero", True, 330, 69990),
        ("Montech", "AIR 903 Max", "ATX", "Acero", True, 400, 89990),
        ("Montech", "AIR 903 Base", "ATX", "Acero", True, 400, 79990),
        ("Montech", "SKY TWO", "ATX", "Vidrio Templado", True, 400, 109990),
        ("Antec", "NX410", "ATX", "Acero", True, 360, 59990),
        ("Antec", "NX416L", "ATX", "Acero", True, 360, 69990),
        ("Antec", "DF700 Flux", "ATX", "Acero", True, 405, 99990),
        ("Antec", "P10C", "ATX", "Acero", False, 415, 109990),
        ("Antec", "NX200M", "Micro-ATX", "Acero", True, 330, 49990),
        ("Lian Li", "Lancool 205 Mesh", "ATX", "Acero", True, 350, 79990),
        ("Phanteks", "Eclipse G300A", "Micro-ATX", "Acero", True, 355, 69990),
        ("Fractal Design", "Focus 2", "ATX", "Acero", True, 405, 79990),
        ("NZXT", "H1", "Mini-ITX", "Acero", True, 305, 199990),
        ("Corsair", "3000D Airflow", "ATX", "Acero", True, 360, 79990),
        ("Corsair", "3500X", "ATX", "Vidrio Templado", True, 410, 119990),
        ("MSI", "MAG Forge 112R", "ATX", "Acero", True, 340, 69990),
        ("MSI", "MAG Forge 321R", "ATX", "Acero", True, 390, 89990),
        ("MSI", "MPG Gungnir 110R", "ATX", "Acero", True, 340, 99990),
        ("MSI", "MAG Forge M100R", "Micro-ATX", "Acero", True, 300, 59990),
        ("ASUS", "TUF Gaming GT502", "ATX", "Acero", True, 400, 169990),
        ("ASUS", "A21", "Micro-ATX", "Acero", True, 380, 69990),
        ("ASUS", "PA602", "ATX", "Acero", True, 450, 199990),
        ("Cooler Master", "MasterBox 520", "ATX", "Acero", True, 410, 99990),
        ("be quiet!", "Pure Base 500 FX", "ATX", "Vidrio Templado", True, 369, 149990),
        ("Thermaltake", "View 200 TG", "ATX", "Vidrio Templado", True, 390, 89990),
        ("Silverstone", "FARA B1", "ATX", "Acero", True, 370, 69990),
        ("Montech", "XR", "ATX", "Vidrio Templado", True, 390, 99990),
        ("Antec", "C8", "ATX", "Vidrio Templado", True, 395, 129990),
        ("Lian Li", "Lancool 207", "ATX", "Acero", True, 375, 99990),
        ("Fractal Design", "Pop XL Air", "ATX", "Acero", True, 430, 119990),
        ("Phanteks", "XT View", "ATX", "Vidrio Templado", True, 415, 119990),
        ("NZXT", "H3 Flow", "Micro-ATX", "Acero", True, 364, 79990),
        ("Corsair", "Frame 4000D", "ATX", "Acero", True, 397, 109990),
        ("Gigabyte", "C301 Glass", "ATX", "Vidrio Templado", True, 400, 99990),
        ("Deepcool", "CC560", "ATX", "Acero", True, 370, 59990),
        ("Deepcool", "CH510", "ATX", "Acero", True, 380, 69990),
        ("Deepcool", "CK560", "ATX", "Acero", True, 380, 79990),
        ("Deepcool", "CH360", "Micro-ATX", "Acero", True, 320, 59990),
        ("Deepcool", "CH160", "Mini-ITX", "Acero", True, 305, 69990),
    ]
    filas = []
    for marca, nombre, formato, material, fans, gpu_mm, base in modelos:
        filas.append({
            "marca": marca,
            "nombre": f"{marca} {nombre}",
            "detalle": f"Gabinete {formato}. Admite GPU de hasta {gpu_mm} mm.",
            "precio_base": base,
            "campos": {
                "formato_soporte": formato,
                "ventiladores_incluidos": fans,
                "material": material,
                "largo_max_gpu_mm": gpu_mm,
            },
        })
    return _enumerar("gabinete", filas)


def _psus() -> list[dict]:
    series = [
        ("Corsair", "RM{w}x", (650, 750, 850, 1000), "80+ Gold", True, 99990),
        ("Corsair", "CX{w}", (550, 650, 750), "80+ Bronze", False, 59990),
        ("Seasonic", "Focus GX-{w}", (650, 750, 850, 1000), "80+ Gold", True, 109990),
        ("Seasonic", "Prime TX-{w}", (850, 1000), "80+ Titanium", True, 249990),
        ("be quiet!", "Pure Power 12 M {w}W", (650, 750, 850), "80+ Gold", True, 109990),
        ("be quiet!", "System Power 10 {w}W", (550, 650, 750), "80+ Bronze", False, 59990),
        ("EVGA", "SuperNOVA {w} G6", (650, 750, 850, 1000), "80+ Gold", True, 119990),
        ("Cooler Master", "MWE Bronze {w}", (550, 650, 750), "80+ Bronze", False, 54990),
        ("Cooler Master", "V{w} Gold", (750, 850), "80+ Gold", True, 129990),
        ("Thermaltake", "Toughpower GF1 {w}W", (650, 750, 850), "80+ Gold", True, 99990),
        ("FSP", "Hydro G {w}", (650, 750, 850), "80+ Gold", True, 99990),
        ("ASUS", "ROG Strix {w}G", (750, 850, 1000), "80+ Gold", True, 149990),
        ("MSI", "MPG A{w}G", (750, 850, 1000), "80+ Gold", True, 129990),
        ("NZXT", "C{w}", (750, 850), "80+ Gold", True, 119990),
        ("Silverstone", "DA{w} Gold", (650, 750, 850), "80+ Gold", True, 109990),
        ("Antec", "NE{w} Gold", (550, 650, 750, 850, 1000), "80+ Gold", True, 89990),
        ("Thermaltake", "Smart {w}W", (500, 600, 700), "80+ White", False, 39990),
        ("Corsair", "HX{w}", (750, 850, 1000), "80+ Platinum", True, 169990),
        ("Seasonic", "Focus PX-{w}", (750, 850), "80+ Platinum", True, 159990),
        ("FSP", "Hydro PTM {w}", (650, 750, 850), "80+ Platinum", True, 139990),
        ("be quiet!", "Dark Power 13 {w}W", (750, 850, 1000), "80+ Titanium", True, 229990),
        ("EVGA", "SuperNOVA {w} P6", (750, 850), "80+ Platinum", True, 159990),
        ("Corsair", "RMe{w}", (650, 750, 850, 1000), "80+ Gold", True, 89990),
        ("Corsair", "SF{w}", (750, 850), "80+ Platinum", True, 149990),
        ("Seasonic", "Core GM-{w}", (500, 650, 750), "80+ Gold", False, 69990),
        ("be quiet!", "Straight Power 12 {w}W", (650, 750, 850, 1000), "80+ Platinum", True, 159990),
        ("EVGA", "BQ {w}", (500, 600, 700, 750), "80+ Bronze", False, 49990),
        ("Cooler Master", "MWE Gold {w}", (550, 650, 750, 850), "80+ Gold", True, 79990),
        ("Thermaltake", "Toughpower GF3 {w}W", (750, 850, 1000, 1200), "80+ Gold", True, 129990),
        ("MSI", "MAG A{w}BN", (550, 650, 750), "80+ Bronze", False, 49990),
        ("ASUS", "TUF Gaming {w}B", (550, 650, 750), "80+ Bronze", False, 69990),
        ("NZXT", "C{w} Gold", (550, 650, 1000), "80+ Gold", True, 99990),
    ]
    filas = []
    for marca, patron, watts, cert, modular, base in series:
        for watt in watts:
            filas.append({
                "marca": marca,
                "nombre": f"{marca} {patron.format(w=watt)}",
                "detalle": f"Fuente {watt} W, certificación {cert}.",
                "precio_base": base + (watt - 550) * 40,
                "campos": {
                    "potencia_watts": watt,
                    "certificacion": cert,
                    "modular": modular,
                },
            })
    vistos = set()
    unicos = []
    for fila in filas:
        if fila["nombre"] in vistos:
            continue
        vistos.add(fila["nombre"])
        unicos.append(fila)
    if len(unicos) < 100:
        raise ValueError(f"PSU únicos insuficientes: {len(unicos)}")
    return _enumerar("fuente_de_poder", unicos[:100])


def _coolers() -> list[dict]:
    aire = [
        ("Noctua", "NH-D15", "AM4, AM5, LGA1700, LGA1200", 89990),
        ("Noctua", "NH-D15S", "AM4, AM5, LGA1700, LGA1200", 79990),
        ("Noctua", "NH-U12A", "AM4, AM5, LGA1700, LGA1200", 99990),
        ("Noctua", "NH-U12S", "AM4, AM5, LGA1700, LGA1200", 69990),
        ("Noctua", "NH-U9S", "AM4, AM5, LGA1700, LGA1200", 59990),
        ("Noctua", "NH-L9a-AM4", "AM4, AM5", 49990),
        ("Noctua", "NH-L9i-1700", "LGA1700, LGA1200", 49990),
        ("Noctua", "NH-L12S", "AM4, AM5, LGA1700, LGA1200", 69990),
        ("Noctua", "NH-D12L", "AM4, AM5, LGA1700, LGA1200", 79990),
        ("Arctic", "Freezer 36", "AM4, AM5, LGA1700, LGA1200", 39990),
        ("Arctic", "Freezer 34 eSports", "AM4, AM5, LGA1700, LGA1200", 34990),
        ("Arctic", "Freezer 34 eSports Duo", "AM4, AM5, LGA1700, LGA1200", 44990),
        ("be quiet!", "Dark Rock 4", "AM4, AM5, LGA1700, LGA1200", 69990),
        ("be quiet!", "Dark Rock Pro 4", "AM4, AM5, LGA1700, LGA1200", 89990),
        ("be quiet!", "Pure Rock 2", "AM4, AM5, LGA1700, LGA1200", 39990),
        ("be quiet!", "Dark Rock Elite", "AM4, AM5, LGA1700, LGA1200", 99990),
        ("Cooler Master", "Hyper 212 Black", "AM4, AM5, LGA1700, LGA1200", 39990),
        ("Cooler Master", "Hyper 212 Halo", "AM4, AM5, LGA1700, LGA1200", 49990),
        ("Cooler Master", "MA624 Stealth", "AM4, AM5, LGA1700, LGA1200", 79990),
        ("Deepcool", "AK400", "AM4, AM5, LGA1700, LGA1200", 29990),
        ("Deepcool", "AK620", "AM4, AM5, LGA1700, LGA1200", 59990),
        ("Deepcool", "AG400", "AM4, AM5, LGA1700, LGA1200", 24990),
        ("Deepcool", "AG620", "AM4, AM5, LGA1700, LGA1200", 49990),
        ("ID-COOLING", "SE-224-XTS", "AM4, AM5, LGA1700, LGA1200", 24990),
        ("ID-COOLING", "SE-226-XT", "AM4, AM5, LGA1700, LGA1200", 34990),
        ("ID-COOLING", "IS-55", "AM4, AM5, LGA1700", 39990),
        ("Scythe", "Fuma 2", "AM4, AM5, LGA1700, LGA1200", 59990),
        ("Scythe", "Fuma 3", "AM4, AM5, LGA1700, LGA1200", 59990),
        ("Scythe", "Mugen 5", "AM4, AM5, LGA1700, LGA1200", 49990),
        ("Thermaltake", "UX200 SE", "AM4, AM5, LGA1700, LGA1200", 29990),
        ("Thermaltake", "TOUGHAIR 510", "AM4, AM5, LGA1700, LGA1200", 59990),
        ("Arctic", "Freezer 7 X", "LGA1700, LGA1200", 19990),
        ("Cooler Master", "Hyper 212 EVO V2", "AM4, AM5, LGA1700, LGA1200", 34990),
        ("Noctua", "NH-U14S", "AM4, AM5, LGA1700, LGA1200", 79990),
        ("be quiet!", "Pure Rock Slim 2", "AM4, AM5, LGA1700, LGA1200", 29990),
        ("Deepcool", "AK500", "AM4, AM5, LGA1700, LGA1200", 44990),
        ("ID-COOLING", "SE-214-XT", "AM4, AM5, LGA1700, LGA1200", 22990),
        ("Scythe", "Big Shuriken 3", "AM4, AM5, LGA1700, LGA1200", 49990),
        ("Arctic", "Alpine 23", "AM4, AM5", 14990),
        ("Arctic", "Alpine 17", "LGA1700", 14990),
    ]
    liquidas = [
        ("Corsair", "iCUE H100i RGB Elite", 240, 129990),
        ("Corsair", "iCUE H115i RGB Elite", 280, 149990),
        ("Corsair", "iCUE H150i RGB Elite", 360, 169990),
        ("Corsair", "iCUE LINK H100i", 240, 159990),
        ("Corsair", "iCUE LINK H150i", 360, 199990),
        ("NZXT", "Kraken 240", 240, 129990),
        ("NZXT", "Kraken 280", 280, 149990),
        ("NZXT", "Kraken 360", 360, 179990),
        ("NZXT", "Kraken Elite 240", 240, 169990),
        ("NZXT", "Kraken Elite 360", 360, 219990),
        ("Arctic", "Liquid Freezer II 240", 240, 89990),
        ("Arctic", "Liquid Freezer II 280", 280, 99990),
        ("Arctic", "Liquid Freezer II 360", 360, 109990),
        ("Arctic", "Liquid Freezer III 240", 240, 99990),
        ("Arctic", "Liquid Freezer III 360", 360, 119990),
        ("Arctic", "Liquid Freezer III 280", 280, 109990),
        ("Deepcool", "LS520", 240, 89990),
        ("Deepcool", "LS720", 360, 119990),
        ("Deepcool", "LT720", 360, 129990),
        ("be quiet!", "Pure Loop 2 240", 240, 109990),
        ("be quiet!", "Pure Loop 2 360", 360, 139990),
        ("be quiet!", "Silent Loop 2 240", 240, 129990),
        ("be quiet!", "Silent Loop 2 360", 360, 159990),
        ("Cooler Master", "MasterLiquid 240L Core", 240, 79990),
        ("Cooler Master", "MasterLiquid 360L Core", 360, 99990),
        ("Thermaltake", "TH240 V2", 240, 89990),
        ("Thermaltake", "TH360 V2", 360, 119990),
        ("ID-COOLING", "ZoomFlow 240 XT", 240, 69990),
        ("ID-COOLING", "Dashflow 360", 360, 89990),
        ("ASUS", "ROG Ryujin III 240", 240, 249990),
        ("ASUS", "ROG Ryujin III 360", 360, 299990),
        ("MSI", "MAG CoreLiquid 240R", 240, 99990),
        ("MSI", "MAG CoreLiquid 360R", 360, 129990),
        ("Fractal Design", "Lumen S24", 240, 99990),
        ("Fractal Design", "Lumen S36", 360, 119990),
        ("Lian Li", "Galahad II Trinity 240", 240, 129990),
        ("Lian Li", "Galahad II Trinity 360", 360, 159990),
        ("Phanteks", "Glacier One 240", 240, 109990),
        ("Phanteks", "Glacier One 360", 360, 139990),
        ("Silverstone", "IceGem 240", 240, 89990),
        ("Silverstone", "IceGem 360", 360, 119990),
        ("Antec", "Symphony 240", 240, 79990),
        ("Antec", "Symphony 360", 360, 99990),
        ("Montech", "HyperFlow 240", 240, 79990),
        ("Montech", "HyperFlow 360", 360, 99990),
        ("Deepcool", "LS320", 240, 79990),
        ("Cooler Master", "MasterLiquid 240 Atmos", 240, 119990),
        ("Corsair", "Nautilus 240", 240, 99990),
        ("Corsair", "Nautilus 360", 360, 129990),
        ("NZXT", "Kraken 240 RGB", 240, 149990),
        ("Arctic", "Liquid Freezer III 420", 420, 139990),
        ("be quiet!", "Pure Loop 2 280", 280, 119990),
        ("Thermaltake", "TH280 V2", 280, 109990),
        ("ID-COOLING", "ZoomFlow 360 XT", 360, 89990),
        ("MSI", "MPG CoreLiquid K360", 360, 169990),
        ("ASUS", "ROG Strix LC II 240", 240, 149990),
        ("ASUS", "ROG Strix LC II 360", 360, 179990),
        ("Lian Li", "GA II Lite 240", 240, 89990),
        ("Lian Li", "GA II Lite 360", 360, 109990),
        ("Scythe", "Mugen 6 Dual", "AM4, AM5, LGA1700, LGA1200", 69990),
    ]
    filas = []
    for marca, nombre, sockets, base in aire:
        filas.append({
            "marca": marca,
            "nombre": f"{marca} {nombre}",
            "detalle": f"Cooler por aire compatible con {sockets}.",
            "precio_base": base,
            "campos": {
                "tipo": "Aire",
                "socket_compatibles": sockets,
                "tamanho_radiador_mm": None,
            },
        })
    for item in liquidas:
        if len(item) == 4 and isinstance(item[2], str):
            marca, nombre, sockets, base = item
            filas.append({
                "marca": marca,
                "nombre": f"{marca} {nombre}",
                "detalle": f"Cooler por aire compatible con {sockets}.",
                "precio_base": base,
                "campos": {
                    "tipo": "Aire",
                    "socket_compatibles": sockets,
                    "tamanho_radiador_mm": None,
                },
            })
            continue
        marca, nombre, radiador, base = item
        filas.append({
            "marca": marca,
            "nombre": f"{marca} {nombre}",
            "detalle": f"Refrigeración líquida con radiador de {radiador} mm. Compatible con AM4, AM5, LGA1700 y LGA1200.",
            "precio_base": base,
            "campos": {
                "tipo": "Líquida",
                "socket_compatibles": "AM4, AM5, LGA1700, LGA1200",
                "tamanho_radiador_mm": radiador,
            },
        })
    if len(filas) != 100:
        raise ValueError(f"coolers {len(filas)}")
    return _enumerar("refrigeracion", filas)


def _fans() -> list[dict]:
    modelos = [
        ("Noctua", "NF-A12x25 PWM", 120, 2000, False, 29990),
        ("Noctua", "NF-A14 PWM", 140, 1500, False, 29990),
        ("Noctua", "NF-P12 redux-1700", 120, 1700, False, 14990),
        ("Noctua", "NF-F12 PWM", 120, 1500, False, 24990),
        ("Noctua", "NF-S12A PWM", 120, 1200, False, 24990),
        ("Noctua", "NF-A12x15 PWM", 120, 1850, False, 24990),
        ("Arctic", "P12 PWM", 120, 1800, False, 9990),
        ("Arctic", "P14 PWM", 140, 1700, False, 10990),
        ("Arctic", "P12 PWM PST", 120, 1800, False, 11990),
        ("Arctic", "P14 PWM PST", 140, 1700, False, 12990),
        ("Arctic", "P12 Max", 120, 3300, False, 14990),
        ("Arctic", "BioniX P120", 120, 2100, False, 12990),
        ("Corsair", "AF120 Elite", 120, 1850, False, 19990),
        ("Corsair", "AF140 Elite", 140, 1600, False, 22990),
        ("Corsair", "iCUE AF120 RGB Elite", 120, 1850, True, 24990),
        ("Corsair", "iCUE AF140 RGB Elite", 140, 1600, True, 27990),
        ("Corsair", "ML120 RGB", 120, 2400, True, 29990),
        ("Corsair", "SP120 RGB Elite", 120, 1500, True, 19990),
        ("be quiet!", "Silent Wings 4 120", 120, 2500, False, 24990),
        ("be quiet!", "Silent Wings 4 140", 140, 1900, False, 27990),
        ("be quiet!", "Pure Wings 2 120", 120, 1500, False, 12990),
        ("be quiet!", "Pure Wings 2 140", 140, 1000, False, 14990),
        ("be quiet!", "Light Wings 120", 120, 1700, True, 24990),
        ("be quiet!", "Light Wings 140", 140, 1500, True, 27990),
        ("Cooler Master", "SickleFlow 120", 120, 1800, False, 12990),
        ("Cooler Master", "SickleFlow 120 ARGB", 120, 1800, True, 16990),
        ("Cooler Master", "Mobius 120", 120, 2050, False, 19990),
        ("Cooler Master", "Mobius 120 ARGB", 120, 2050, True, 24990),
        ("Cooler Master", "Mobius 140", 140, 1900, False, 22990),
        ("NZXT", "F120 RGB", 120, 1800, True, 19990),
        ("NZXT", "F140 RGB", 140, 1500, True, 22990),
        ("NZXT", "F120Q", 120, 1700, False, 14990),
        ("Thermaltake", "Toughfan 12", 120, 2000, False, 19990),
        ("Thermaltake", "Toughfan 14", 140, 2000, False, 22990),
        ("Thermaltake", "Pure 12 ARGB", 120, 1500, True, 14990),
        ("Thermaltake", "SWAFAN EX12", 120, 2000, True, 24990),
        ("Deepcool", "RF120 FS", 120, 1500, True, 12990),
        ("Deepcool", "FK120", 120, 1850, False, 12990),
        ("Deepcool", "FC120", 120, 1800, True, 16990),
        ("ID-COOLING", "ZF-12025", 120, 1500, True, 12990),
        ("ID-COOLING", "NO-12015", 120, 1800, False, 14990),
        ("Phanteks", "T30-120", 120, 3000, False, 34990),
        ("Phanteks", "SK120 PWM", 120, 1500, False, 14990),
        ("Arctic", "P12 ARGB", 120, 2000, True, 14990),
        ("Arctic", "P14 ARGB", 140, 1900, True, 16990),
        ("Noctua", "NF-A14 chromax", 140, 1500, False, 32990),
        ("Corsair", "RS120", 120, 2100, False, 14990),
        ("Corsair", "RS140", 140, 1700, False, 16990),
        ("Lian Li", "UNI FAN SL120", 120, 1900, True, 24990),
        ("Lian Li", "UNI FAN SL140", 140, 1600, True, 27990),
        ("Lian Li", "UNI FAN P28", 120, 2600, False, 29990),
        ("Fractal Design", "Aspect 12", 120, 2000, False, 14990),
        ("Fractal Design", "Aspect 14", 140, 1700, False, 16990),
        ("Fractal Design", "Dynamic X2 GP-12", 120, 1200, False, 12990),
        ("Silverstone", "Air Blazer 120", 120, 1800, False, 12990),
        ("Antec", "Fusion 120 ARGB", 120, 1500, True, 14990),
        ("Montech", "AX120 PWM", 120, 1600, False, 9990),
        ("be quiet!", "Silent Wings Pro 4 120", 120, 3000, False, 32990),
        ("Noctua", "NF-A12x25 G2", 120, 1800, False, 34990),
        ("Arctic", "F12 PWM", 120, 1350, False, 8990),
        ("Cooler Master", "SickleFlow 140", 140, 1400, False, 14990),
        ("NZXT", "F120 RGB Core", 120, 1800, True, 22990),
        ("Deepcool", "FL120", 120, 1800, True, 14990),
        ("Thermaltake", "CT120 ARGB", 120, 2000, True, 16990),
        ("ID-COOLING", "DF-12025", 120, 1800, True, 14990),
        ("Phanteks", "M25-120", 120, 2000, False, 12990),
        ("Corsair", "iCUE LINK QX120", 120, 2400, True, 39990),
        ("Corsair", "iCUE LINK QX140", 140, 2000, True, 44990),
        ("be quiet!", "Pure Wings 3 120", 120, 1600, False, 14990),
        ("be quiet!", "Pure Wings 3 140", 140, 1200, False, 16990),
        ("Noctua", "NF-A9 PWM", 92, 2000, False, 19990),
        ("Arctic", "P8 PWM", 80, 3000, False, 8990),
        ("Scythe", "Kaze Flex 120", 120, 1800, False, 14990),
        ("Scythe", "Wonder Tornado 120", 120, 2500, False, 19990),
        ("Lian Li", "UNI FAN SL-INF 120", 120, 2100, True, 29990),
        ("MSI", "MEG SILENT GALE P12", 120, 2000, False, 24990),
        ("ASUS", "TUF Gaming TF120", 120, 1900, True, 19990),
        ("Gigabyte", "AORUS GP-ARGB 120", 120, 1700, True, 19990),
        ("Fractal Design", "Momentum 12", 120, 1800, False, 16990),
        ("Fractal Design", "Momentum 14", 140, 1600, False, 18990),
        ("Silverstone", "Air Penetrator 120i", 120, 1800, False, 14990),
        ("Thermaltake", "SWAFAN EX14", 140, 2000, True, 27990),
        ("Deepcool", "FC120 A-RGB", 120, 1800, True, 17990),
        ("Cooler Master", "MasterFan MF120 Halo", 120, 2000, True, 19990),
        ("Corsair", "AF120 Slim", 120, 2000, False, 19990),
        ("Noctua", "NF-A14x25 G2", 140, 1500, False, 39990),
        ("Arctic", "P12 Pro", 120, 3000, False, 12990),
        ("be quiet!", "Light Wings 120 High Speed", 120, 2500, True, 27990),
        ("Phanteks", "D30-120", 120, 2000, True, 24990),
        ("NZXT", "F140Q", 140, 1500, False, 16990),
        ("Montech", "AX140 PWM", 140, 1600, False, 12990),
        ("Antec", "Fusion 140 ARGB", 140, 1400, True, 16990),
        ("ID-COOLING", "AS-120", 120, 1800, True, 12990),
        ("Scythe", "Kaze Flex 140", 140, 1200, False, 16990),
        ("Lian Li", "UNI FAN TL 120", 120, 2600, True, 32990),
        ("MSI", "MAX F12A", 120, 2000, False, 14990),
        ("ASUS", "ROG Strix XF120", 120, 1800, False, 29990),
        ("Gigabyte", "AORUS 140 ARGB", 140, 1500, True, 22990),
        ("Deepcool", "FK120 Triple", 120, 1850, False, 24990),
        ("Arctic", "P14 Pro", 140, 2500, False, 14990),
    ]
    filas = []
    for marca, nombre, mm, rpm, rgb, base in modelos:
        filas.append({
            "marca": marca,
            "nombre": f"{marca} {nombre}",
            "detalle": f"Ventilador de {mm} mm{' con RGB' if rgb else ''}.",
            "precio_base": base,
            "campos": {
                "tamanho_mm": mm,
                "velocidad_rpm": rpm,
                "rgb": rgb,
            },
        })
    if len(filas) != 100:
        raise ValueError(f"fans {len(filas)}")
    return _enumerar("ventilador", filas)


def build_catalog() -> list[dict]:
    grupos = [
        _cpus(),
        _gpus(),
        _rams(),
        _placas(),
        _ssds(),
        _hdds(),
        _gabinetes(),
        _psus(),
        _coolers(),
        _fans(),
    ]
    filas = [fila for grupo in grupos for fila in grupo]
    validar_catalogo(filas)
    return filas


def validar_catalogo(filas: list[dict]) -> None:
    if len(filas) != 1000:
        raise ValueError(f"Se esperaban 1000 productos, hay {len(filas)}")
    vistos = set()
    nombres = set()
    for fila in filas:
        modelo = fila["modelo"]
        pk = fila["pk"]
        if (modelo, pk) in vistos:
            raise ValueError(f"Identidad duplicada {modelo}:{pk}")
        vistos.add((modelo, pk))
        if (modelo, fila["nombre"]) in nombres:
            raise ValueError(f"Nombre duplicado en {modelo}: {fila['nombre']}")
        nombres.add((modelo, fila["nombre"]))
        if "test" in fila["nombre"].lower() or "serie test" in fila["nombre"].lower():
            raise ValueError(f"Nombre de prueba: {fila['nombre']}")
        if "no son un precio de mercado verificado" not in fila["descripcion"]:
            raise ValueError(f"Falta la nota sintética en {fila['nombre']}")
        _validar_coherencia(fila)
    for modelo in CATEGORIAS:
        if sum(1 for fila in filas if fila["modelo"] == modelo) != 100:
            raise ValueError(f"{modelo} no tiene 100 filas")


SOCKETS = {"AM4", "AM5", "LGA1200", "LGA1700", "Otro"}
CHIPSETS = {"B550", "B650", "Z790", "X670", "Otro"}
FORMATOS_PLACA = {"ATX", "Micro-ATX", "Mini-ITX"}
DDR = {"DDR5", "DDR4", "DDR3"}
FORMATOS_RAM = {"DIMM", "SO-DIMM"}
MEMORIA_GPU = {"GDDR6X", "GDDR6", "GDDR5", "Otro"}
BUS_GPU = {"PCIe 4.0", "PCIe 5.0", "PCIe 3.0", "Otro"}
INTERFAZ_SSD = {"NVMe PCIe 4.0", "NVMe PCIe 3.0", "SATA III"}
FORMATO_SSD = {"M.2 2280", '2.5"'}
MATERIALES = {"Acero", "Aluminio", "Plástico", "Vidrio Templado"}
CERTIFICACIONES = {
    "80+ White", "80+ Bronze", "80+ Silver", "80+ Gold", "80+ Platinum", "80+ Titanium",
}
TIPOS_COOLER = {"Aire", "Líquida"}


def _validar_coherencia(fila: dict) -> None:
    modelo = fila["modelo"]
    marca = fila["marca"]
    campos = fila["campos"]
    if fila["precio"] <= 0 or not (1 <= fila["stock"] <= 30):
        raise ValueError(f"Precio o stock inválido en {fila['nombre']}")
    if modelo == "procesador":
        socket = campos["socket"]
        if socket not in SOCKETS or marca not in CPU_AMD | CPU_INTEL:
            raise ValueError(fila["nombre"])
        if marca == "AMD" and socket not in SOCKET_AMD:
            raise ValueError(fila["nombre"])
        if marca == "Intel" and socket not in SOCKET_INTEL:
            raise ValueError(fila["nombre"])
        if campos["nucleos"] < 1 or campos["potencia_referencia_watts"] < 1:
            raise ValueError(fila["nombre"])
    elif modelo == "placa_madre":
        if campos["chipset"] not in CHIPSETS or campos["formato"] not in FORMATOS_PLACA:
            raise ValueError(fila["nombre"])
        esperado = SOCKET_POR_CHIPSET[campos["chipset"]]
        if campos["socket_cpu"] != esperado[0] or campos["tipo_ram_soportado"] != esperado[1]:
            raise ValueError(fila["nombre"])
        if campos["formato_ram_soportado"] != "DIMM" or campos["ranuras_ram"] < 1:
            raise ValueError(fila["nombre"])
        if not fila["nombre"].startswith(marca + " "):
            raise ValueError(fila["nombre"])
    elif modelo == "memoria_ram":
        if campos["tipo_ddr"] not in DDR or campos["formato_ram"] not in FORMATOS_RAM:
            raise ValueError(fila["nombre"])
        if campos["capacidad_gb"] != campos["modulos_por_producto"] * campos["capacidad_modulo_gb"]:
            raise ValueError(fila["nombre"])
        if not fila["nombre"].startswith(marca + " "):
            raise ValueError(fila["nombre"])
    elif modelo == "tarjeta_grafica":
        if campos["tipo_memoria"] not in MEMORIA_GPU or campos["interfaz"] not in BUS_GPU:
            raise ValueError(fila["nombre"])
        if campos["potencia_minima_fuente_watts"] < campos["consumo_referencia_watts"]:
            raise ValueError(fila["nombre"])
        if campos["largo_mm"] < 1 or campos["consumo_referencia_watts"] < 1:
            raise ValueError(fila["nombre"])
        if not fila["nombre"].startswith(marca + " "):
            raise ValueError(fila["nombre"])
    elif modelo == "refrigeracion":
        if campos["tipo"] not in TIPOS_COOLER:
            raise ValueError(fila["nombre"])
        if campos["tipo"] == "Aire" and campos["tamanho_radiador_mm"] is not None:
            raise ValueError(fila["nombre"])
        if campos["tipo"] == "Líquida" and not campos["tamanho_radiador_mm"]:
            raise ValueError(fila["nombre"])
        if not fila["nombre"].startswith(marca + " "):
            raise ValueError(fila["nombre"])
    elif modelo == "almacenamiento_ssd":
        if campos["interfaz"] not in INTERFAZ_SSD or campos["formato"] not in FORMATO_SSD:
            raise ValueError(fila["nombre"])
        if campos["interfaz"] == "SATA III" and campos["formato"] != '2.5"':
            raise ValueError(fila["nombre"])
        if campos["interfaz"].startswith("NVMe") and campos["formato"] != "M.2 2280":
            raise ValueError(fila["nombre"])
    elif modelo == "gabinete":
        if campos["formato_soporte"] not in FORMATOS_PLACA or campos["material"] not in MATERIALES:
            raise ValueError(fila["nombre"])
        if campos["largo_max_gpu_mm"] < 1:
            raise ValueError(fila["nombre"])
    elif modelo == "fuente_de_poder":
        if campos["certificacion"] not in CERTIFICACIONES or campos["potencia_watts"] < 1:
            raise ValueError(fila["nombre"])
    elif modelo == "ventilador":
        if campos["tamanho_mm"] < 1 or campos["velocidad_rpm"] < 1:
            raise ValueError(fila["nombre"])
    if not fila["nombre"].startswith(marca + " "):
        raise ValueError(f"La marca no coincide con el nombre: {fila['nombre']}")
