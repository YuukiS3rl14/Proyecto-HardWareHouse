"""Serializa y lee el catálogo demo en SQL y CSV, sin Django."""
from __future__ import annotations

import csv
import io
import re
from decimal import Decimal

from core.demo_catalog import COLUMNAS, TABLAS, build_catalog, nombre_comercial
from core.seed_sql import iter_sql_statements

SITE_URL_DEFECTO = "http://127.0.0.1:8000"

TABLA_A_MODELO = {tabla: modelo for modelo, tabla in TABLAS.items()}

ETIQUETAS = {
    "procesador": (
        ("socket", "Socket"),
        ("nucleos", "Núcleos"),
        ("frecuencia_base", "Frecuencia base (GHz)"),
        ("potencia_referencia_watts", "Potencia de referencia (W)"),
    ),
    "placa_madre": (
        ("socket_cpu", "Socket de CPU"),
        ("chipset", "Chipset"),
        ("formato", "Formato"),
        ("tipo_ram_soportado", "Tipo de RAM"),
        ("formato_ram_soportado", "Formato de RAM admitido"),
        ("ranuras_ram", "Ranuras de RAM"),
        ("capacidad_maxima_ram_gb", "Capacidad máxima de RAM (GB)"),
    ),
    "memoria_ram": (
        ("tipo_ddr", "Tipo DDR"),
        ("formato_ram", "Formato"),
        ("capacidad_gb", "Capacidad del producto (GB)"),
        ("modulos_por_producto", "Módulos por producto"),
        ("capacidad_modulo_gb", "Capacidad por módulo (GB)"),
        ("velocidad_mhz", "Velocidad indicada (MHz)"),
    ),
    "refrigeracion": (
        ("tipo", "Tipo de refrigeración"),
        ("socket_compatibles", "Sockets compatibles"),
        ("tamanho_radiador_mm", "Radiador (mm)"),
    ),
    "tarjeta_grafica": (
        ("vram_gb", "VRAM (GB)"),
        ("tipo_memoria", "Tipo de memoria"),
        ("interfaz", "Interfaz"),
        ("consumo_referencia_watts", "Consumo de referencia (W)"),
        ("potencia_minima_fuente_watts", "Fuente mínima recomendada (W)"),
        ("largo_mm", "Largo GPU (mm)"),
    ),
    "almacenamiento_ssd": (
        ("capacidad_gb", "Capacidad (GB)"),
        ("interfaz", "Interfaz"),
        ("formato", "Formato"),
    ),
    "almacenamiento_hdd": (
        ("capacidad_gb", "Capacidad (GB)"),
        ("velocidad_rpm", "Velocidad (RPM)"),
        ("cache_mb", "Caché (MB)"),
    ),
    "gabinete": (
        ("formato_soporte", "Formato admitido"),
        ("material", "Material"),
        ("ventiladores_incluidos", "Ventiladores incluidos"),
        ("largo_max_gpu_mm", "Largo máximo de GPU (mm)"),
    ),
    "fuente_de_poder": (
        ("potencia_watts", "Potencia (W)"),
        ("certificacion", "Certificación"),
        ("modular", "Modular"),
    ),
}

COLUMNAS_CSV = (
    "id",
    "modelo",
    "categoria",
    "marca",
    "nombre",
    "descripcion",
    "precio_clp",
    "stock",
    "especificaciones",
    "url_detalle",
    "titulo",
    "contenido",
)

DECIMALES = {"precio", "frecuencia_base"}


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _subconsulta_proveedor(marca: str) -> str:
    return f"(SELECT id FROM core_proveedor WHERE nombre = {sql_literal(marca)})"


def render_product_inserts(filas: list[dict] | None = None) -> str:
    filas = build_catalog() if filas is None else filas
    bloques = [
        "-- Productos demo. El proveedor se resuelve por nombre, no por un id fijo.\n",
        "-- Precio y stock son sintéticos; no son un precio de mercado verificado.\n",
    ]
    modelo_actual = None
    for fila in filas:
        if fila["modelo"] != modelo_actual:
            modelo_actual = fila["modelo"]
            bloques.append(f"\n-- {modelo_actual}\n")
        bloques.append(_insert_producto(fila))
    bloques.append("\n")
    return "".join(bloques)


def _insert_producto(fila: dict) -> str:
    columnas = COLUMNAS[fila["modelo"]]
    valores = []
    for columna in columnas:
        if columna == "id":
            valores.append(str(fila["pk"]))
        elif columna == "proveedor_id":
            valores.append(_subconsulta_proveedor(fila["marca"]))
        elif columna == "imagen":
            valores.append("NULL")
        elif columna in fila["campos"]:
            valores.append(sql_literal(fila["campos"][columna]))
        else:
            valores.append(sql_literal(fila[columna]))
    return (
        f"INSERT INTO {TABLAS[fila['modelo']]} ({', '.join(columnas)}) VALUES\n"
        f"({', '.join(valores)});\n"
    )


def _visible(valor) -> str:
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, Decimal):
        texto = format(valor, "f")
        if "." in texto:
            texto = texto.rstrip("0").rstrip(".")
        return texto
    return str(valor)


def especificaciones_de_fila(fila: dict) -> str:
    if fila["modelo"] == "ventilador":
        campos = fila["campos"]
        return "; ".join(
            (
                f"Tamaño (mm): {campos['tamanho_mm']}",
                f"Velocidad (RPM): {campos['velocidad_rpm']}",
                f"RGB: {'Sí' if campos['rgb'] else 'No'}",
            )
        )
    partes = []
    for clave, etiqueta in ETIQUETAS[fila["modelo"]]:
        valor = fila["campos"].get(clave)
        if valor is None or valor == "":
            continue
        partes.append(f"{etiqueta}: {_visible(valor)}")
    return "; ".join(partes)


def _url_detalle(site_url: str, modelo: str, pk: int) -> str:
    return f"{site_url.rstrip('/')}/detalle/{modelo}/{pk}/"


def _contenido(row: dict) -> str:
    lineas = [
        f"Producto: {nombre_comercial(row['marca'], row['nombre'])}",
        f"Categoría: {row['categoria']}",
        f"ID interno: {row['id']}",
        f"Precio (CLP): {row['precio_clp']}",
        f"Stock disponible: {row['stock']}",
    ]
    if row["descripcion"]:
        lineas.append(f"Descripción: {row['descripcion']}")
    if row["especificaciones"]:
        lineas.append(f"Especificaciones: {row['especificaciones']}")
    lineas.append(f"Más información: {row['url_detalle']}")
    return "\n".join(lineas)


def filas_csv(filas: list[dict], site_url: str = SITE_URL_DEFECTO) -> list[dict]:
    salida = []
    for fila in filas:
        row = {
            "id": f"{fila['modelo']}:{fila['pk']}",
            "modelo": fila["modelo"],
            "categoria": fila["categoria"],
            "marca": fila["marca"],
            "nombre": fila["nombre"],
            "descripcion": fila["descripcion"],
            "precio_clp": str(int(fila["precio"])),
            "stock": str(fila["stock"]),
            "especificaciones": especificaciones_de_fila(fila),
            "url_detalle": _url_detalle(site_url, fila["modelo"], fila["pk"]),
            "titulo": f"{nombre_comercial(fila['marca'], fila['nombre'])} ({fila['categoria']})",
            "contenido": "",
        }
        row["contenido"] = _contenido(row)
        salida.append(row)
    return salida


def render_csv(filas: list[dict] | None = None, site_url: str = SITE_URL_DEFECTO) -> str:
    filas = build_catalog() if filas is None else filas
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNAS_CSV, lineterminator="\n")
    writer.writeheader()
    for row in filas_csv(filas, site_url):
        writer.writerow(row)
    return buffer.getvalue()


def parse_csv(texto: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(texto.lstrip("\ufeff")))
    return list(reader)


def split_sql_values(body: str) -> list[str]:
    valores = []
    buffer: list[str] = []
    profundidad = 0
    en_texto = False
    i = 0
    while i < len(body):
        caracter = body[i]
        if en_texto:
            buffer.append(caracter)
            if caracter == "'":
                if i + 1 < len(body) and body[i + 1] == "'":
                    buffer.append("'")
                    i += 1
                else:
                    en_texto = False
        elif caracter == "'":
            en_texto = True
            buffer.append(caracter)
        elif caracter == "(":
            profundidad += 1
            buffer.append(caracter)
        elif caracter == ")":
            profundidad -= 1
            buffer.append(caracter)
        elif caracter == "," and profundidad == 0:
            valores.append("".join(buffer).strip())
            buffer = []
        else:
            buffer.append(caracter)
        i += 1
    if buffer and "".join(buffer).strip():
        valores.append("".join(buffer).strip())
    return valores


def _marca_de_subconsulta(token: str) -> str:
    coincidencia = re.search(r"nombre\s*=\s*'((?:''|[^'])*)'", token, flags=re.I)
    if not coincidencia:
        raise ValueError(f"No se pudo leer la marca del proveedor: {token}")
    return coincidencia.group(1).replace("''", "'")


def _decodificar(token: str, columna: str):
    token = token.strip()
    if token.upper() == "NULL":
        return None
    if token.upper() == "TRUE":
        return True
    if token.upper() == "FALSE":
        return False
    if token.startswith("'"):
        return token[1:-1].replace("''", "'")
    if columna in DECIMALES:
        return Decimal(token)
    return int(token)


def parse_product_inserts(sql: str) -> list[dict]:
    filas = []
    for sentencia in iter_sql_statements(sql):
        if not sentencia.lstrip().upper().startswith("INSERT INTO"):
            continue
        fila = _parse_insert(sentencia)
        if fila is not None:
            filas.append(fila)
    return filas


def _parse_insert(sentencia: str) -> dict | None:
    coincidencia = re.match(
        r"INSERT INTO\s+(?P<tabla>core_\w+)\s*\((?P<columnas>.*?)\)\s*VALUES\s*\(",
        sentencia,
        flags=re.I | re.S,
    )
    if not coincidencia:
        return None
    tabla = coincidencia.group("tabla").lower()
    modelo = TABLA_A_MODELO.get(tabla)
    if modelo is None:
        return None
    columnas = [columna.strip() for columna in coincidencia.group("columnas").split(",")]
    cuerpo = sentencia[coincidencia.end():].strip()
    if cuerpo.endswith(")"):
        cuerpo = cuerpo[:-1]
    tokens = split_sql_values(cuerpo)
    if len(tokens) != len(columnas):
        raise ValueError(
            f"{tabla} id esperado: {len(columnas)} columnas y {len(tokens)} valores."
        )
    fila = {"modelo": modelo, "campos": {}}
    for columna, token in zip(columnas, tokens):
        if columna == "proveedor_id":
            fila["marca"] = _marca_de_subconsulta(token)
        elif columna == "id":
            fila["pk"] = _decodificar(token, columna)
        elif columna == "imagen":
            continue
        elif columna in {"categoria", "nombre", "descripcion", "precio", "stock"}:
            fila[columna] = _decodificar(token, columna)
        else:
            fila["campos"][columna] = _decodificar(token, columna)
    return fila


def comparar_fuentes(filas_sql: list[dict], filas_csv: list[dict]) -> None:
    if len(filas_sql) != len(filas_csv):
        raise ValueError(
            f"El SQL tiene {len(filas_sql)} productos y el CSV {len(filas_csv)}."
        )
    csv_por_id = {fila["id"]: fila for fila in filas_csv}
    if len(csv_por_id) != len(filas_csv):
        raise ValueError("El CSV repite identificadores de producto.")
    for fila in filas_sql:
        ident = f"{fila['modelo']}:{fila['pk']}"
        csv_fila = csv_por_id.get(ident)
        if csv_fila is None:
            raise ValueError(f"El CSV no incluye {ident}.")
        esperado = {
            "modelo": fila["modelo"],
            "categoria": fila["categoria"],
            "marca": fila["marca"],
            "nombre": fila["nombre"],
            "descripcion": fila["descripcion"],
            "precio_clp": str(int(fila["precio"])),
            "stock": str(fila["stock"]),
            "especificaciones": especificaciones_de_fila(fila),
        }
        for clave, valor in esperado.items():
            actual = csv_fila.get(clave) or ""
            if actual != valor:
                raise ValueError(f"{ident} difiere en {clave}.")
