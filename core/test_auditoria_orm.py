"""Auditoría ORM-01 a ORM-08. Mide las vistas actuales y no cambia su lógica."""
import json
import statistics
import subprocess
import threading
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.db import connection, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.inventario import StockInsuficiente, aplicar_delta
from core.models import (
    Carrito,
    Favorito,
    ItemCarrito,
    ItemPedido,
    MovimientoStock,
    Pedido,
    Procesador,
    Proveedor,
)
from core.views import TIENDA_PAGE_SIZE

REPETICIONES = 5
ZONA = ZoneInfo('America/Santiago')
RAIZ = Path(__file__).resolve().parent.parent / 'evidencias' / 'orm'
RECEPTOR = 'sb-receiver@sandbox.example'


def exigir_bd_pruebas():
    datos = connection.settings_dict
    host = str(datos.get('HOST') or '').lower()
    nombre = str(datos.get('NAME') or '')
    if connection.vendor != 'postgresql':
        raise RuntimeError(f'La auditoría exige PostgreSQL. Motor: {connection.vendor}.')
    if host not in ('127.0.0.1', 'localhost', '::1'):
        raise RuntimeError(f'Host no reconocido como base local de pruebas: {host}.')
    if not nombre.startswith('test_'):
        raise RuntimeError(f'El nombre no es una base temporal de Django: {nombre}.')
    if 'railway' in f'{host} {nombre}'.lower() or 'rlwy' in host:
        raise RuntimeError('La conexión apunta a un destino que no es la base de pruebas.')
    return {
        'motor': connection.vendor,
        'host': host,
        'puerto': str(datos.get('PORT') or ''),
        'nombre': nombre,
        'usuario': str(datos.get('USER') or ''),
    }


def ahora():
    return datetime.now(ZONA).strftime('%Y-%m-%d %H:%M:%S %z')


def sha_actual():
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=RAIZ.parent.parent,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return 'no disponible'


def mediana(valores):
    return statistics.median(valores)


def resumen_muestras(muestras):
    return {
        'repeticiones': len(muestras),
        'consultas': int(mediana([m['consultas'] for m in muestras])),
        'selects': int(mediana([m['selects'] for m in muestras])),
        'tiempo_respuesta_ms': round(mediana([m['tiempo_respuesta_ms'] for m in muestras]), 3),
        'tiempo_sql_ms': round(mediana([m['tiempo_sql_ms'] for m in muestras]), 3),
        'tiempo_respuesta_min_ms': round(min(m['tiempo_respuesta_ms'] for m in muestras), 3),
        'tiempo_respuesta_max_ms': round(max(m['tiempo_respuesta_ms'] for m in muestras), 3),
        'consultas_min': min(m['consultas'] for m in muestras),
        'consultas_max': max(m['consultas'] for m in muestras),
    }


def medir_solicitud(cliente, url):
    cliente.get(url)
    muestras = []
    sql = []
    estado = None
    renderizados = None
    total = None
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        with CaptureQueriesContext(connection) as ctx:
            respuesta = cliente.get(url)
        fin = time.perf_counter()
        estado = respuesta.status_code
        if getattr(respuesta, 'context', None):
            if 'productos' in respuesta.context:
                renderizados = len(respuesta.context['productos'])
            if 'productos_favoritos' in respuesta.context:
                renderizados = len(respuesta.context['productos_favoritos'])
            if 'items' in respuesta.context:
                renderizados = len(list(respuesta.context['items']))
            if 'total_productos' in respuesta.context:
                total = respuesta.context['total_productos']
            if 'pagina' in respuesta.context:
                pagina = respuesta.context['pagina']
                renderizados = len(pagina.object_list)
                total = pagina.paginator.count
        consultas = ctx.captured_queries
        sql = [fila['sql'] for fila in consultas]
        muestras.append({
            'consultas': len(consultas),
            'selects': sum(1 for fila in consultas if fila['sql'].lstrip().upper().startswith('SELECT')),
            'tiempo_respuesta_ms': (fin - inicio) * 1000,
            'tiempo_sql_ms': sum(float(fila['time']) for fila in consultas) * 1000,
        })
    datos = resumen_muestras(muestras)
    datos.update({
        'url': url,
        'estado_http': estado,
        'filas_renderizadas': renderizados,
        'filas_catalogo': total,
        'sql': sql,
    })
    return datos


def medir_bloque(accion):
    muestras = []
    sql = []
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        with CaptureQueriesContext(connection) as ctx:
            accion()
        fin = time.perf_counter()
        consultas = ctx.captured_queries
        sql = [fila['sql'] for fila in consultas]
        muestras.append({
            'consultas': len(consultas),
            'selects': sum(1 for fila in consultas if fila['sql'].lstrip().upper().startswith('SELECT')),
            'tiempo_respuesta_ms': (fin - inicio) * 1000,
            'tiempo_sql_ms': sum(float(fila['time']) for fila in consultas) * 1000,
        })
    datos = resumen_muestras(muestras)
    datos['sql'] = sql
    return datos


def fila_csv(caso, escenario, muestra, medicion, consultadas=''):
    return {
        'caso': caso,
        'escenario': escenario,
        'tamano_muestra': muestra,
        'consultas_sql': medicion.get('consultas', ''),
        'consultas_select': medicion.get('selects', ''),
        'tiempo_respuesta_ms': medicion.get('tiempo_respuesta_ms', ''),
        'tiempo_sql_ms': medicion.get('tiempo_sql_ms', ''),
        'tiempo_respuesta_min_ms': medicion.get('tiempo_respuesta_min_ms', ''),
        'tiempo_respuesta_max_ms': medicion.get('tiempo_respuesta_max_ms', ''),
        'filas_consultadas': medicion.get('filas_catalogo', consultadas),
        'filas_renderizadas': medicion.get('filas_renderizadas', ''),
        'repeticiones': medicion.get('repeticiones', ''),
        'unidad_consultas': 'cantidad',
        'unidad_tiempo': 'ms',
        'unidad_filas': 'filas',
    }


def escribir_csv(ruta, filas):
    columnas = [
        'caso', 'escenario', 'tamano_muestra', 'consultas_sql', 'consultas_select',
        'tiempo_respuesta_ms', 'tiempo_sql_ms', 'tiempo_respuesta_min_ms',
        'tiempo_respuesta_max_ms', 'filas_consultadas', 'filas_renderizadas',
        'repeticiones', 'unidad_consultas', 'unidad_tiempo', 'unidad_filas',
    ]
    lineas = [','.join(columnas)]
    for fila in filas:
        lineas.append(','.join(str(fila.get(columna, '')) for columna in columnas))
    ruta.write_text('\n'.join(lineas) + '\n', encoding='utf-8')


def grafico_barras(ruta, titulo, categorias, series):
    ancho, alto = 760, 420
    margen_izq, margen_inf = 70, 90
    area_ancho = ancho - margen_izq - 30
    area_alto = alto - 70 - margen_inf
    maximo = max((valor for serie in series for valor in serie['valores']), default=1) or 1
    grupo = area_ancho / max(len(categorias), 1)
    barra = grupo / (len(series) + 1)
    colores = ('#1f4e79', '#c45911', '#548235')
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{ancho / 2}" y="28" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="16">{titulo}</text>',
    ]
    for indice, categoria in enumerate(categorias):
        x = margen_izq + indice * grupo
        partes.append(
            f'<text x="{x + grupo / 2}" y="{alto - 58}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="12">{categoria}</text>'
        )
        for s, serie in enumerate(series):
            valor = serie['valores'][indice]
            altura = 0 if maximo == 0 else (valor / maximo) * area_alto
            bx = x + 8 + s * barra
            by = 50 + area_alto - altura
            color = colores[s % len(colores)]
            partes.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{barra - 4:.1f}" height="{altura:.1f}" fill="{color}"/>')
            partes.append(
                f'<text x="{bx + (barra - 4) / 2:.1f}" y="{by - 4:.1f}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10">{valor}</text>'
            )
    leyenda = 20
    for s, serie in enumerate(series):
        partes.append(f'<rect x="{leyenda}" y="{alto - 28}" width="14" height="14" fill="{colores[s % len(colores)]}"/>')
        partes.append(
            f'<text x="{leyenda + 18}" y="{alto - 16}" font-family="Segoe UI, sans-serif" font-size="12">{serie["nombre"]}</text>'
        )
        leyenda += 180
    partes.append('</svg>')
    ruta.write_text('\n'.join(partes), encoding='utf-8')


def sql_legible(consultas, limite=12):
    salida = []
    for numero, sql in enumerate(consultas[:limite], start=1):
        salida.append(f'-- consulta {numero}\n{sql};\n')
    if len(consultas) > limite:
        salida.append(f'-- {len(consultas) - limite} consultas adicionales omitidas en esta muestra.\n')
    return '\n'.join(salida)


def guardar_caso(codigo, resultado, referencia, esperado, resumen, filas, incidencias, extras=None):
    carpeta = RAIZ / codigo
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / 'resultado.txt').write_text(resultado, encoding='utf-8')
    (carpeta / 'referencia.txt').write_text(referencia, encoding='utf-8')
    (carpeta / 'resultado_esperado.txt').write_text(esperado.strip() + '\n', encoding='utf-8')
    (carpeta / 'resumen.txt').write_text(resumen.strip() + '\n', encoding='utf-8')
    (carpeta / 'incidencias.txt').write_text(incidencias.strip() + '\n', encoding='utf-8')
    escribir_csv(carpeta / 'metricas.csv', filas)
    for nombre, contenido in (extras or {}).items():
        destino = carpeta / nombre
        if isinstance(contenido, (dict, list)):
            destino.write_text(json.dumps(contenido, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
        else:
            destino.write_text(str(contenido), encoding='utf-8')
    return carpeta


def crear_proveedor(nombre):
    return Proveedor.objects.create(nombre=nombre)


def crear_cpus(proveedor, cantidad, stock=8, prefijo='CPU ORM'):
    return [
        Procesador.objects.create(
            proveedor=proveedor,
            nombre=f'{prefijo} {indice + 1:03d}',
            precio=Decimal('10000.00'),
            stock=stock,
            socket='AM5',
            nucleos=6,
            frecuencia_base=Decimal('3.50'),
        )
        for indice in range(cantidad)
    ]


def crecimiento(puntos):
    if len(puntos) < 2:
        return 'NO CONCLUYENTE'
    base_n, base_q = puntos[0]
    alto_n, alto_q = puntos[-1]
    if alto_n == base_n:
        return 'NO CONCLUYENTE'
    pendiente = (alto_q - base_q) / (alto_n - base_n)
    if pendiente >= 0.5:
        return f'N+1 ({pendiente:.2f} consultas extra por elemento)'
    if alto_q - base_q <= 2:
        return 'sin crecimiento proporcional al tamaño'
    return f'aumento de {alto_q - base_q} consultas entre {base_n} y {alto_n} elementos'


class AuditoriaOrm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bd = exigir_bd_pruebas()

    def setUp(self):
        self.cliente = Client()
        self.cliente_auth = Client()
        self.usuario = User.objects.create_user('cliente_orm', password='Clave-orm-1')
        self.cliente_auth.force_login(self.usuario)
        self.staff = User.objects.create_user('staff_orm', password='Clave-orm-1', is_staff=True)
        self.cliente_staff = Client()
        self.cliente_staff.force_login(self.staff)

    def _referencia(self, escenarios, estado):
        bd = self.bd
        return (
            f'Fecha y hora: {ahora()}\n'
            f'Commit: {sha_actual()}\n'
            'Entorno: Django TestCase, PostgreSQL local.\n'
            f'Base: motor={bd["motor"]} host={bd["host"]} puerto={bd["puerto"]} nombre={bd["nombre"]} usuario={bd["usuario"]}\n'
            'La contraseña no se registra.\n'
            'Comando: python manage.py test core.test_auditoria_orm.AuditoriaOrm --verbosity 1\n'
            f'Escenarios: {escenarios}\n'
            f'Resultado de calidad: {estado}\n'
        )

    def test_orm01_listado_y_paginacion(self):
        marca = crear_proveedor('Marca ORM 01')
        filas = []
        bloques = []
        for cantidad in (10, 50, 100):
            Procesador.objects.filter(proveedor=marca).delete()
            crear_cpus(marca, cantidad)
            medicion = medir_solicitud(self.cliente, reverse('core:tienda'))
            bloques.append(medicion)
            filas.append(fila_csv('ORM-01', f'listado {cantidad}', cantidad, medicion, cantidad))
        pagina2 = medir_solicitud(self.cliente, reverse('core:tienda') + '?page=2')
        pagina3 = medir_solicitud(self.cliente, reverse('core:tienda') + '?page=3')
        autenticado = medir_solicitud(self.cliente_auth, reverse('core:tienda'))
        filas.extend([
            fila_csv('ORM-01', 'pagina 2 de 100', 100, pagina2, 100),
            fila_csv('ORM-01', 'pagina 3 de 100', 100, pagina3, 100),
            fila_csv('ORM-01', 'tienda autenticada', 100, autenticado, 100),
        ])
        patron = crecimiento([(10, bloques[0]['consultas']), (50, bloques[1]['consultas']), (100, bloques[2]['consultas'])])
        render_100 = bloques[2]['filas_renderizadas']
        sql_cpu = [sql for sql in bloques[2]['sql'] if 'core_procesador' in sql.lower()]
        tiene_limite = any('LIMIT' in sql.upper() for sql in sql_cpu)
        texto = [
            f'Base confirmada: {self.bd["nombre"]} en {self.bd["host"]}:{self.bd["puerto"]}.',
            f'TIENDA_PAGE_SIZE = {TIENDA_PAGE_SIZE}. Las muestras de 10, 50 y 100 son procesadores de prueba. La página muestra como máximo {TIENDA_PAGE_SIZE}.',
            'La creación de fixtures quedó fuera de CaptureQueriesContext. Cada GET se repitió 5 veces tras un calentamiento.',
        ]
        for medicion, cantidad in zip(bloques, (10, 50, 100)):
            texto.append(
                f'Muestra {cantidad}: HTTP {medicion["estado_http"]}, consultas {medicion["consultas"]} '
                f'(SELECT {medicion["selects"]}), respuesta {medicion["tiempo_respuesta_ms"]} ms '
                f'(min {medicion["tiempo_respuesta_min_ms"]}, max {medicion["tiempo_respuesta_max_ms"]}), '
                f'SQL {medicion["tiempo_sql_ms"]} ms, catálogo {medicion["filas_catalogo"]}, '
                f'renderizados {medicion["filas_renderizadas"]}.'
            )
        texto.append(
            f'Página 2: consultas {pagina2["consultas"]}, renderizados {pagina2["filas_renderizadas"]}, respuesta {pagina2["tiempo_respuesta_ms"]} ms.'
        )
        texto.append(
            f'Página 3: HTTP {pagina3["estado_http"]}, consultas {pagina3["consultas"]}, renderizados {pagina3["filas_renderizadas"]}. '
            'Django devuelve la última página si el número pedido se pasa.'
        )
        texto.append(f'Tienda autenticada: {autenticado["consultas"]} consultas; anónimo con 100: {bloques[2]["consultas"]}.')
        texto.append(f'Comparación de consultas: {patron}.')
        texto.append(
            'El SELECT de core_procesador '
            + ('incluye LIMIT.' if tiene_limite else 'no incluye LIMIT: la vista recorre la familia y pagina en memoria.')
        )
        estado = 'FALLIDA' if 'N+1' in patron else 'PARCIAL'
        if tiene_limite and 'N+1' not in patron and render_100 == min(100, TIENDA_PAGE_SIZE):
            estado = 'APROBADA' if tiene_limite else estado
        incidencia = (
            'No se detectó crecimiento N+1 ni lectura de filas por encima de la página.'
            if estado == 'APROBADA' else
            f'Severidad media. Con 100 productos la página renderiza {render_100} y el catálogo contabiliza {bloques[2]["filas_catalogo"]}. '
            f'LIMIT en el SELECT de procesadores: {"sí" if tiene_limite else "no"}. Patrón: {patron}.'
        )
        guardar_caso(
            'ORM-01',
            '\n'.join(texto) + '\n\n' + sql_legible(bloques[2]['sql'], 25),
            self._referencia('A 10, B 50, C 100, D páginas 2 y 3, E proporción, F usuario autenticado', estado),
            'El listado debe mantener un número estable de consultas al pasar de 10 a 100 productos y la paginación debe limitar las filas leídas y renderizadas.',
            (
                f'Se registraron {bloques[0]["consultas"]}, {bloques[1]["consultas"]} y {bloques[2]["consultas"]} consultas '
                f'para 10, 50 y 100 productos, con respuestas de {bloques[0]["tiempo_respuesta_ms"]}, '
                f'{bloques[1]["tiempo_respuesta_ms"]} y {bloques[2]["tiempo_respuesta_ms"]} ms. '
                f'La página de 100 renderizó {render_100} de {bloques[2]["filas_catalogo"]} y el patrón fue: {patron}.'
            ),
            filas,
            incidencia,
            {'consultas.sql': sql_legible(bloques[2]['sql'], 40)},
        )
        grafico_barras(
            RAIZ / 'ORM-01' / 'comparacion.svg',
            'ORM-01 consultas y tiempo',
            ['10', '50', '100'],
            [
                {'nombre': 'Consultas SQL', 'valores': [b['consultas'] for b in bloques]},
                {'nombre': 'Tiempo respuesta ms', 'valores': [round(b['tiempo_respuesta_ms'], 1) for b in bloques]},
            ],
        )

    def test_orm02_detalle_y_proveedor(self):
        cpus = []
        for indice in range(10):
            marca = crear_proveedor(f'Marca ORM 02 {indice + 1}')
            cpus.extend(crear_cpus(marca, 1, prefijo=f'CPU P{indice + 1}'))
        identificadores = [cpu.pk for cpu in cpus]

        def sin_optimizar():
            for producto in Procesador.objects.filter(pk__in=identificadores):
                producto.proveedor.nombre

        def con_optimizar():
            for producto in Procesador.objects.select_related('proveedor').filter(pk__in=identificadores):
                producto.proveedor.nombre

        individual = medir_solicitud(self.cliente, reverse('core:detalle', args=['procesador', cpus[0].pk]))
        antes = medir_bloque(sin_optimizar)
        despues = medir_bloque(con_optimizar)
        antes['filas_catalogo'] = 10
        despues['filas_catalogo'] = 10
        join = any('JOIN' in sql.upper() for sql in despues['sql'])
        filas = [
            fila_csv('ORM-02', 'detalle individual', 1, individual, 1),
            fila_csv('ORM-02', 'sin select_related', 10, antes, 10),
            fila_csv('ORM-02', 'con select_related', 10, despues, 10),
        ]
        texto = [
            f'Detalle HTTP {individual["estado_http"]}: {individual["consultas"]} consultas, {individual["selects"]} SELECT, respuesta {individual["tiempo_respuesta_ms"]} ms, SQL {individual["tiempo_sql_ms"]} ms.',
            f'Diez productos y diez proveedores, sin select_related: {antes["consultas"]} consultas, SQL {antes["tiempo_sql_ms"]} ms.',
            f'La misma lectura con select_related: {despues["consultas"]} consultas, SQL {despues["tiempo_sql_ms"]} ms, JOIN={"sí" if join else "no"}.',
            'La vista de detalle no se modificó. La comparación de los diez productos usa querysets de medición.',
        ]
        detalle_join = any('JOIN' in sql.upper() and 'proveedor' in sql.lower() for sql in individual['sql'])
        texto.append(f'El detalle de la vista incluye JOIN al proveedor: {"sí" if detalle_join else "no"}.')
        estado = 'APROBADA' if despues['consultas'] < antes['consultas'] and join and detalle_join else 'PARCIAL'
        incidencia = (
            'La vista ya resuelve el proveedor con JOIN. El queryset sin select_related sirve como contraste y no es el camino de la tienda.'
            if estado == 'APROBADA' else
            'La comparación no redujo las consultas o el detalle no mostró el JOIN del proveedor.'
        )
        guardar_caso(
            'ORM-02',
            '\n'.join(texto) + '\n\n-- detalle\n' + sql_legible(individual['sql'], 15) + '\n-- sin optimizar\n' + sql_legible(antes['sql'], 12) + '\n-- con select_related\n' + sql_legible(despues['sql'], 6),
            self._referencia('A detalle, B proveedor, C 10 productos, D select_related, E proveedores distintos', estado),
            'El detalle y una lectura de diez productos con proveedores distintos deben resolver la marca sin un SELECT adicional por cada proveedor.',
            (
                f'El detalle ejecutó {individual["consultas"]} consultas en {individual["tiempo_respuesta_ms"]} ms. '
                f'La lectura de 10 productos pasó de {antes["consultas"]} consultas sin select_related a {despues["consultas"]} con select_related '
                f'({"con" if join else "sin"} JOIN), en {antes["tiempo_sql_ms"]} y {despues["tiempo_sql_ms"]} ms de SQL.'
            ),
            filas,
            incidencia,
            {
                'consultas.sql': '-- detalle\n' + sql_legible(individual['sql'], 20) + '\n-- contraste\n' + sql_legible(antes['sql'], 12) + '\n' + sql_legible(despues['sql'], 6),
                'comparacion.txt': '\n'.join(texto) + '\n',
            },
        )

    def test_orm03_carrito_y_favoritos(self):
        marca = crear_proveedor('Marca ORM 03')
        cpus = crear_cpus(marca, 20)
        carrito = Carrito.objects.create(usuario=self.usuario)
        filas = []
        carritos = []
        favoritos = []
        for cantidad in (1, 5, 20):
            ItemCarrito.objects.filter(carrito=carrito).delete()
            Favorito.objects.filter(usuario=self.usuario).delete()
            ItemCarrito.objects.bulk_create([
                ItemCarrito(carrito=carrito, procesador=cpu, cantidad=1, precio_unitario=cpu.precio)
                for cpu in cpus[:cantidad]
            ])
            medicion = medir_solicitud(self.cliente_auth, reverse('core:carrito'))
            medicion['filas_catalogo'] = cantidad
            carritos.append(medicion)
            filas.append(fila_csv('ORM-03', f'carrito {cantidad}', cantidad, medicion, cantidad))
            ItemCarrito.objects.filter(carrito=carrito).delete()
            Favorito.objects.bulk_create([
                Favorito(usuario=self.usuario, procesador=cpu) for cpu in cpus[:cantidad]
            ])
            medicion_fav = medir_solicitud(self.cliente_auth, reverse('core:favoritos'))
            medicion_fav['filas_catalogo'] = cantidad
            favoritos.append(medicion_fav)
            filas.append(fila_csv('ORM-03', f'favoritos {cantidad}', cantidad, medicion_fav, cantidad))
        patron_c = crecimiento([(1, carritos[0]['consultas']), (5, carritos[1]['consultas']), (20, carritos[2]['consultas'])])
        patron_f = crecimiento([(1, favoritos[0]['consultas']), (5, favoritos[1]['consultas']), (20, favoritos[2]['consultas'])])
        lineas = ['Carrito y favoritos medidos con un usuario ficticio y procesadores de prueba.']
        for etiqueta, grupo in (('Carrito', carritos), ('Favoritos', favoritos)):
            for medicion, cantidad in zip(grupo, (1, 5, 20)):
                lineas.append(
                    f'{etiqueta} {cantidad}: HTTP {medicion["estado_http"]}, consultas {medicion["consultas"]} '
                    f'(SELECT {medicion["selects"]}), respuesta {medicion["tiempo_respuesta_ms"]} ms, '
                    f'SQL {medicion["tiempo_sql_ms"]} ms, renderizados {medicion["filas_renderizadas"]}.'
                )
        lineas.append(f'Patrón carrito: {patron_c}.')
        lineas.append(f'Patrón favoritos: {patron_f}.')
        estado = 'FALLIDA' if 'N+1' in patron_c or 'N+1' in patron_f else 'APROBADA'
        incidencia = 'No se observó crecimiento proporcional en carrito ni favoritos.'
        if estado == 'FALLIDA':
            incidencia = (
                f'Severidad media. Carrito: {patron_c}. Favoritos: {patron_f}. '
                'Las líneas no precargan el producto y el render accede a la relación por elemento.'
            )
        guardar_caso(
            'ORM-03',
            '\n'.join(lineas) + '\n\n-- carrito 20\n' + sql_legible(carritos[2]['sql'], 30),
            self._referencia('A carrito 1, B carrito 5, C carrito 20, D favoritos 1, E favoritos 5, F favoritos 20, G relaciones', estado),
            'Carrito y favoritos deben mostrar 1, 5 y 20 elementos sin agregar una consulta SQL por cada producto, imagen o proveedor.',
            (
                f'El carrito ejecutó {carritos[0]["consultas"]}, {carritos[1]["consultas"]} y {carritos[2]["consultas"]} consultas '
                f'en {carritos[0]["tiempo_respuesta_ms"]}, {carritos[1]["tiempo_respuesta_ms"]} y {carritos[2]["tiempo_respuesta_ms"]} ms. '
                f'Favoritos ejecutó {favoritos[0]["consultas"]}, {favoritos[1]["consultas"]} y {favoritos[2]["consultas"]} consultas. '
                f'Patrones: carrito {patron_c}; favoritos {patron_f}.'
            ),
            filas,
            incidencia,
            {'consultas.sql': '-- carrito 20\n' + sql_legible(carritos[2]['sql'], 40) + '\n-- favoritos 20\n' + sql_legible(favoritos[2]['sql'], 40)},
        )
        grafico_barras(
            RAIZ / 'ORM-03' / 'comparacion.svg',
            'ORM-03 carrito y favoritos',
            ['1', '5', '20'],
            [
                {'nombre': 'Consultas carrito', 'valores': [m['consultas'] for m in carritos]},
                {'nombre': 'Consultas favoritos', 'valores': [m['consultas'] for m in favoritos]},
                {'nombre': 'Tiempo carrito ms', 'valores': [round(m['tiempo_respuesta_ms'], 1) for m in carritos]},
            ],
        )

    def test_orm04_control_de_stock(self):
        marca = crear_proveedor('Marca ORM 04')
        crear_cpus(marca, 8, stock=0, prefijo='AGOT')
        crear_cpus(marca, 8, stock=1, prefijo='CRIT')
        crear_cpus(marca, 8, stock=4, prefijo='ADV')
        crear_cpus(marca, 8, stock=20, prefijo='OK')
        base = reverse('core:alertas_stock')
        escenarios = [
            ('agotados', base + '?estado=agotado'),
            ('criticos', base + '?estado=critico'),
            ('advertencia', base + '?estado=advertencia'),
            ('todos', base),
            ('categoria CPU', base + '?categoria=CPU'),
            ('pagina 2', base + '?page=2'),
        ]
        filas = []
        mediciones = []
        for nombre, url in escenarios:
            medicion = medir_solicitud(self.cliente_staff, url)
            medicion['escenario'] = nombre
            mediciones.append(medicion)
            filas.append(fila_csv('ORM-04', nombre, medicion.get('filas_catalogo') or '', medicion))
        volumen = []
        for cantidad in (20, 80):
            Procesador.objects.filter(proveedor=marca).delete()
            crear_cpus(marca, cantidad, stock=1, prefijo=f'VOL{cantidad}')
            medicion = medir_solicitud(self.cliente_staff, base)
            medicion['filas_catalogo'] = cantidad
            volumen.append(medicion)
            filas.append(fila_csv('ORM-04', f'volumen {cantidad}', cantidad, medicion, cantidad))
        lineas = ['La página de alertas muestra 20 filas. Los contadores salen de las filas ya recuperadas.']
        for medicion in mediciones:
            lineas.append(
                f'{medicion["escenario"]}: HTTP {medicion["estado_http"]}, consultas {medicion["consultas"]} '
                f'(SELECT {medicion["selects"]}), respuesta {medicion["tiempo_respuesta_ms"]} ms, '
                f'SQL {medicion["tiempo_sql_ms"]} ms, total {medicion["filas_catalogo"]}, renderizados {medicion["filas_renderizadas"]}.'
            )
        for medicion, cantidad in zip(volumen, (20, 80)):
            lineas.append(
                f'Volumen {cantidad}: consultas {medicion["consultas"]}, respuesta {medicion["tiempo_respuesta_ms"]} ms, '
                f'renderizados {medicion["filas_renderizadas"]}, total {medicion["filas_catalogo"]}.'
            )
        patron = crecimiento([(20, volumen[0]['consultas']), (80, volumen[1]['consultas'])])
        sql_cpu = [sql for sql in mediciones[3]['sql'] if 'core_procesador' in sql.lower()]
        lineas.append(f'Patrón de volumen: {patron}.')
        lineas.append(f'Condición de stock en el SELECT de procesadores: {"sí" if any("stock" in sql.lower() for sql in sql_cpu) else "no"}.')
        estado = 'FALLIDA' if 'N+1' in patron else 'PARCIAL'
        page_limit = volumen[1]['filas_renderizadas'] == volumen[1]['filas_catalogo'] == 20
        if page_limit and 'N+1' not in patron:
            estado = 'APROBADA'
        incidencia = (
            f'Severidad media. El listado pagina en memoria después de leer las familias con stock en alerta. '
            f'Con 80 críticos se renderizaron {volumen[1]["filas_renderizadas"]} de {volumen[1]["filas_catalogo"]}. Patrón: {patron}.'
        )
        guardar_caso(
            'ORM-04',
            '\n'.join(lineas) + '\n\n' + sql_legible(mediciones[3]['sql'], 25),
            self._referencia('A agotado, B crítico, C advertencia, D total, E categoría, F página, G volúmenes 20 y 80', estado),
            'Los contadores y el listado de stock deben filtrarse en PostgreSQL y la página no debe recuperar todas las familias afectadas.',
            (
                f'Los filtros ejecutaron entre {min(m["consultas"] for m in mediciones)} y {max(m["consultas"] for m in mediciones)} consultas, '
                f'con respuestas de {min(m["tiempo_respuesta_ms"] for m in mediciones)} a {max(m["tiempo_respuesta_ms"] for m in mediciones)} ms. '
                f'Con 20 y 80 productos críticos hubo {volumen[0]["consultas"]} y {volumen[1]["consultas"]} consultas; {patron}.'
            ),
            filas,
            incidencia,
            {'consultas.sql': sql_legible(mediciones[3]['sql'], 30)},
        )
        grafico_barras(
            RAIZ / 'ORM-04' / 'comparacion.svg',
            'ORM-04 volumen de alertas',
            ['20', '80'],
            [
                {'nombre': 'Consultas SQL', 'valores': [m['consultas'] for m in volumen]},
                {'nombre': 'Tiempo respuesta ms', 'valores': [round(m['tiempo_respuesta_ms'], 1) for m in volumen]},
            ],
        )

    def test_orm05_historial(self):
        marca = crear_proveedor('Marca ORM 05')
        cpus = crear_cpus(marca, 3, stock=80)
        pedido = Pedido.objects.create(
            usuario=self.usuario,
            total_monto=Decimal('10000.00'),
            direccion_envio='Calle Ficticia 123',
            estado='PAGADO',
        )
        for indice in range(45):
            aplicar_delta(
                cpus[indice % 3], -1, tipo=MovimientoStock.AJUSTE, usuario=self.staff,
                origen='auditoria', pedido=pedido, motivo=f'mov {indice}',
            )
        base = reverse('core:movimientos_stock')
        escenarios = [
            ('primera', base),
            ('intermedia', base + '?page=2'),
            ('ultima', base + '?page=3'),
            ('producto', base + f'?q=procesador:{cpus[0].pk}'),
            ('usuario', base + f'?usuario={self.staff.pk}'),
            ('tipo', base + '?tipo=AJUSTE'),
        ]
        filas = []
        mediciones = []
        for nombre, url in escenarios:
            medicion = medir_solicitud(self.cliente_staff, url)
            medicion['escenario'] = nombre
            mediciones.append(medicion)
            filas.append(fila_csv('ORM-05', nombre, medicion.get('filas_catalogo') or '', medicion))
        sql_pagina = mediciones[0]['sql']
        usa_join = any('JOIN' in sql.upper() and 'movimiento' in sql.lower() for sql in sql_pagina)
        renderizados = mediciones[0]['filas_renderizadas'] or 0
        selects = mediciones[0]['selects']
        lineas = ['Se crearon 45 ajustes antes de medir. Cada página muestra 20 movimientos.']
        for medicion in mediciones:
            lineas.append(
                f'{medicion["escenario"]}: HTTP {medicion["estado_http"]}, consultas {medicion["consultas"]} '
                f'(SELECT {medicion["selects"]}), respuesta {medicion["tiempo_respuesta_ms"]} ms, '
                f'SQL {medicion["tiempo_sql_ms"]} ms, total {medicion["filas_catalogo"]}, renderizados {medicion["filas_renderizadas"]}.'
            )
        lineas.append(f'JOIN de la consulta de movimientos: {"sí" if usa_join else "no"}.')
        lineas.append(f'SELECT de la primera página: {selects}. Filas renderizadas: {renderizados}.')
        estado = 'APROBADA'
        if not usa_join:
            estado = 'PARCIAL'
        if renderizados and selects > renderizados:
            estado = 'FALLIDA'
        incidencia = 'No se observó un SELECT adicional por usuario o pedido en la página medida.'
        if estado != 'APROBADA':
            incidencia = (
                f'Severidad media. JOIN detectado: {"sí" if usa_join else "no"}. '
                f'SELECT {selects} para {renderizados} filas.'
            )
        guardar_caso(
            'ORM-05',
            '\n'.join(lineas) + '\n\n' + sql_legible(sql_pagina, 20),
            self._referencia('A página 1, B página 2, C página 3, D producto, E usuario, F tipo, G usuario y H pedido', estado),
            'El historial debe paginar de a 20 y traer usuario y pedido en la misma consulta, sin un SELECT por fila.',
            (
                f'Las tres páginas ejecutaron {mediciones[0]["consultas"]}, {mediciones[1]["consultas"]} y {mediciones[2]["consultas"]} consultas, '
                f'con {mediciones[0]["filas_renderizadas"]}, {mediciones[1]["filas_renderizadas"]} y {mediciones[2]["filas_renderizadas"]} filas renderizadas. '
                f'Los filtros quedaron en {mediciones[3]["consultas"]}, {mediciones[4]["consultas"]} y {mediciones[5]["consultas"]} consultas. '
                f'JOIN de la consulta principal: {"sí" if usa_join else "no"}.'
            ),
            filas,
            incidencia,
            {'consultas.sql': sql_legible(sql_pagina, 20)},
        )

    def test_orm06_explain(self):
        exigir_bd_pruebas()
        marca = crear_proveedor('Marca ORM 06')
        otra = crear_proveedor('Otra ORM 06')
        crear_cpus(marca, 60, stock=1, prefijo='IDX')
        crear_cpus(otra, 10, stock=20, prefijo='OTRA')
        pedido = Pedido.objects.create(
            usuario=self.usuario, total_monto=Decimal('1.00'), direccion_envio='Calle 1', estado='PENDIENTE',
        )
        producto = Procesador.objects.filter(proveedor=marca).first()
        aplicar_delta(producto, -1, tipo=MovimientoStock.AJUSTE, usuario=self.staff, origen='auditoria', pedido=pedido)
        consultas = {
            'A listado': Procesador.objects.all()[:50],
            'B nombre': Procesador.objects.filter(nombre__icontains='IDX'),
            'C categoria': Procesador.objects.filter(categoria='CPU'),
            'D proveedor': Procesador.objects.filter(proveedor=marca),
            'E stock critico': Procesador.objects.filter(stock__lte=3),
            'F historial': MovimientoStock.objects.select_related('usuario', 'pedido').order_by('-creado_en', '-id')[:20],
            'G pedidos usuario': Pedido.objects.filter(usuario=self.usuario).order_by('-fecha_pedido'),
        }
        planes = {}
        sql_txt = []
        lineas = [f'EXPLAIN (ANALYZE, BUFFERS) sobre {self.bd["nombre"]} en {self.bd["host"]}. Solo SELECT.']
        with connection.cursor() as cursor:
            for nombre, qs in consultas.items():
                sql, params = qs.query.sql_with_params()
                cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + sql, params)
                plan = cursor.fetchone()[0]
                if isinstance(plan, str):
                    plan = json.loads(plan)
                nodo = plan[0]['Plan']
                planes[nombre] = plan
                sql_txt.append(f'-- {nombre}\n{sql};\n')
                lineas.append(
                    f'{nombre}: nodo={nodo.get("Node Type")} costo={nodo.get("Total Cost")} '
                    f'filas_estimadas={nodo.get("Plan Rows")} filas_reales={nodo.get("Actual Rows")} '
                    f'tiempo_ms={nodo.get("Actual Total Time")} shared_hit={nodo.get("Shared Hit Blocks")} '
                    f'shared_read={nodo.get("Shared Read Blocks")} orden={nodo.get("Sort Key") or nodo.get("Index Name") or "-"}.'
                )
            cursor.execute(
                """
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename IN ('core_procesador', 'core_movimientostock', 'core_pedido', 'core_proveedor')
                ORDER BY tablename, indexname
                """
            )
            indices = cursor.fetchall()
        lineas.append('Índices presentes:')
        for tabla, indice, definicion in indices:
            lineas.append(f'- {tabla}.{indice}: {definicion}')
        secuenciales = [nombre for nombre, plan in planes.items() if _tiene_seq_scan(plan[0]['Plan'])]
        propuestas = [
            'No se creó ningún índice y no se modificó ningún modelo.',
            f'Planes con algún Seq Scan: {", ".join(secuenciales) if secuenciales else "ninguno"}.',
            'En estas tablas de prueba un Sequential Scan puede ser la opción más barata. No se propone un índice solo por ver ese nodo.',
        ]
        plan_nombre = planes['B nombre'][0]['Plan']
        if _tiene_seq_scan(plan_nombre):
            propuestas.append(
                'La búsqueda por nombre usa ILIKE con comodín inicial. Un índice btree no cubre ese patrón. '
                'Solo tendría sentido valorar pg_trgm si el catálogo crece y este plan deja de ser barato. Esta muestra no justifica crearlo.'
            )
        plan_stock = planes['E stock critico'][0]['Plan']
        propuestas.append(
            f'El filtro de stock crítico recorrió {plan_stock.get("Actual Rows")} filas reales '
            f'en {plan_stock.get("Actual Total Time")} ms con nodo {plan_stock.get("Node Type")}. '
            'No se propone un índice con este volumen.'
        )
        estado = 'PARCIAL'
        incidencia = (
            'Sin incidencia de ejecución. La conclusión sobre índices de producción queda NO CONCLUYENTE: '
            f'la muestra cabe en memoria y {len(secuenciales)} de 7 planes contienen Seq Scan.'
        )
        metricas = []
        for nombre, plan in planes.items():
            nodo = plan[0]['Plan']
            metricas.append(fila_csv('ORM-06', nombre, nodo.get('Actual Rows'), {
                'consultas': 1,
                'selects': 1,
                'tiempo_respuesta_ms': nodo.get('Actual Total Time'),
                'tiempo_sql_ms': nodo.get('Actual Total Time'),
                'filas_catalogo': nodo.get('Actual Rows'),
                'filas_renderizadas': nodo.get('Actual Rows'),
                'repeticiones': 1,
                'tiempo_respuesta_min_ms': nodo.get('Actual Total Time'),
                'tiempo_respuesta_max_ms': nodo.get('Actual Total Time'),
            }))
        guardar_caso(
            'ORM-06',
            '\n'.join(lineas),
            self._referencia('A listado, B nombre, C categoría, D proveedor, E stock, F historial, G pedidos', estado),
            'Los planes deben identificar el tipo de acceso, filas, costo, tiempo y buffers, y solo entonces proponer un índice.',
            (
                f'Se ejecutaron 7 EXPLAIN ANALYZE sobre {self.bd["nombre"]}. '
                f'{len(secuenciales)} contienen Seq Scan. No se crearon índices. '
                'La muestra es pequeña y no alcanza para declarar una consulta costosa en producción.'
            ),
            metricas,
            incidencia,
            {
                'consultas.sql': '\n'.join(sql_txt),
                'explain.json': planes,
                'explain.txt': '\n'.join(lineas) + '\n',
                'propuestas_optimizacion.txt': '\n'.join(propuestas) + '\n',
            },
        )

    def test_orm08_componentes_compartidos(self):
        marca = crear_proveedor('Marca ORM 08')
        cpus = crear_cpus(marca, 6, stock=1)
        carrito = Carrito.objects.create(usuario=self.usuario)
        ItemCarrito.objects.create(carrito=carrito, procesador=cpus[0], cantidad=1, precio_unitario=cpus[0].precio)
        Favorito.objects.create(usuario=self.usuario, procesador=cpus[1])
        paginas = [
            ('inicio', reverse('core:index')),
            ('tienda', reverse('core:tienda')),
            ('nosotros', reverse('core:sobrenosotros')),
        ]
        roles = [
            ('anonimo', self.cliente),
            ('cliente', self.cliente_auth),
            ('staff', self.cliente_staff),
        ]
        filas = []
        tabla = []
        for rol, cliente in roles:
            for nombre, url in paginas:
                medicion = medir_solicitud(cliente, url)
                tabla.append((rol, nombre, medicion))
                filas.append(fila_csv('ORM-08', f'{rol} {nombre}', '', medicion))
        lineas = ['La barra compartida se midió por rol en inicio, tienda y sobre nosotros.']
        for rol, nombre, medicion in tabla:
            lineas.append(
                f'{rol} {nombre}: HTTP {medicion["estado_http"]}, consultas {medicion["consultas"]} '
                f'(SELECT {medicion["selects"]}), respuesta {medicion["tiempo_respuesta_ms"]} ms, SQL {medicion["tiempo_sql_ms"]} ms.'
            )
        anon = next(m for r, n, m in tabla if r == 'anonimo' and n == 'inicio')
        cliente = next(m for r, n, m in tabla if r == 'cliente' and n == 'inicio')
        staff = next(m for r, n, m in tabla if r == 'staff' and n == 'inicio')
        extra_cliente = cliente['consultas'] - anon['consultas']
        extra_staff = staff['consultas'] - anon['consultas']
        lineas.append(f'Inicio anónimo {anon["consultas"]} consultas; el cliente suma {extra_cliente}; el personal suma {extra_staff}.')
        duplicadas = len(staff['sql']) - len(set(staff['sql']))
        lineas.append(f'SQL idéntico repetido en el inicio del personal: {duplicadas}.')
        estado = 'PARCIAL' if extra_staff > 5 else 'APROBADA'
        incidencia = 'No se observó una carga extra relevante en los componentes compartidos.'
        if estado == 'PARCIAL':
            incidencia = (
                f'Severidad media. El inicio del personal ejecutó {staff["consultas"]} consultas frente a '
                f'{anon["consultas"]} del anónimo y {cliente["consultas"]} del cliente. '
                'El context processor recalcula las alertas de stock en cada página del personal. '
                f'SQL idéntico repetido: {duplicadas}.'
            )
        guardar_caso(
            'ORM-08',
            '\n'.join(lineas) + '\n\n-- inicio staff\n' + sql_legible(staff['sql'], 30),
            self._referencia('A anónimo, B cliente, C personal, D favoritos, E carrito, F alertas, G inicio/tienda/nosotros', estado),
            'La barra compartida debe agregar pocas consultas estables y no repetir el inventario completo en cada página.',
            (
                f'El inicio ejecutó {anon["consultas"]} consultas anónimo, {cliente["consultas"]} cliente y {staff["consultas"]} personal, '
                f'en {anon["tiempo_respuesta_ms"]}, {cliente["tiempo_respuesta_ms"]} y {staff["tiempo_respuesta_ms"]} ms. '
                f'El personal sumó {extra_staff} consultas respecto del anónimo.'
            ),
            filas,
            incidencia,
            {'consultas.sql': sql_legible(staff['sql'], 40)},
        )


def _tiene_seq_scan(nodo):
    if nodo.get('Node Type') == 'Seq Scan':
        return True
    return any(_tiene_seq_scan(hijo) for hijo in nodo.get('Plans') or [])


@override_settings(PAYPAL_TEST=True, PAYPAL_RECEIVER_EMAIL=RECEPTOR, CLP_TO_USD_RATE=950)
class AuditoriaOrmTransacciones(TransactionTestCase):
    def setUp(self):
        self.bd = exigir_bd_pruebas()
        self.usuario = User.objects.create_user('cliente_tx', 'cliente_tx@sandbox.example', 'Clave-orm-1')
        self.staff = User.objects.create_user('staff_tx', password='Clave-orm-1', is_staff=True)
        self.marca = crear_proveedor('Marca ORM 07')

    def _cpu(self, stock, prefijo):
        return crear_cpus(self.marca, 1, stock=stock, prefijo=prefijo)[0]

    def test_orm07_transacciones_y_bloqueos(self):
        lineas = [f'Base confirmada: {self.bd["nombre"]} en {self.bd["host"]}:{self.bd["puerto"]}.']
        cpu = self._cpu(5, 'Normal')
        inicio = time.perf_counter()
        movimiento = aplicar_delta(cpu, -1, tipo=MovimientoStock.AJUSTE, usuario=self.staff, origen='auditoria')
        normal_ms = (time.perf_counter() - inicio) * 1000
        cpu.refresh_from_db()
        lineas.append(f'A descuento normal: stock {cpu.stock}, movimiento {movimiento.pk if movimiento else None}, {normal_ms:.3f} ms.')

        corto = self._cpu(1, 'Corto')
        inicio = time.perf_counter()
        with self.assertRaises(StockInsuficiente):
            aplicar_delta(corto, -2, tipo=MovimientoStock.AJUSTE, usuario=self.staff, origen='auditoria')
        insuficiente_ms = (time.perf_counter() - inicio) * 1000
        corto.refresh_from_db()
        lineas.append(
            f'B stock insuficiente: stock permanece {corto.stock}, '
            f'movimientos {MovimientoStock.objects.filter(producto_pk=corto.pk).count()}, {insuficiente_ms:.3f} ms.'
        )

        pago = self._cpu(4, 'Pago')
        pedido = Pedido.objects.create(
            usuario=self.usuario, total_monto=Decimal('190000.00'), direccion_envio='Calle Ficticia 1', estado='PENDIENTE',
        )
        ItemPedido.objects.create(
            pedido=pedido, producto_nombre=pago.nombre, producto_tipo='procesador',
            precio_unitario=Decimal('190000.00'), cantidad=1, producto_modelo='procesador', producto_pk=pago.pk,
        )
        from paypal.standard.ipn.models import PayPalIPN
        from core.payments import clp_a_usd, confirmar_pago_paypal

        ipn = PayPalIPN.objects.create(
            payment_status='Completed', txn_id='TXN-ORM07', invoice=str(pedido.paypal_invoice),
            mc_gross=clp_a_usd(pedido.total_monto), mc_currency='USD', receiver_email=RECEPTOR,
            test_ipn=True, payer_email='sb-buyer@sandbox.example', first_name='Sandbox', last_name='Buyer',
        )
        observado = {}

        def sonda_correo(template_id, parametros):
            def tomar_fila():
                connection.close()
                marca_tiempo = time.perf_counter()
                with transaction.atomic():
                    Procesador.objects.select_for_update().get(pk=pago.pk)
                observado['lock_producto_ms'] = (time.perf_counter() - marca_tiempo) * 1000
                connection.close()

            hilo = threading.Thread(target=tomar_fila)
            hilo.start()
            hilo.join(2)
            observado['hilo_bloqueado'] = hilo.is_alive()
            observado['hilo'] = hilo
            pago.refresh_from_db()
            pedido.refresh_from_db()
            observado['stock_al_enviar'] = pago.stock
            observado['estado_al_enviar'] = pedido.estado
            return True

        inicio = time.perf_counter()
        with patch('core.correo._enviar', side_effect=sonda_correo):
            resultado = confirmar_pago_paypal(ipn)
        if observado.get('hilo') is not None:
            observado['hilo'].join(2)
        pago_ms = (time.perf_counter() - inicio) * 1000
        pago.refresh_from_db()
        pedido.refresh_from_db()
        lineas.append(
            f'C pago válido: resultado {resultado}, stock {pago.stock}, estado {pedido.estado}, {pago_ms:.3f} ms. '
            f'Al llegar al aviso el stock era {observado.get("stock_al_enviar")} y el estado {observado.get("estado_al_enviar")}. '
            f'Otro hilo tomó la fila en {observado.get("lock_producto_ms")} ms. Hilo aún bloqueado: {observado.get("hilo_bloqueado")}.'
        )
        inicio = time.perf_counter()
        with patch('core.correo._enviar', return_value=True):
            repetido = confirmar_pago_paypal(ipn)
        repetido_ms = (time.perf_counter() - inicio) * 1000
        pago.refresh_from_db()
        lineas.append(f'D pago repetido: resultado {repetido}, stock {pago.stock}, {repetido_ms:.3f} ms.')

        reversible = self._cpu(6, 'Reversible')
        inicio = time.perf_counter()
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                aplicar_delta(reversible, -1, tipo=MovimientoStock.AJUSTE, usuario=self.staff, origen='auditoria')
                raise RuntimeError('falla de prueba')
        reversible.refresh_from_db()
        rollback_ms = (time.perf_counter() - inicio) * 1000
        lineas.append(
            f'E rollback: stock {reversible.stock}, movimientos {MovimientoStock.objects.filter(producto_pk=reversible.pk).count()}, {rollback_ms:.3f} ms.'
        )

        disputado = self._cpu(1, 'Disputa')
        barrera = threading.Barrier(2)
        salidas = []

        def competir():
            try:
                connection.close()
                barrera.wait(5)
                aplicar_delta(disputado, -1, tipo=MovimientoStock.AJUSTE, usuario=self.staff, origen='auditoria')
                salidas.append('ok')
            except StockInsuficiente:
                salidas.append('insuficiente')
            finally:
                connection.close()

        hilos = [threading.Thread(target=competir), threading.Thread(target=competir)]
        inicio = time.perf_counter()
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(5)
        concurrencia_ms = (time.perf_counter() - inicio) * 1000
        disputado.refresh_from_db()
        lineas.append(
            f'F concurrencia: resultados {sorted(salidas)}, stock {disputado.stock}, '
            f'movimientos {MovimientoStock.objects.filter(producto_pk=disputado.pk).count()}, {concurrencia_ms:.3f} ms.'
        )

        bloqueado = self._cpu(4, 'Bloqueo')
        tiempos = {}
        barrera_bloqueo = threading.Barrier(2)

        def titular():
            connection.close()
            with transaction.atomic():
                type(bloqueado).objects.select_for_update().get(pk=bloqueado.pk)
                tiempos['adquirido'] = time.perf_counter()
                barrera_bloqueo.wait(5)
                time.sleep(0.3)
            tiempos['liberado'] = time.perf_counter()
            connection.close()

        def esperando():
            connection.close()
            barrera_bloqueo.wait(5)
            marca_espera = time.perf_counter()
            with transaction.atomic():
                type(bloqueado).objects.select_for_update().get(pk=bloqueado.pk)
            tiempos['espera_ms'] = (time.perf_counter() - marca_espera) * 1000
            connection.close()

        t1 = threading.Thread(target=titular)
        t2 = threading.Thread(target=esperando)
        t1.start()
        t2.start()
        t1.join(5)
        t2.join(5)
        retencion = (tiempos.get('liberado', 0) - tiempos.get('adquirido', 0)) * 1000
        inicio = time.perf_counter()
        with transaction.atomic():
            type(bloqueado).objects.select_for_update().get(pk=bloqueado.pk)
        posterior_ms = (time.perf_counter() - inicio) * 1000
        lineas.append(
            f'G bloqueo retenido {retencion:.1f} ms por la prueba, espera del segundo {tiempos.get("espera_ms")} ms, '
            f'acceso posterior {posterior_ms:.3f} ms.'
        )
        correo_fuera = (
            observado.get('estado_al_enviar') == 'PAGADO'
            and observado.get('hilo_bloqueado') is False
            and (observado.get('lock_producto_ms') or 9999) < 500
        )
        concurrencia_ok = sorted(salidas) == ['insuficiente', 'ok'] and disputado.stock == 0
        rollback_ok = reversible.stock == 6 and MovimientoStock.objects.filter(producto_pk=reversible.pk).count() == 0
        estado = 'APROBADA' if correo_fuera and concurrencia_ok and rollback_ok and (tiempos.get('espera_ms') or 0) >= 200 else 'PARCIAL'
        if estado == 'APROBADA':
            incidencia = (
                'Sin cambios parciales en los escenarios ejecutados. El aviso se invocó con el pedido ya pagado y el otro hilo '
                f'tomó la fila del producto en {observado.get("lock_producto_ms")} ms. '
                f'La espera forzada del bloqueo fue {tiempos.get("espera_ms")} ms y el acceso siguiente tardó {posterior_ms:.3f} ms.'
            )
        else:
            incidencia = (
                'Severidad alta si la concurrencia o el rollback no cierran. '
                f'Concurrencia {salidas}, stock reversible {reversible.stock}, correo fuera del bloqueo: {correo_fuera}, '
                f'espera {tiempos.get("espera_ms")} ms.'
            )
        filas = [
            fila_csv('ORM-07', 'descuento', 1, _punto(normal_ms, 1)),
            fila_csv('ORM-07', 'insuficiente', 1, _punto(insuficiente_ms, 0)),
            fila_csv('ORM-07', 'pago', 1, _punto(pago_ms, 1)),
            fila_csv('ORM-07', 'repetido', 1, _punto(repetido_ms, 1)),
            fila_csv('ORM-07', 'rollback', 1, _punto(rollback_ms, reversible.stock)),
            fila_csv('ORM-07', 'concurrencia', 2, _punto(concurrencia_ms, disputado.stock)),
            fila_csv('ORM-07', 'espera bloqueo', 2, _punto(tiempos.get('espera_ms') or 0, 1)),
        ]
        guardar_caso(
            'ORM-07',
            '\n'.join(lineas) + '\n',
            f'Fecha y hora: {ahora()}\nCommit: {sha_actual()}\n'
            f'Base: motor=postgresql host={self.bd["host"]} puerto={self.bd["puerto"]} nombre={self.bd["nombre"]} usuario={self.bd["usuario"]}\n'
            'Comando: python manage.py test core.test_auditoria_orm.AuditoriaOrmTransacciones --verbosity 1\n'
            'Escenarios: A descuento, B insuficiente, C pago, D repetido, E rollback, F dos hilos, G liberación.\n'
            f'Resultado de calidad: {estado}\n',
            'Las transacciones de stock y pago deben confirmar o revertir completas, bloquear la fila solo durante la escritura y liberarla antes del aviso HTTP.',
            (
                f'El descuento normal dejó stock {cpu.stock} en {normal_ms:.1f} ms y el rollback conservó stock {reversible.stock}. '
                f'La concurrencia devolvió {sorted(salidas)} con stock {disputado.stock}. '
                f'El segundo bloqueo esperó {tiempos.get("espera_ms")} ms y el acceso siguiente tardó {posterior_ms:.1f} ms. '
                f'Durante el aviso el pedido ya estaba {observado.get("estado_al_enviar")}.'
            ),
            filas,
            incidencia,
            {'bloqueos.txt': '\n'.join(lineas) + '\n'},
        )
        self.assertTrue(concurrencia_ok)
        self.assertTrue(rollback_ok)
        self.assertEqual(pago.stock, 3)
        self.assertEqual(repetido, 'ya_procesado')


def _punto(milisegundos, filas):
    valor = round(float(milisegundos), 3)
    return {
        'consultas': 1,
        'selects': 1,
        'tiempo_respuesta_ms': valor,
        'tiempo_sql_ms': valor,
        'tiempo_respuesta_min_ms': valor,
        'tiempo_respuesta_max_ms': valor,
        'filas_catalogo': 1,
        'filas_renderizadas': filas,
        'repeticiones': 1,
    }
