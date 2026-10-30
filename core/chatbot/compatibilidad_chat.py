"""Preguntas de compatibilidad resueltas con productos del ORM."""
from __future__ import annotations

import re

from core.catalogo.registry import CATALOGO_MODELOS
from core.chatbot.texto import normalizar_texto
from core.compatibilidad import (
    CLAVE_POR_CATEGORIA,
    ESTADO_COMPATIBLE,
    ESTADO_DATOS_INSUFICIENTES,
    ESTADO_INCOMPATIBLE,
    FORMATOS_RAM_CONOCIDOS,
    TIPOS_DDR_CONOCIDOS,
    evaluar_candidato,
    normalizar_spec,
)
from core.piezas_demo import sin_demo

_PREGUNTA_RAM = re.compile(
    r'\bque tipo de (?:memoria )?ram\b|\bque memoria ram\b|\bque ram puedo\b',
    re.I,
)
_PREFIJOS = frozenset(
    {
        'es',
        'son',
        'compatible',
        'compatibles',
        'puedo',
        'puede',
        'pueden',
        'podria',
        'se',
        'instalar',
        'poner',
        'montar',
        'usar',
        'el',
        'la',
        'los',
        'las',
        'un',
        'una',
        'en',
        'con',
        'para',
        'que',
        'tipo',
        'de',
        'memoria',
        'ram',
        'procesador',
        'procesadores',
        'placa',
        'madre',
        'motherboard',
        'mother',
        'tarjeta',
        'grafica',
        'graficas',
    }
)
_ORDEN_CANDIDATO = (
    'procesador',
    'memoria_ram',
    'tarjeta_grafica',
    'refrigeracion',
    'fuente_de_poder',
    'gabinete',
    'placa_madre',
)


def _norm(texto: str) -> str:
    limpio = normalizar_texto(texto)
    limpio = re.sub(r'[^\w\s]+', ' ', limpio)
    return re.sub(r'\s+', ' ', limpio).strip()


def _sin_prefijos(fragmento: str) -> str:
    palabras = _norm(fragmento).split()
    while palabras and palabras[0] in _PREFIJOS:
        palabras.pop(0)
    return ' '.join(palabras)


def _analizar(texto: str):
    norm = _norm(texto)
    if not norm:
        return None
    if _PREGUNTA_RAM.search(norm):
        encontrado = re.search(r'\b(?:en|para)\s+(.+)$', norm)
        if not encontrado:
            return None
        return ('ram_placa', _sin_prefijos(encontrado.group(1)))
    if re.search(r'\bes compatible\b', norm) and re.search(r'\bcon\b', norm):
        izquierda, derecha = norm.split(' con ', 1)
        return ('par', _sin_prefijos(izquierda), _sin_prefijos(derecha))
    if re.search(r'\bpuedo instalar\b', norm):
        encontrado = re.search(r'\binstalar\s+(.+?)\s+\ben\b\s+(.+)$', norm)
        if encontrado:
            return (
                'par',
                _sin_prefijos(encontrado.group(1)),
                _sin_prefijos(encontrado.group(2)),
            )
    return None


def _palabras(texto: str) -> list[str]:
    return [parte for parte in _norm(texto).split() if parte]


def _resolver(frase: str):
    tokens = _palabras(frase)
    if not tokens:
        return None
    encontrados = []
    for modelo, clave in CATALOGO_MODELOS:
        for producto in sin_demo(modelo.objects.select_related('proveedor')):
            bolsa = set(_palabras(f'{producto.proveedor.nombre} {producto.nombre}'))
            if all(token in bolsa for token in tokens):
                encontrados.append((len(bolsa), producto.pk, producto, clave))
    if not encontrados:
        return None
    encontrados.sort(key=lambda item: (item[0], item[1]))
    mejor = encontrados[0][0]
    top = [item for item in encontrados if item[0] == mejor]
    unicos = {(type(item[2]), item[2].pk): (item[2], item[3]) for item in top}
    if len(unicos) > 1:
        return 'ambiguo'
    return next(iter(unicos.values()))


def _paquete(reply: str, estado: str) -> dict:
    return {
        'reply': reply,
        'intent': 'compatibilidad',
        'response_type': 'compatibility',
        'motor': 'reglas',
        'compatibilidad': {'estado': estado},
    }


def _no_encontrado(nombre: str) -> dict:
    return _paquete(
        f'No encontré «{nombre}» en el catálogo, así que no puedo comprobar la compatibilidad.',
        'no_encontrado',
    )


def _respuesta_ram(nombre: str) -> dict:
    resuelto = _resolver(nombre)
    if resuelto is None:
        return _no_encontrado(nombre)
    if resuelto == 'ambiguo':
        return _paquete(
            f'Hay más de un producto que coincide con «{nombre}». '
            'No puedo decir qué memoria admite sin un único modelo.',
            'ambiguo',
        )
    producto, clave = resuelto
    if clave != 'placa_madre':
        return _paquete(
            f'{producto.nombre} no es una placa madre. '
            'No puedo indicar el tipo de RAM que admite.',
            'no_evaluada',
        )
    tipo = normalizar_spec(producto.tipo_ram_soportado)
    formato = normalizar_spec(getattr(producto, 'formato_ram_soportado', None))
    tipo_conocido = tipo in TIPOS_DDR_CONOCIDOS
    formato_conocido = formato in FORMATOS_RAM_CONOCIDOS
    if tipo_conocido and formato_conocido:
        return _paquete(
            f'{producto.nombre} admite memoria {tipo} {formato}. '
            'Ese dato está registrado en la placa.',
            'dato_catalogo',
        )
    if tipo_conocido:
        return _paquete(
            f'{producto.nombre} tiene registrado el tipo {tipo}. '
            'El formato DIMM o SO-DIMM no está en la ficha, así que no puedo confirmarlo.',
            ESTADO_DATOS_INSUFICIENTES,
        )
    return _paquete(
        f'La ficha de {producto.nombre} no tiene un tipo de RAM conocido. '
        'No puedo confirmar qué memoria se puede instalar.',
        ESTADO_DATOS_INSUFICIENTES,
    )


def _clave_candidata(piezas: dict) -> str:
    for clave in _ORDEN_CANDIDATO:
        if clave in piezas and not (clave == 'placa_madre' and len(piezas) > 1):
            return clave
    return next(iter(piezas))


def _texto_par(primero, segundo, evaluacion) -> dict:
    nombres = f'{primero.nombre} y {segundo.nombre}'
    if evaluacion.estado == ESTADO_COMPATIBLE:
        detalle = ', '.join(evaluacion.coincidencias) or evaluacion.etiqueta
        return _paquete(f'Sí. {nombres} son compatibles ({detalle}).', ESTADO_COMPATIBLE)
    if evaluacion.estado == ESTADO_INCOMPATIBLE:
        motivo = ' '.join(evaluacion.motivos) or 'No cumplen las reglas de compatibilidad.'
        return _paquete(f'No. {nombres} no son compatibles. {motivo}', ESTADO_INCOMPATIBLE)
    if evaluacion.estado == ESTADO_DATOS_INSUFICIENTES:
        motivo = ' '.join(evaluacion.motivos) or 'Faltan especificaciones para comprobarlo.'
        return _paquete(
            f'No puedo confirmar si {nombres} son compatibles. {motivo}',
            ESTADO_DATOS_INSUFICIENTES,
        )
    return _paquete(
        f'No hay datos suficientes para confirmar si {nombres} son compatibles.',
        evaluacion.estado,
    )


def _respuesta_par(nombre_a: str, nombre_b: str) -> dict:
    primero = _resolver(nombre_a)
    segundo = _resolver(nombre_b)
    if primero is None:
        return _no_encontrado(nombre_a)
    if segundo is None:
        return _no_encontrado(nombre_b)
    if primero == 'ambiguo' or segundo == 'ambiguo':
        return _paquete(
            'Hay más de un producto con ese nombre. '
            'No puedo comprobar la compatibilidad sin un único modelo de cada pieza.',
            'ambiguo',
        )
    producto_a, clave_a = primero
    producto_b, clave_b = segundo
    if clave_a not in CLAVE_POR_CATEGORIA or clave_b not in CLAVE_POR_CATEGORIA:
        return _paquete(
            f'No hay una regla de compatibilidad entre {producto_a.nombre} y {producto_b.nombre}. '
            'No puedo confirmar si son compatibles.',
            'no_evaluada',
        )
    if clave_a == clave_b:
        return _paquete(
            f'{producto_a.nombre} y {producto_b.nombre} son de la misma categoría. '
            'No puedo compararlas entre sí.',
            'no_evaluada',
        )
    piezas = {clave_a: producto_a, clave_b: producto_b}
    candidata = _clave_candidata(piezas)
    candidato = piezas.pop(candidata)
    evaluacion = evaluar_candidato(candidata, candidato, **piezas)
    return _texto_par(producto_a, producto_b, evaluacion)


def responder_si_compatibilidad(texto: str) -> dict | None:
    analisis = _analizar(texto or '')
    if analisis is None:
        return None
    if analisis[0] == 'ram_placa':
        return _respuesta_ram(analisis[1])
    return _respuesta_par(analisis[1], analisis[2])
