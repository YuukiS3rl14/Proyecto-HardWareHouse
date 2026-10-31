"""Consultas de catálogo en lenguaje natural (sinónimos, filtros, orden)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from typing import Literal

from core.catalogo.registry import categorias_disponibles
from core.chatbot.texto import normalizar_texto

OrdenCatalogo = Literal['relevancia', 'precio_asc', 'precio_desc', 'stock_desc']


def _normalizar_clave(texto: str) -> str:
    return normalizar_texto(texto)


_ALIAS_CATEGORIA: dict[str, str] = {
    _normalizar_clave(cat): cat for cat in categorias_disponibles()
}
_ALIAS_CATEGORIA.update(
    {
        'cpu': 'CPU',
        'procesador': 'CPU',
        'procesadores': 'CPU',
        'processor': 'CPU',
        'gpu': 'Tarjeta Gráfica',
        'grafica': 'Tarjeta Gráfica',
        'graficas': 'Tarjeta Gráfica',
        'tarjeta grafica': 'Tarjeta Gráfica',
        'tarjetas graficas': 'Tarjeta Gráfica',
        'tarjetas': 'Tarjeta Gráfica',
        'tarjeta de video': 'Tarjeta Gráfica',
        'video': 'Tarjeta Gráfica',
        'ram': 'Memoria RAM',
        'memoria': 'Memoria RAM',
        'memorias': 'Memoria RAM',
        'ddr': 'Memoria RAM',
        'placa madre': 'Placa Madre',
        'motherboard': 'Placa Madre',
        'mother': 'Placa Madre',
        'ssd': 'SSD',
        'nvme': 'SSD',
        'disco ssd': 'SSD',
        'hdd': 'Disco Duro HDD',
        'disco duro': 'Disco Duro HDD',
        'gabinete': 'Gabinete',
        'case': 'Gabinete',
        'fuente': 'Fuente de Poder',
        'psu': 'Fuente de Poder',
        'fuente de poder': 'Fuente de Poder',
        'cooler': 'Refrigeración',
        'refrigeracion': 'Refrigeración',
        'ventilador': 'Ventilador',
        'fan': 'Ventilador',
    }
)

_MARCAS_HINT = (
    'asus',
    'msi',
    'gigabyte',
    'asrock',
    'corsair',
    'kingston',
    'samsung',
    'wd',
    'seagate',
    'evga',
    'cooler master',
    'nzxt',
    'intel',
    'amd',
    'nvidia',
)

_ORDEN_BARATO = re.compile(
    r'\b(mas barat[ao]|más barat[ao]|mas economic[ao]|más economic[ao]|'
    r'menor precio|precio mas bajo|precio más bajo|la mas barata|la más barata|'
    r'cheapest|mas economica)\b',
    re.I,
)
_ORDEN_CARO = re.compile(
    r'\b(mas car[ao]|más car[ao]|mayor precio|precio mas alto|precio más alto|'
    r'mas premium|la mas cara|la más cara|most expensive)\b',
    re.I,
)
_PRECIO_MAX = re.compile(
    r'\b(?:menos de|bajo|hasta|maximo|máximo|max)\s*\$?\s*([\d.\s]+)\s*(?:mil|k\b)?',
    re.I,
)
_FRASE_PRECIO = re.compile(
    r'\b(?:por\s+)?(?:menos(?:\s+de)?|mas(?:\s+de)?|hasta|desde|bajo|sobre|maximo|minimo|max|min)\s+'
    r'\d[\d\s]*(?:\s*(?:mil|k|pesos|clp))?',
    re.I,
)
_PRECIO_MIN = re.compile(
    r'\b(?:mas de|más de|sobre|desde|minimo|mínimo|min)\s*\$?\s*([\d.\s]+)\s*(?:mil|k\b)?',
    re.I,
)
_STOCK_DISPONIBLE = re.compile(
    r'\b(con stock|en stock|disponible|disponibles|que tengan stock)\b',
    re.I,
)

_STOPWORDS = re.compile(
    r'\b(busco|buscar|quiero|necesito|precio de|cuanto cuesta|cuánto cuesta|hay|tienen|tiene|'
    r'me interesa|algun|algún|una|un|el|la|los|las|de|para|del|al|en|que|cual|cuales|'
    r'muestrame|muestra|mostrar|ver|dime|ensename|'
    r'este|esta|estos|estas|por|jugar|juego|juegos|gamer|gaming|'
    r'mas barata|más barata|mas barato|más barato|mas cara|más cara|'
    r'mas caro|más caro|mas economic[ao]|más economic[ao]|'
    r'menor precio|mayor precio|cheapest|disponible|disponibles|con stock|en stock|'
    r'stock|agotado|marca|modelo)\b',
    re.I,
)


def _parse_monto(fragmento: str, texto_completo: str) -> int | None:
    raw = fragmento.replace(' ', '').replace('.', '')
    if not raw.isdigit():
        return None
    valor = int(raw)
    if re.search(r'\bmil\b|\bk\b', texto_completo, re.I) and valor < 10000:
        valor *= 1000
    return valor


@dataclass
class ConsultaCatalogoNL:
    categoria: str | None = None
    marca: str | None = None
    orden: OrdenCatalogo = 'relevancia'
    precio_min: int | None = None
    precio_max: int | None = None
    solo_con_stock: bool = False
    q: str = ''
    pks_por_modelo: dict | None = None

    def requiere_orm_estructurado(self) -> bool:
        return bool(
            self.categoria
            or self.marca
            or self.orden != 'relevancia'
            or self.precio_min is not None
            or self.precio_max is not None
            or self.solo_con_stock
        )

    def a_filtros(self, limit: int = 6):
        from core.chatbot.search import FiltrosCatalogo

        lim = limit
        if self.orden in ('precio_asc', 'precio_desc') and self.categoria:
            lim = min(lim, 3)
        return FiltrosCatalogo(
            q=self.q,
            categoria=self.categoria,
            marca=self.marca,
            precio_min=self.precio_min,
            precio_max=self.precio_max,
            solo_con_stock=self.solo_con_stock,
            limit=lim,
            orden=self.orden,
            pks_por_modelo=self.pks_por_modelo,
        )


def _una_edicion(izquierda: str, derecha: str) -> bool:
    """Una sustitución, un agregado o un borrado. Sirve para un typo corto."""
    if izquierda == derecha:
        return False
    largo_izq, largo_der = len(izquierda), len(derecha)
    if abs(largo_izq - largo_der) > 1:
        return False
    if largo_izq == largo_der:
        return sum(a != b for a, b in zip(izquierda, derecha)) == 1
    if largo_izq > largo_der:
        izquierda, derecha = derecha, izquierda
        largo_izq, largo_der = largo_der, largo_izq
    indice_corto = indice_largo = 0
    diferencias = 0
    while indice_corto < largo_izq and indice_largo < largo_der:
        if izquierda[indice_corto] != derecha[indice_largo]:
            diferencias += 1
            if diferencias > 1:
                return False
            indice_largo += 1
            continue
        indice_corto += 1
        indice_largo += 1
    return True


def _alias_de_categoria(token: str, categoria: str) -> bool:
    for alias, cat in _ALIAS_CATEGORIA.items():
        if cat != categoria or not alias or ' ' in alias:
            continue
        if token == alias:
            return True
        if len(token) >= 8 and len(alias) >= 8 and _una_edicion(token, alias):
            return True
    return False


def _resolver_categoria(norm: str) -> str | None:
    if norm in _ALIAS_CATEGORIA:
        return _ALIAS_CATEGORIA[norm]
    for alias, cat in sorted(_ALIAS_CATEGORIA.items(), key=lambda x: -len(x[0])):
        if len(alias) >= 3 and re.search(rf'\b{re.escape(alias)}\b', norm):
            return cat
    categorias = set()
    for token in norm.split():
        if len(token) < 8:
            continue
        for alias, cat in _ALIAS_CATEGORIA.items():
            if ' ' in alias or len(alias) < 8:
                continue
            if _una_edicion(token, alias):
                categorias.add(cat)
    if len(categorias) == 1:
        return categorias.pop()
    return None


def limpiar_q_catalogo(q: str, categoria: str | None = None) -> str:
    """Deja el nombre del producto. La categoría, el precio y el pedido no se buscan en el nombre."""
    norm = normalizar_texto(q or '')
    norm = re.sub(r'[^\w\s]+', ' ', norm)
    norm = _FRASE_PRECIO.sub(' ', norm)
    norm = _STOPWORDS.sub(' ', norm)
    if categoria:
        for alias, cat in _ALIAS_CATEGORIA.items():
            if cat == categoria and alias:
                norm = re.sub(rf'\b{re.escape(alias)}\b', ' ', norm)
        for token in norm.split():
            if _alias_de_categoria(token, categoria):
                norm = re.sub(rf'\b{re.escape(token)}\b', ' ', norm)
    norm = re.sub(r'\s+', ' ', norm).strip()
    if not norm or norm in _ALIAS_CATEGORIA or len(norm) < 2:
        return ''
    return norm


def extraer_consulta_catalogo(texto: str) -> ConsultaCatalogoNL:
    original = (texto or '').strip()
    norm = normalizar_texto(original)
    norm = re.sub(r'[^\w\s]+', ' ', norm)
    norm = re.sub(r'\s+', ' ', norm).strip()

    consulta = ConsultaCatalogoNL()

    if _ORDEN_BARATO.search(norm) or _ORDEN_BARATO.search(normalizar_texto(original)):
        consulta.orden = 'precio_asc'
        consulta.solo_con_stock = True
    elif _ORDEN_CARO.search(norm) or _ORDEN_CARO.search(normalizar_texto(original)):
        consulta.orden = 'precio_desc'

    if _STOCK_DISPONIBLE.search(norm):
        consulta.solo_con_stock = True

    m_max = _PRECIO_MAX.search(original)
    if m_max:
        consulta.precio_max = _parse_monto(m_max.group(1), original)
    m_min = _PRECIO_MIN.search(original)
    if m_min:
        consulta.precio_min = _parse_monto(m_min.group(1), original)

    consulta.categoria = _resolver_categoria(norm)

    for marca in _MARCAS_HINT:
        if re.search(rf'\b{re.escape(marca)}\b', norm):
            if marca in ('intel', 'amd', 'nvidia'):
                consulta.q = marca
            else:
                consulta.marca = marca.title() if ' ' not in marca else marca.title()
            break

    resto = _STOPWORDS.sub(' ', norm)
    if consulta.categoria:
        for alias, cat in _ALIAS_CATEGORIA.items():
            if cat == consulta.categoria:
                resto = re.sub(rf'\b{re.escape(alias)}\b', ' ', resto)
    resto = re.sub(r'\s+', ' ', resto).strip()
    if resto and len(resto) >= 2 and not consulta.q:
        consulta.q = resto
    consulta.q = limpiar_q_catalogo(consulta.q, consulta.categoria)

    return consulta
