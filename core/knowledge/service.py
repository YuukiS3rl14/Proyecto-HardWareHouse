"""Conocimiento institucional compartido (Sobre nosotros y chatbot)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from django.core.cache import cache
from django.urls import reverse

_JSON_PATH = Path(__file__).resolve().parent / 'hardwarehouse.json'
_CACHE_PREFIX = 'hw_company_knowledge'
_REQUIRED = ('identity', 'mission', 'vision', 'values', 'services', 'policies', 'contact', 'sections', 'faqs')
_SEGUIMIENTO = re.compile(
    r'^(y\b|tambien|también|ademas|además|eso|esa|cuentame mas|cuéntame más|y la|y el|y los|y las)\b',
    re.I,
)


class ConocimientoInvalido(ValueError):
    pass


def _ruta(nombre: str) -> str:
    return reverse(nombre)


def _enlaces() -> dict[str, str]:
    return {
        'contacto': _ruta('core:contacto'),
        'sobre': _ruta('core:sobrenosotros'),
        'tienda': _ruta('core:tienda'),
        'armado': _ruta('core:armado'),
        'pedidos': _ruta('core:mis_pedidos'),
    }


def _aplicar_plantilla(texto: str, datos: dict) -> str:
    def reemplazo(match: re.Match) -> str:
        clave = match.group(1)
        if clave in _enlaces():
            return _enlaces()[clave]
        if clave == 'mission':
            return datos['mission']
        if clave == 'vision':
            return datos['vision']
        if clave == 'values':
            return ' '.join(datos['values'])
        if clave == 'services':
            return ' '.join(datos['services'])
        if clave == 'identity.summary':
            return datos['identity']['summary']
        if clave == 'contact_block':
            return _bloque_contacto(datos)
        return match.group(0)

    return re.sub(r'\{([a-z0-9_.]+)\}', reemplazo, texto)


def _bloque_contacto(datos: dict) -> str:
    contacto = datos['contact']
    partes = [
        f'Canales publicados: formulario en {_ruta("core:contacto")}.',
        'Dirección, correo y teléfono que aparecen en el sitio son datos de ejemplo.',
    ]
    for campo in ('address', 'email', 'phone'):
        item = contacto[campo]
        if item.get('placeholder'):
            partes.append(
                f'{campo}: "{item["value"]}" está marcado como ejemplo. {item.get("note", "")}'.strip()
            )
    partes.append(f'Escríbenos en {_ruta("core:contacto")}.')
    return ' '.join(partes)


def validar_conocimiento(data: dict) -> None:
    if not isinstance(data, dict):
        raise ConocimientoInvalido('El conocimiento debe ser un objeto JSON.')
    faltan = [clave for clave in _REQUIRED if clave not in data]
    if faltan:
        raise ConocimientoInvalido(f'Faltan claves: {", ".join(faltan)}')
    identidad = data['identity']
    if not isinstance(identidad.get('name'), str) or not identidad['name'].strip():
        raise ConocimientoInvalido('identity.name es obligatorio.')
    años = identidad.get('years_in_business')
    if not isinstance(años, int) or años < 0:
        raise ConocimientoInvalido('identity.years_in_business debe ser un entero >= 0.')
    if not isinstance(data['values'], list) or not data['values']:
        raise ConocimientoInvalido('values debe ser una lista no vacía.')
    if not isinstance(data['services'], list) or not data['services']:
        raise ConocimientoInvalido('services debe ser una lista no vacía.')
    contacto = data['contact']
    for campo in ('address', 'email', 'phone'):
        item = contacto.get(campo)
        if not isinstance(item, dict) or 'placeholder' not in item or 'value' not in item:
            raise ConocimientoInvalido(f'contact.{campo} requiere value y placeholder.')
        if not isinstance(item['placeholder'], bool):
            raise ConocimientoInvalido(f'contact.{campo}.placeholder debe ser booleano.')
    ids = set()
    for faq in data['faqs']:
        if not faq.get('id') or not faq.get('question') or not faq.get('answer'):
            raise ConocimientoInvalido('Cada FAQ requiere id, question y answer.')
        if faq['id'] in ids:
            raise ConocimientoInvalido(f'FAQ duplicada: {faq["id"]}')
        ids.add(faq['id'])
    for seccion in data['sections']:
        if not seccion.get('id') or not seccion.get('text'):
            raise ConocimientoInvalido('Cada sección requiere id y text.')


def cargar_conocimiento() -> dict:
    mtime = int(_JSON_PATH.stat().st_mtime)
    clave = f'{_CACHE_PREFIX}:{mtime}'
    cached = cache.get(clave)
    if isinstance(cached, dict):
        return cached
    data = json.loads(_JSON_PATH.read_text(encoding='utf-8'))
    validar_conocimiento(data)
    cache.set(clave, data, 600)
    return data


def faq_por_id(clave: str) -> dict | None:
    for faq in cargar_conocimiento()['faqs']:
        if faq['id'] == clave:
            return faq
    return None


def texto_faq(clave: str) -> str | None:
    faq = faq_por_id(clave)
    if faq is None:
        return None
    return _aplicar_plantilla(faq['answer'], cargar_conocimiento())


def faq_items_pagina() -> list[dict]:
    datos = cargar_conocimiento()
    items = []
    for faq in datos['faqs']:
        if not faq.get('show_on_about'):
            continue
        items.append(
            {
                'clave': faq['id'],
                'titulo': faq['question'],
                'respuesta': _aplicar_plantilla(faq['answer'], datos),
            }
        )
    return items


def perfil_publico() -> dict:
    datos = cargar_conocimiento()
    contacto = datos['contact']
    return {
        'name': datos['identity']['name'],
        'summary': datos['identity']['summary'],
        'years_in_business': datos['identity']['years_in_business'],
        'mission': datos['mission'],
        'vision': datos['vision'],
        'values': list(datos['values']),
        'services': list(datos['services']),
        'address_placeholder': contacto['address']['placeholder'],
        'address_value': contacto['address']['value'],
        'address_note': contacto['address'].get('note', ''),
    }


def _normalizar(texto: str) -> str:
    return re.sub(r'\s+', ' ', (texto or '').lower()).strip()


def _puntuacion(texto: str, aliases: list[str]) -> int:
    puntos = 0
    for alias in aliases:
        if alias and alias in texto:
            puntos += len(alias)
    return puntos


def _candidatos(datos: dict) -> list[dict]:
    items = []
    for seccion in datos['sections']:
        items.append(
            {
                'id': seccion['id'],
                'kind': 'section',
                'intent': seccion.get('intent') or 'empresa',
                'title': seccion.get('title') or seccion['id'],
                'text': _aplicar_plantilla(seccion['text'], datos),
                'aliases': [a.lower() for a in seccion.get('aliases') or []],
            }
        )
    for faq in datos['faqs']:
        items.append(
            {
                'id': faq['id'],
                'kind': 'faq',
                'intent': faq.get('intent') or 'empresa',
                'title': faq['question'],
                'text': _aplicar_plantilla(faq['answer'], datos),
                'aliases': [a.lower() for a in faq.get('aliases') or []],
            }
        )
    return items


def _texto_consulta(texto: str, historial: list | None) -> str:
    actual = _normalizar(texto)
    if historial and _SEGUIMIENTO.search(actual):
        for item in reversed(historial):
            if isinstance(item, dict) and item.get('role') == 'user' and item.get('content'):
                return _normalizar(f'{item["content"]} {actual}')
    return actual


def buscar_conocimiento(texto: str, historial: list | None = None, tema: str | None = None) -> dict | None:
    datos = cargar_conocimiento()
    if tema:
        for item in _candidatos(datos):
            if item['id'] == tema:
                return item
    consulta = _texto_consulta(texto, historial)
    if len(consulta) < 3:
        return None
    mejor = None
    mejor_puntos = 0
    empates = []
    for item in _candidatos(datos):
        puntos = _puntuacion(consulta, item['aliases'])
        if puntos <= 0:
            continue
        if puntos > mejor_puntos:
            mejor = item
            mejor_puntos = puntos
            empates = [item]
        elif puntos == mejor_puntos:
            empates.append(item)
    if mejor is None:
        return None
    if len(empates) > 1 and re.search(r'\b(y|e)\b', consulta):
        textos = []
        vistos = set()
        for item in empates[:2]:
            if item['text'] in vistos:
                continue
            vistos.add(item['text'])
            textos.append(item['text'])
        if len(textos) > 1:
            combinado = dict(mejor)
            combinado['text'] = '\n'.join(textos)
            return combinado
    return mejor


_PREGUNTA_EMPRESA = re.compile(
    r'\b(empresa|mision|misión|vision|visión|valores|historia|servicios|quienes somos|'
    r'quiénes somos|quienes son|despacho|delivery|garantia|garantía|sobre nosotros)\b',
    re.I,
)


def responder_conocimiento(texto: str, historial: list | None = None, tema: str | None = None) -> dict | None:
    hallazgo = buscar_conocimiento(texto, historial=historial, tema=tema)
    if hallazgo is None:
        if tema or not _PREGUNTA_EMPRESA.search(texto or ''):
            return None
        return {
            'reply': (
                'No tengo ese dato verificado sobre HardWareHouse. '
                f'Puedes escribirnos en {_ruta("core:contacto")} y te orientamos con la información publicada.'
            ),
            'intent': 'clarification',
            'necesita_clarificacion': True,
            'response_type': 'clarification',
            'motor': 'reglas',
        }
    return {
        'reply': hallazgo['text'],
        'intent': hallazgo['intent'],
        'response_type': 'faq',
        'conocimiento': {
            'id': hallazgo['id'],
            'title': hallazgo['title'],
            'verified': True,
        },
        'motor': 'reglas',
    }


@lru_cache(maxsize=1)
def ruta_json() -> str:
    return str(_JSON_PATH)
