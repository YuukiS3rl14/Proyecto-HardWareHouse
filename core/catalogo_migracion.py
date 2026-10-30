"""Exporta e importa solo el catálogo, con IDs nuevos y sin tocar compras."""
from __future__ import annotations

import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Model
from django.db.utils import IntegrityError

from core.catalogo.registry import CATALOGO_MODELOS, MODEL_BY_API_NAME
from core.models import (
    Carrito,
    Comentario,
    Favorito,
    ItemCarrito,
    ItemPedido,
    PagoBoleta,
    Pedido,
    Proveedor,
)

FORMATO = 'hardwarehouse-catalogo-v1'
VERSION = 1
CLAVES_RAIZ = frozenset({'formato', 'version', 'proveedores', 'productos'})
CLAVES_PROHIBIDAS = frozenset({
    'id', 'pk', 'proveedor_id', 'usuario', 'usuarios', 'password', 'passwords',
    'pedido', 'pedidos', 'boleta', 'boletas', 'pago', 'pagos', 'ipn',
    'sesion', 'sesiones', 'carrito', 'carritos', 'email', 'transaccion_id',
})
OMITIR_PRODUCTO = frozenset({'id', 'categoria', 'proveedor', 'imagen'})
COMUNES = frozenset({'nombre', 'descripcion', 'precio', 'stock'})
TABLAS_SOLO_CONTEO = frozenset({'paypal_ipn', 'django_session'})
MAX_ARCHIVO = 5_000_000


class CatalogoMigracionError(Exception):
    """El archivo o la base no permiten una importación segura."""


def normalizar_clave(valor: str) -> str:
    """Clave de comparación: sin acentos, minúsculas y espacios simples."""
    texto = unicodedata.normalize('NFKD', valor or '')
    texto = ''.join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = texto.casefold().strip()
    return re.sub(r'\s+', ' ', texto)


def exportar_documento() -> dict:
    """Catálogo actual sin IDs ni datos de clientes, pedidos o pagos."""
    proveedores = [proveedor.nombre for proveedor in Proveedor.objects.order_by('nombre', 'pk')]
    productos = []
    for modelo, familia in CATALOGO_MODELOS:
        consulta = modelo.objects.select_related('proveedor').order_by(
            'proveedor__nombre', 'nombre', 'pk'
        )
        for obj in consulta:
            productos.append(_producto_exportado(familia, obj))
    documento = {
        'formato': FORMATO,
        'version': VERSION,
        'proveedores': proveedores,
        'productos': productos,
    }
    validar_documento(documento)
    return documento


def escribir_exportacion(destino: Path) -> dict:
    documento = exportar_documento()
    temporal = destino.with_suffix(destino.suffix + '.tmp')
    temporal.write_text(
        json.dumps(documento, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    temporal.replace(destino)
    return documento


def leer_documento(origen: Path) -> dict:
    if not origen.is_file():
        raise CatalogoMigracionError(f'No existe el archivo {origen.name}.')
    if origen.stat().st_size > MAX_ARCHIVO:
        raise CatalogoMigracionError('El archivo supera el tamaño permitido.')
    try:
        data = json.loads(origen.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogoMigracionError('El archivo no es JSON legible.') from exc
    if not isinstance(data, dict):
        raise CatalogoMigracionError('El archivo no contiene un objeto JSON.')
    return data


def validar_documento(documento: dict) -> dict:
    if not isinstance(documento, dict):
        raise CatalogoMigracionError('El catálogo tiene que ser un objeto JSON.')
    prohibidas = CLAVES_PROHIBIDAS.intersection(documento)
    if prohibidas:
        raise CatalogoMigracionError('El archivo incluye datos que no son del catálogo.')
    desconocidas = set(documento) - CLAVES_RAIZ
    if desconocidas:
        raise CatalogoMigracionError('El archivo tiene secciones que este importador no acepta.')
    if documento.get('formato') != FORMATO or documento.get('version') != VERSION:
        raise CatalogoMigracionError('La versión del archivo de catálogo no es compatible.')

    proveedores = documento.get('proveedores')
    productos = documento.get('productos')
    if not isinstance(proveedores, list) or not isinstance(productos, list):
        raise CatalogoMigracionError('Proveedores y productos tienen que ser listas.')

    limpios_proveedores = []
    claves_proveedor = set()
    for nombre in proveedores:
        limpio = _texto_corto(nombre, 100, 'proveedor')
        clave = normalizar_clave(limpio)
        if not clave:
            raise CatalogoMigracionError('Hay un proveedor sin nombre.')
        if clave in claves_proveedor:
            raise CatalogoMigracionError(f'El archivo repite el proveedor {limpio}.')
        claves_proveedor.add(clave)
        limpios_proveedores.append({'nombre': limpio, 'clave': clave})

    limpios_productos = []
    claves_producto = set()
    for crudo in productos:
        if not isinstance(crudo, dict):
            raise CatalogoMigracionError('Hay un producto que no es un objeto.')
        if CLAVES_PROHIBIDAS.intersection(crudo):
            raise CatalogoMigracionError('Un producto trae un identificador o un dato privado.')
        familia = crudo.get('familia')
        modelo = MODEL_BY_API_NAME.get(familia)
        if modelo is None:
            raise CatalogoMigracionError('Hay un producto de una familia desconocida.')
        proveedor = _texto_corto(crudo.get('proveedor'), 100, 'proveedor del producto')
        clave_proveedor = normalizar_clave(proveedor)
        if clave_proveedor not in claves_proveedor:
            raise CatalogoMigracionError(
                f'Falta el proveedor {proveedor} en la lista de proveedores.'
            )
        nombre = _texto_corto(crudo.get('nombre'), 200, 'nombre')
        clave_nombre = normalizar_clave(nombre)
        if not clave_nombre:
            raise CatalogoMigracionError('Hay un producto sin nombre.')
        clave = (familia, clave_proveedor, clave_nombre)
        if clave in claves_producto:
            raise CatalogoMigracionError(
                f'El archivo repite {familia} / {proveedor} / {nombre}.'
            )
        claves_producto.add(clave)
        descripcion = crudo.get('descripcion', '')
        if not isinstance(descripcion, str) or len(descripcion) > 20000:
            raise CatalogoMigracionError(f'La descripción de {nombre} no es válida.')
        campos = _campos_producto(modelo, crudo.get('campos'), nombre)
        limpios_productos.append({
            'familia': familia,
            'proveedor': proveedor,
            'clave_proveedor': clave_proveedor,
            'nombre': nombre,
            'clave_nombre': clave_nombre,
            'descripcion': descripcion,
            'precio': _decimal(crudo.get('precio'), 'precio', nombre),
            'stock': _entero(crudo.get('stock'), 'stock', nombre),
            'campos': campos,
        })
    return {'proveedores': limpios_proveedores, 'productos': limpios_productos}


def importar_documento(documento: dict, *, apply: bool) -> dict:
    limpio = validar_documento(documento)
    if not apply:
        with transaction.atomic():
            resumen = _clasificar(limpio)
            transaction.set_rollback(True)
        resumen['apply'] = False
        return resumen

    try:
        with transaction.atomic():
            _bloquear_catalogo()
            snapshot = _snapshot()
            resumen = _clasificar(limpio)
            _insertar(resumen)
            _exigir_intactos(snapshot)
    except IntegrityError as exc:
        raise CatalogoMigracionError(
            'No se pudo insertar sin modificar registros existentes.'
        ) from exc
    resumen['apply'] = True
    return resumen


def destino_legible() -> str:
    """Host y base, nunca usuario ni contraseña."""
    host = str(connection.settings_dict.get('HOST') or 'local')
    nombre = str(connection.settings_dict.get('NAME') or '')
    if any(marca in valor for valor in (host, nombre) for marca in ('://', '@')):
        return 'destino=oculto'
    return f'host={host} base={nombre}'


def _producto_exportado(familia: str, obj: Model) -> dict:
    modelo = type(obj)
    campos = {}
    for field in _campos_especificacion(modelo):
        campos[field.name] = _exportar_valor(field, getattr(obj, field.attname))
    return {
        'familia': familia,
        'proveedor': obj.proveedor.nombre,
        'nombre': obj.nombre,
        'descripcion': obj.descripcion or '',
        'precio': _exportar_valor(modelo._meta.get_field('precio'), obj.precio),
        'stock': obj.stock,
        'campos': campos,
    }


def _campos_especificacion(modelo):
    campos = []
    for field in modelo._meta.concrete_fields:
        if field.primary_key or field.is_relation or field.name in OMITIR_PRODUCTO | COMUNES:
            continue
        campos.append(field)
    return campos


def _campos_producto(modelo, crudo, nombre: str) -> dict:
    if not isinstance(crudo, dict):
        raise CatalogoMigracionError(f'Faltan las especificaciones de {nombre}.')
    if CLAVES_PROHIBIDAS.intersection(crudo):
        raise CatalogoMigracionError(f'{nombre} trae un identificador en sus especificaciones.')
    esperados = {field.name: field for field in _campos_especificacion(modelo)}
    if set(crudo) != set(esperados):
        raise CatalogoMigracionError(f'Las especificaciones de {nombre} no coinciden con la familia.')
    convertidos = {}
    for nombre_campo, field in esperados.items():
        valor = _convertir_campo(field, crudo[nombre_campo], nombre)
        if field.choices and valor is not None and valor not in dict(field.flatchoices):
            raise CatalogoMigracionError(f'{nombre} tiene un valor no permitido en {nombre_campo}.')
        convertidos[nombre_campo] = valor
    return convertidos


def _convertir_campo(field, valor, nombre: str):
    from django.db import models

    if isinstance(field, models.DecimalField):
        return _decimal(valor, field.name, nombre)
    if isinstance(field, models.BooleanField):
        if valor is None and field.null:
            return None
        if not isinstance(valor, bool):
            raise CatalogoMigracionError(f'{nombre}: {field.name} tiene que ser verdadero o falso.')
        return valor
    if isinstance(field, models.IntegerField):
        if valor is None and field.null:
            return None
        return _entero(valor, field.name, nombre)
    if isinstance(field, (models.CharField, models.TextField)):
        if valor is None and field.null:
            return None
        return _texto_corto(valor, field.max_length or 20000, f'{nombre}.{field.name}')
    raise CatalogoMigracionError(f'No se puede importar el campo {field.name}.')


def _texto_corto(valor, largo: int, etiqueta: str) -> str:
    if not isinstance(valor, str):
        raise CatalogoMigracionError(f'{etiqueta} tiene que ser texto.')
    limpio = valor.strip()
    if len(limpio) > largo:
        raise CatalogoMigracionError(f'{etiqueta} es demasiado largo.')
    return limpio


def _decimal(valor, etiqueta: str, nombre: str) -> Decimal:
    if isinstance(valor, bool) or isinstance(valor, float) or not isinstance(valor, str):
        raise CatalogoMigracionError(f'{nombre}: {etiqueta} tiene que ser un decimal en texto.')
    try:
        numero = Decimal(valor)
    except InvalidOperation as exc:
        raise CatalogoMigracionError(f'{nombre}: {etiqueta} no es un decimal.') from exc
    if not numero.is_finite() or numero < 0:
        raise CatalogoMigracionError(f'{nombre}: {etiqueta} no puede ser negativo.')
    return numero


def _entero(valor, etiqueta: str, nombre: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise CatalogoMigracionError(f'{nombre}: {etiqueta} tiene que ser un entero.')
    if valor < 0:
        raise CatalogoMigracionError(f'{nombre}: {etiqueta} no puede ser negativo.')
    return valor


def _exportar_valor(field, valor):
    from django.db import models

    if valor is None:
        return None
    if isinstance(field, models.DecimalField):
        cuantia = Decimal('1').scaleb(-field.decimal_places)
        return format(Decimal(valor).quantize(cuantia), 'f')
    return valor


def _clasificar(limpio: dict) -> dict:
    grupos = _grupos_proveedor()
    indices = {familia: _grupos_producto(modelo) for modelo, familia in CATALOGO_MODELOS}
    proveedores = []
    for item in limpio['proveedores']:
        coincidencias = grupos.get(item['clave'], [])
        if not coincidencias:
            accion = 'crear'
        elif len(coincidencias) == 1:
            accion = 'reutilizar'
        else:
            accion = 'ambiguo'
        proveedores.append({**item, 'accion': accion, 'coincidencias': len(coincidencias)})

    productos = []
    for item in limpio['productos']:
        proveedor = next(
            candidato for candidato in proveedores if candidato['clave'] == item['clave_proveedor']
        )
        if proveedor['accion'] == 'ambiguo':
            productos.append({**item, 'accion': 'ambiguo', 'motivo': 'proveedor_duplicado', 'distinto': False})
            continue
        coincidencias = indices[item['familia']].get((item['clave_proveedor'], item['clave_nombre']), [])
        if not coincidencias:
            productos.append({**item, 'accion': 'insertar', 'motivo': '', 'distinto': False})
            continue
        if len(coincidencias) > 1:
            productos.append({**item, 'accion': 'ambiguo', 'motivo': 'nombre_duplicado', 'distinto': False})
            continue
        distinto = _distinto(coincidencias[0], item)
        productos.append({**item, 'accion': 'ya_existe', 'motivo': '', 'distinto': distinto})

    return {
        'proveedores': proveedores,
        'productos': productos,
        'proveedores_crear': sum(1 for item in proveedores if item['accion'] == 'crear'),
        'proveedores_reutilizar': sum(1 for item in proveedores if item['accion'] == 'reutilizar'),
        'proveedores_ambiguos': sum(1 for item in proveedores if item['accion'] == 'ambiguo'),
        'insertar': sum(1 for item in productos if item['accion'] == 'insertar'),
        'ya_existe': sum(1 for item in productos if item['accion'] == 'ya_existe'),
        'distintos': sum(1 for item in productos if item['accion'] == 'ya_existe' and item['distinto']),
        'ambiguos': sum(1 for item in productos if item['accion'] == 'ambiguo'),
    }


def _grupos_proveedor() -> dict[str, list[Proveedor]]:
    grupos: dict[str, list[Proveedor]] = {}
    for proveedor in Proveedor.objects.order_by('pk'):
        grupos.setdefault(normalizar_clave(proveedor.nombre), []).append(proveedor)
    return grupos


def _grupos_producto(modelo) -> dict[tuple[str, str], list]:
    grupos: dict[tuple[str, str], list] = {}
    for obj in modelo.objects.select_related('proveedor').order_by('pk'):
        clave = (normalizar_clave(obj.proveedor.nombre), normalizar_clave(obj.nombre))
        grupos.setdefault(clave, []).append(obj)
    return grupos


def _distinto(obj, item: dict) -> bool:
    if obj.nombre != item['nombre'] or (obj.descripcion or '') != item['descripcion']:
        return True
    if Decimal(obj.precio) != item['precio'] or obj.stock != item['stock']:
        return True
    for nombre, esperado in item['campos'].items():
        if getattr(obj, nombre) != esperado:
            return True
    return False


def _insertar(resumen: dict) -> None:
    grupos = _grupos_proveedor()
    creados: dict[str, Proveedor] = {}
    for item in resumen['proveedores']:
        if item['accion'] != 'crear':
            continue
        proveedor = Proveedor(nombre=item['nombre'])
        proveedor.full_clean()
        proveedor.save()
        creados[item['clave']] = proveedor

    for item in resumen['productos']:
        if item['accion'] != 'insertar':
            continue
        proveedor = creados.get(item['clave_proveedor'])
        if proveedor is None:
            coincidencias = grupos.get(item['clave_proveedor'], [])
            if len(coincidencias) != 1:
                raise CatalogoMigracionError('El proveedor quedó ambiguo durante la importación.')
            proveedor = coincidencias[0]
        modelo = MODEL_BY_API_NAME[item['familia']]
        obj = modelo(
            proveedor=proveedor,
            nombre=item['nombre'],
            descripcion=item['descripcion'],
            precio=item['precio'],
            stock=item['stock'],
            **item['campos'],
        )
        try:
            obj.full_clean()
        except ValidationError as exc:
            raise CatalogoMigracionError(f'No se puede insertar {item["nombre"]}.') from exc
        obj.save()


def _bloquear_catalogo() -> None:
    list(Proveedor.objects.select_for_update().order_by('pk').values_list('pk', flat=True))
    for modelo, _familia in CATALOGO_MODELOS:
        list(modelo.objects.select_for_update().order_by('pk').values_list('pk', flat=True))


def _snapshot() -> dict:
    return {
        'proveedores': {obj.pk: _valores(obj) for obj in Proveedor.objects.order_by('pk')},
        'productos': {
            familia: {obj.pk: _valores(obj) for obj in modelo.objects.order_by('pk')}
            for modelo, familia in CATALOGO_MODELOS
        },
        'usuarios': {obj.pk: _valores(obj) for obj in User.objects.order_by('pk')},
        'pedidos': {obj.pk: _valores(obj) for obj in Pedido.objects.order_by('pk')},
        'items_pedido': {obj.pk: _valores(obj) for obj in ItemPedido.objects.order_by('pk')},
        'boletas': {obj.pk: _valores(obj) for obj in PagoBoleta.objects.order_by('pk')},
        'carritos': {obj.pk: _valores(obj) for obj in Carrito.objects.order_by('pk')},
        'items_carrito': {obj.pk: _valores(obj) for obj in ItemCarrito.objects.order_by('pk')},
        'favoritos': {obj.pk: _valores(obj) for obj in Favorito.objects.order_by('pk')},
        'comentarios': {obj.pk: _valores(obj) for obj in Comentario.objects.order_by('pk')},
        'referencias': _referencias_compra(),
        'conteos': {tabla: _contar_tabla(tabla) for tabla in sorted(TABLAS_SOLO_CONTEO)},
    }


def _exigir_intactos(antes: dict) -> None:
    despues = _snapshot()
    for etiqueta in (
        'proveedores', 'usuarios', 'pedidos', 'items_pedido', 'boletas',
        'carritos', 'items_carrito', 'favoritos', 'comentarios',
    ):
        if not _previos_iguales(antes[etiqueta], despues[etiqueta]):
            raise CatalogoMigracionError(
                'Se revirtió la importación porque cambiaron registros que no son altas de catálogo.'
            )
    for familia, filas in antes['productos'].items():
        if not _previos_iguales(filas, despues['productos'][familia]):
            raise CatalogoMigracionError(
                'Se revirtió la importación porque cambió un producto que ya existía.'
            )
    if antes['referencias'] != despues['referencias'] or antes['conteos'] != despues['conteos']:
        raise CatalogoMigracionError(
            'Se revirtió la importación porque cambiaron compras, sesiones o IPN.'
        )


def _previos_iguales(antes: dict, despues: dict) -> bool:
    for pk, fila in antes.items():
        if despues.get(pk) != fila:
            return False
    return True


def _referencias_compra() -> tuple:
    nombres = []
    pares = (
        ItemPedido.objects.exclude(producto_pk__isnull=True)
        .order_by('producto_modelo', 'producto_pk')
        .values_list('producto_modelo', 'producto_pk')
        .distinct()
    )
    for familia, pk in pares:
        modelo = MODEL_BY_API_NAME.get(familia)
        obj = modelo.objects.filter(pk=pk).first() if modelo is not None else None
        nombres.append((familia, pk, None if obj is None else obj.nombre))
    return tuple(nombres)


def _valores(obj: Model) -> tuple:
    return tuple(
        (field.attname, _canon(getattr(obj, field.attname)))
        for field in obj._meta.concrete_fields
    )


def _canon(valor):
    if isinstance(valor, Decimal):
        return format(valor, 'f')
    if isinstance(valor, UUID):
        return str(valor)
    return valor


def _contar_tabla(tabla: str) -> int | None:
    if tabla not in TABLAS_SOLO_CONTEO:
        raise CatalogoMigracionError('Tabla fuera del control de la importación.')
    with connection.cursor() as cursor:
        cursor.execute('SELECT to_regclass(%s)', [tabla])
        if cursor.fetchone()[0] is None:
            return None
        cursor.execute(f'SELECT COUNT(*) FROM {tabla}')
        return cursor.fetchone()[0]
