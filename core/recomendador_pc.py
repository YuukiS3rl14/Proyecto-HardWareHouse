"""Motor de armado por presupuesto y uso.

No llama a servicios externos ni estima FPS. Cada candidato se acepta o se
descarta con ``validar_armado()``. Una configuración solo se recomienda si
esas reglas quedan en estado compatible. El almacenamiento se comprueba
solo cuando la placa tiene ranuras y puertos y el disco tiene interfaz.
Si falta ese dato, no se marca compatible ni se bloquea el armado.

Búsqueda
--------
No se prueba el producto cartesiano del catálogo. Se avanza por etapas
(CPU, placa, RAM, GPU, gabinete, fuente, almacenamiento opcional y
cooler opcional) y se conserva un haz de cinco. En cada etapa queda
como máximo una parcial por procesador y por cifra de VRAM, y se reservan
cupos para otra CPU, para otra VRAM y para la parcial más barata. El disco se elige
antes del cooler, pero en gaming y edición se reserva antes el precio del
cooler de aire compatible más barato, para que el SSD no se quede con esos
pesos. El cooler no suma puntaje. En cada etapa se descartan las
combinaciones incompatibles, con datos insuficientes o más caras que el
presupuesto.

Puntaje
-------
Solo usa campos guardados en el inventario. No estima rendimiento: núcleos,
frecuencia, VRAM y capacidad entran con crecimiento decreciente y cada
categoría queda en una escala parecida, para que el peso del uso sí decida.

- procesador: promedio del indicador de núcleos y el de frecuencia base
- memoria: capacidad_gb × cantidad, hasta el objetivo de ``OBJETIVO_RAM_GB``.
  Pasado ese objetivo el indicador no sube. No es un límite de la placa
- tarjeta gráfica: VRAM en GB. En 1440p o 4K ese indicador pesa un poco más
- almacenamiento: capacidad_gb × cantidad. El tipo sale del modelo: SSD o HDD.
  Si hay un SSD con stock y dentro del presupuesto, es el disco principal.
  Un HDD entra cuando ningún SSD cabe o ninguno pasa las reglas.
  Si la placa no tiene conteos de ranuras y puertos, el disco no se da por verificado
- uso general: el mismo indicador se combina con lo que aporta por peso
  gastado, para no pagar más si el dato de catálogo no mejora
- empate: si el indicador de catálogo no cambia, se queda la opción más barata.
  Entre placas o gabinetes del mismo puntaje se prefiere la que trae los
  conteos que las reglas ya saben usar, para no dejar la comprobación pendiente

La fuente no suma puntaje. Sus watts solo aprueban o rechazan la regla de
potencia. Placa, gabinete y cooler tampoco suman: solo cumplen las reglas.
Un requisito obligatorio se aplica dentro de la búsqueda y no se relaja.
Una preferencia opcional se intenta primero; si no cabe, la respuesta lo dice.
Si dos tarjetas tienen la misma VRAM, el haz se queda con la que trae
consumo y largo: la otra no podría aprobar la potencia. Los pesos están
en ``PESOS_POR_USO``. Los objetivos de RAM están en ``OBJETIVO_RAM_GB``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from django.conf import settings

from core.compatibilidad import (
    ESTADO_COMPATIBLE,
    ESTADO_DATOS_INSUFICIENTES,
    ESTADO_INCOMPATIBLE,
    ESTADO_NO_EVALUADA,
    textos_almacenamiento_no_verificado,
    MENSAJE_POTENCIA_INTEGRADA,
    LineaRam,
    evaluaciones_de_seleccion,
    validar_armado,
    video_integrado_confirmado,
)
from core.piezas_demo import sin_demo
from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    RefrigeracionCooler,
    TarjetaGrafica,
)

USOS = ('gaming', 'trabajo', 'edicion', 'general')
RESOLUCIONES = ('', '1080p', '1440p', '4k')
ANCHURA = 5
ANCHURA_RESCATE = 8
_ESTADOS_QUE_DESCARTAN = frozenset({ESTADO_INCOMPATIBLE, ESTADO_DATOS_INSUFICIENTES})

# Cada valor es el peso de un indicador entre 0 y 1, no de la cifra cruda.
PESOS_POR_USO = {
    'gaming': {
        'procesador': Decimal('0.22'),
        'memoria_ram': Decimal('0.16'),
        'tarjeta_grafica': Decimal('0.46'),
        'almacenamiento': Decimal('0.16'),
    },
    'trabajo': {
        'procesador': Decimal('0.40'),
        'memoria_ram': Decimal('0.28'),
        'tarjeta_grafica': Decimal('0.07'),
        'almacenamiento': Decimal('0.25'),
    },
    'edicion': {
        'procesador': Decimal('0.34'),
        'memoria_ram': Decimal('0.24'),
        'tarjeta_grafica': Decimal('0.30'),
        'almacenamiento': Decimal('0.12'),
    },
    'general': {
        'procesador': Decimal('0.24'),
        'memoria_ram': Decimal('0.22'),
        'tarjeta_grafica': Decimal('0.20'),
        'almacenamiento': Decimal('0.34'),
    },
}

# Punto en el que el indicador vale 0.5. No es una meta de rendimiento.
REFERENCIAS = {
    'nucleos': Decimal('8'),
    'frecuencia': Decimal('4'),
    'vram_gb': Decimal('8'),
    'disco_gb': Decimal('1000'),
}

# GB orientativos por uso. Al llegar aquí el indicador de RAM vale 1 y
# más capacidad no lo sube. No son requisitos de un programa ni límites
# de compatibilidad: la placa y el stock se siguen validando aparte.
OBJETIVO_RAM_GB = {
    'gaming': Decimal('32'),
    'trabajo': Decimal('32'),
    'edicion': Decimal('64'),
    'general': Decimal('32'),
}

MENSAJE_REFRIGERACION_NO_VERIFICADA = 'Refrigeración no verificada'

AJUSTE_VRAM_POR_RESOLUCION = {
    '': Decimal('1'),
    '1080p': Decimal('1'),
    '1440p': Decimal('1.15'),
    '4k': Decimal('1.25'),
}

ETIQUETAS = {
    'procesador': 'Procesador (CPU)',
    'placa_madre': 'Placa Madre',
    'memoria_ram': 'Memoria RAM',
    'refrigeracion': 'Refrigeración CPU',
    'tarjeta_grafica': 'Tarjeta Gráfica (GPU)',
    'gabinete': 'Gabinete',
    'fuente_de_poder': 'Fuente de Poder',
    'almacenamiento': 'Almacenamiento',
}

_CLAVE_SELECCION = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'refrigeracion': 'refrigeracion',
    'tarjeta_grafica': 'tarjeta_grafica',
    'gabinete': 'gabinete',
    'fuente_de_poder': 'fuente_de_poder',
}

_TIPO_API = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'refrigeracion': 'refrigeracion',
    'tarjeta_grafica': 'tarjeta_grafica',
    'gabinete': 'gabinete',
    'fuente_de_poder': 'fuente_de_poder',
}

_OBLIGATORIAS = (
    'procesador',
    'placa_madre',
    'memoria_ram',
    'tarjeta_grafica',
    'gabinete',
    'fuente_de_poder',
)


class EntradaInvalida(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


@dataclass
class Parcial:
    seleccion: dict
    memorias: list
    discos: list
    puntaje: Decimal = Decimal('0')

    def firma(self):
        piezas = []
        for clave in sorted(self.seleccion):
            piezas.append((clave, self.seleccion[clave].pk, 1))
        for linea in self.memorias:
            piezas.append(('memoria_ram', linea.producto.pk, linea.cantidad))
        for disco in self.discos:
            piezas.append((disco['tipo'], disco['producto'].pk, disco['cantidad']))
        return tuple(piezas)


_MODOS_PREFERENCIA = ('preferencia', 'obligatorio')
_RAM_GB_VALIDOS = (8, 16, 32, 64)
_DISCO_GB_VALIDOS = (500, 1000, 2000)
_SOCKETS_PLATAFORMA = ('AM4', 'AM5', 'LGA1200', 'LGA1700')
_TIPOS_DISCO = ('ssd', 'hdd')
_MENSAJES_SIN_GPU_USO = {
    'gaming': (
        'Para un PC Gaming se requiere una tarjeta gráfica dedicada. '
        'No es posible generar una configuración sin ella.'
    ),
    'edicion': (
        'Para un PC de Edición se requiere una tarjeta gráfica dedicada '
        'según las reglas actuales del recomendador. '
        'No es posible generar una configuración sin ella.'
    ),
}
_MENSAJE_SIN_VIDEO = (
    'No se encontró una combinación de procesador y placa madre con gráficos integrados '
    'y salida de video confirmados. No es posible generar una configuración sin tarjeta '
    'gráfica dedicada con los componentes disponibles.'
)


@dataclass(frozen=True)
class Preferencias:
    """Pedido del formulario. Vacío conserva el comportamiento anterior."""

    ram_gb: int | None = None
    ram_modo: str = 'preferencia'
    disco_tipo: str | None = None
    disco_tipo_modo: str = 'preferencia'
    disco_gb: int | None = None
    disco_gb_modo: str = 'preferencia'
    socket: str | None = None
    socket_modo: str = 'preferencia'
    gpu: str = 'automatica'
    gpu_modo: str = 'preferencia'

    def exigir(self, nombre, exigir_opcionales):
        if nombre == 'ram' and self.ram_gb:
            return self.ram_modo == 'obligatorio' or bool(exigir_opcionales)
        if nombre == 'disco_tipo' and self.disco_tipo:
            return self.disco_tipo_modo == 'obligatorio' or bool(exigir_opcionales)
        if nombre == 'disco_gb' and self.disco_gb:
            return self.disco_gb_modo == 'obligatorio' or bool(exigir_opcionales)
        if nombre == 'socket' and self.socket:
            return self.socket_modo == 'obligatorio' or bool(exigir_opcionales)
        if nombre == 'sin_gpu' and self.gpu == 'sin_dedicada':
            return self.gpu_modo == 'obligatorio' or bool(exigir_opcionales)
        return False

    def tiene_obligatorios(self):
        return any((
            self.ram_gb and self.ram_modo == 'obligatorio',
            self.disco_tipo and self.disco_tipo_modo == 'obligatorio',
            self.disco_gb and self.disco_gb_modo == 'obligatorio',
            self.socket and self.socket_modo == 'obligatorio',
            self.gpu == 'sin_dedicada' and self.gpu_modo == 'obligatorio',
        ))

    def tiene_opcionales(self):
        return any((
            self.ram_gb and self.ram_modo != 'obligatorio',
            self.disco_tipo and self.disco_tipo_modo != 'obligatorio',
            self.disco_gb and self.disco_gb_modo != 'obligatorio',
            self.socket and self.socket_modo != 'obligatorio',
            self.gpu == 'sin_dedicada' and self.gpu_modo != 'obligatorio',
        ))

    def rechazo_de_uso(self, uso):
        if self.gpu == 'sin_dedicada' and uso in _MENSAJES_SIN_GPU_USO:
            return _MENSAJES_SIN_GPU_USO[uso]
        return None


def _tipo_disco_api(disco_tipo):
    if disco_tipo == 'ssd':
        return 'almacenamiento_ssd'
    if disco_tipo == 'hdd':
        return 'almacenamiento_hdd'
    return None


def _ram_alcanza(producto, minimo):
    if producto.capacidad_gb >= minimo and producto.stock >= 1:
        return True
    return producto.capacidad_gb * 2 >= minimo and producto.stock >= 2


@dataclass
class Informe:
    sin_stock: list = field(default_factory=list)
    sin_presupuesto: list = field(default_factory=list)
    descartes: list = field(default_factory=list)
    motivo: str = ''

    def anotar(self, textos):
        for texto in textos:
            limpio = str(texto or '').strip()
            if limpio and limpio not in self.descartes:
                self.descartes.append(limpio)

    def mensaje(self, etapa):
        if self.motivo:
            return self.motivo
        etiqueta = ETIQUETAS.get(etapa, etapa)
        if self.descartes:
            return ' '.join(
                ['No hay una combinación que pase las reglas de compatibilidad.']
                + self.descartes[:6]
            )
        if self.sin_presupuesto:
            return f'El presupuesto no alcanza para completar {etiqueta}.'
        if self.sin_stock:
            return f'No hay stock suficiente de {etiqueta}.'
        return (
            'No encontré una configuración verificable con el catálogo y el presupuesto indicados.'
        )


def interpretar_pedido(datos):
    """Valida el formulario. No consulta el catálogo."""
    if not isinstance(datos, dict):
        raise EntradaInvalida('La solicitud no es válida.')
    presupuesto = _entero_positivo(datos.get('presupuesto'), 'El presupuesto máximo')
    uso = datos.get('uso')
    if uso not in USOS:
        raise EntradaInvalida('El uso debe ser gaming, trabajo, edición o general.')
    resolucion = datos.get('resolucion') or ''
    if resolucion not in RESOLUCIONES:
        raise EntradaInvalida('La resolución debe ser 1080p, 1440p, 4K o quedar vacía.')
    modo = datos.get('modo')
    if modo not in ('desde_cero', 'completar'):
        raise EntradaInvalida('La modalidad debe ser desde cero o completar el armado.')
    return {
        'presupuesto_clp': presupuesto,
        'uso': uso,
        'resolucion': resolucion,
        'modo': modo,
        'preferencias': _leer_preferencias(datos),
    }


def _valor_catalogo(datos, clave, permitidos, etiqueta):
    if clave not in datos or datos.get(clave) in (None, ''):
        return None
    crudo = datos.get(clave)
    if isinstance(crudo, str) and crudo.isdigit():
        crudo = int(crudo)
    if crudo not in permitidos:
        raise EntradaInvalida(f'{etiqueta} no es una opción válida.')
    return crudo


def _modo_preferencia(datos, clave, activo):
    if not activo:
        return 'preferencia'
    modo = datos.get(clave) or 'preferencia'
    if modo not in _MODOS_PREFERENCIA:
        raise EntradaInvalida('Cada preferencia se aplica como obligatoria o como preferencia.')
    return modo


def _leer_preferencias(datos):
    ram = _valor_catalogo(datos, 'ram_gb', _RAM_GB_VALIDOS, 'La RAM mínima')
    disco_tipo = _valor_catalogo(datos, 'disco_tipo', _TIPOS_DISCO, 'El tipo de almacenamiento')
    disco_gb = _valor_catalogo(datos, 'disco_gb', _DISCO_GB_VALIDOS, 'La capacidad mínima')
    socket = _valor_catalogo(datos, 'socket', _SOCKETS_PLATAFORMA, 'La plataforma del procesador')
    gpu = datos.get('gpu') or 'automatica'
    if gpu not in ('automatica', 'sin_dedicada'):
        raise EntradaInvalida('La tarjeta gráfica debe ser automática o sin GPU dedicada.')
    return Preferencias(
        ram_gb=ram,
        ram_modo=_modo_preferencia(datos, 'ram_modo', ram is not None),
        disco_tipo=disco_tipo,
        disco_tipo_modo=_modo_preferencia(datos, 'disco_tipo_modo', disco_tipo is not None),
        disco_gb=disco_gb,
        disco_gb_modo=_modo_preferencia(datos, 'disco_gb_modo', disco_gb is not None),
        socket=socket,
        socket_modo=_modo_preferencia(datos, 'socket_modo', socket is not None),
        gpu=gpu,
        gpu_modo=_modo_preferencia(datos, 'gpu_modo', gpu == 'sin_dedicada'),
    )


def generar_recomendaciones(
    presupuesto_clp,
    uso,
    *,
    resolucion='',
    seleccion=None,
    memorias=None,
    almacenamientos=None,
    max_resultados=3,
    preferencias=None,
):
    """Devuelve hasta ``max_resultados`` armados, o el motivo por el que no hay ninguno."""
    if uso not in USOS:
        raise EntradaInvalida('El uso debe ser gaming, trabajo, edición o general.')
    if resolucion not in RESOLUCIONES:
        raise EntradaInvalida('La resolución debe ser 1080p, 1440p, 4K o quedar vacía.')
    if not isinstance(presupuesto_clp, int) or isinstance(presupuesto_clp, bool) or presupuesto_clp < 1:
        raise EntradaInvalida('El presupuesto máximo debe ser un entero positivo en CLP.')
    if isinstance(preferencias, dict):
        preferencias = _leer_preferencias(preferencias)
    prefs = preferencias or Preferencias()
    if not isinstance(prefs, Preferencias):
        raise EntradaInvalida('Las preferencias no son válidas.')
    rechazo = prefs.rechazo_de_uso(uso)
    if rechazo:
        return _sin_resultado(presupuesto_clp, uso, resolucion, rechazo, [])

    presupuesto = Decimal(presupuesto_clp)
    parcial = Parcial(
        seleccion=dict(seleccion or {}),
        memorias=list(memorias or []),
        discos=[dict(item) for item in (almacenamientos or [])],
    )
    fallo = _rechazo_inicial(parcial, presupuesto)
    if fallo:
        return _sin_resultado(presupuesto_clp, uso, resolucion, fallo, [])
    conflicto = _conflicto_obligatorio(parcial, prefs)
    if conflicto:
        return _sin_resultado(presupuesto_clp, uso, resolucion, conflicto, [])

    if prefs.tiene_opcionales() and not _opcionales_bloqueadas(parcial, prefs):
        hallado = _buscar(
            presupuesto_clp, uso, resolucion, parcial, max_resultados, prefs, True,
        )
        if _resultado_completo(hallado):
            return _solo_completas(hallado)
    hallado = _buscar(
        presupuesto_clp, uso, resolucion, parcial, max_resultados, prefs, False,
    )
    if not _resultado_completo(hallado) and prefs.tiene_obligatorios():
        # El haz corto puede quedarse con la RAM o la placa de mayor puntaje y
        # dejar fuera la única combinación que todavía paga la fuente.
        # Este paso sigue exigiendo los requisitos; no abre la plataforma.
        rescate = _buscar(
            presupuesto_clp, uso, resolucion, parcial, max_resultados, prefs, False,
            anchura=ANCHURA_RESCATE, distinguir_ram=True,
        )
        if _resultado_completo(rescate) or (
            rescate['status'] == 'success' and hallado['status'] != 'success'
        ):
            hallado = rescate
    if parcial.discos or _resultado_completo(hallado):
        return _solo_completas(hallado)
    # Desde cero, un armado sin disco no cierra la búsqueda: se reserva el
    # precio del disco más barato y se distinguen cantidades de RAM.
    con_disco = _buscar(
        presupuesto_clp, uso, resolucion, parcial, max_resultados, prefs, False,
        anchura=ANCHURA_RESCATE, distinguir_ram=True, reservar_disco=True,
    )
    if _resultado_completo(con_disco):
        return _solo_completas(con_disco)
    return _marcar_parciales(hallado)


def _resultado_completo(resultado):
    return (
        resultado.get('status') == 'success'
        and any(not item['configuracion_incompleta'] for item in resultado['recomendaciones'])
    )


def _solo_completas(resultado):
    if resultado.get('status') != 'success':
        return resultado
    completas = [
        item for item in resultado['recomendaciones']
        if not item['configuracion_incompleta']
    ]
    if not completas:
        return resultado
    resultado = dict(resultado)
    resultado['recomendaciones'] = completas
    resultado['sin_configuracion_completa'] = False
    return resultado


def _marcar_parciales(resultado):
    if not _resultado_completo(resultado) and resultado.get('status') == 'success':
        resultado = dict(resultado)
        resultado['sin_configuracion_completa'] = True
        resultado['mensaje'] = (
            'No se encontró un computador completo dentro del presupuesto y los requisitos seleccionados. '
            'Esta configuración no está lista para comprar.'
        )
    return resultado


def _precio_minimo_disco(catalogo):
    precios = [producto.precio for _tipo, producto in catalogo['almacenamiento'] if producto.stock >= 1]
    if not precios:
        return None
    return min(precios)


def _referencia_disco(parcial, catalogo, presupuesto):
    """Disco verificado más barato que completaría esta selección, si existe."""
    if parcial.discos:
        return None
    restante = presupuesto - _total(parcial)
    viables = []
    for tipo, producto in catalogo['almacenamiento']:
        if producto.stock < 1:
            continue
        opcion = {'tipo': tipo, 'producto': producto, 'cantidad': 1}
        nuevo = _aplicar(parcial, 'almacenamiento', opcion)
        resultado = validar_armado(
            **nuevo.seleccion,
            memorias_ram=nuevo.memorias or None,
            almacenamientos=nuevo.discos or None,
        )
        if resultado.estado in _ESTADOS_QUE_DESCARTAN:
            continue
        almacenamiento = resultado.almacenamiento
        if almacenamiento is None or almacenamiento.estado != ESTADO_COMPATIBLE:
            continue
        viables.append(producto)
    if not viables:
        return None
    barato = min(viables, key=lambda producto: (producto.precio, producto.pk))
    adicional = barato.precio - restante
    if adicional <= 0:
        return None
    return {
        'nombre': barato.nombre,
        'precio': int(barato.precio),
        'adicional': int(adicional),
    }


def _buscar(
    presupuesto_clp, uso, resolucion, parcial, max_resultados, prefs, exigir_opcionales,
    anchura=None, distinguir_ram=False, reservar_disco=False,
):
    presupuesto = Decimal(presupuesto_clp)
    catalogo = _catalogo_con_stock()
    presupuesto_base = presupuesto
    if reservar_disco and not parcial.discos:
        minimo = _precio_minimo_disco(catalogo)
        if minimo and minimo < presupuesto:
            presupuesto_base = presupuesto - minimo
    informe = Informe()
    haz = [parcial]
    for etapa in _OBLIGATORIAS:
        if etapa == 'tarjeta_grafica':
            haz = _ampliar_video(
                haz, catalogo, presupuesto_base, uso, resolucion, informe, prefs, exigir_opcionales,
                anchura, distinguir_ram,
            )
        else:
            haz = _ampliar(
                haz, etapa, True, catalogo, presupuesto_base, uso, resolucion, informe,
                prefs, exigir_opcionales, anchura, distinguir_ram,
            )
        if not haz:
            return _sin_resultado(presupuesto_clp, uso, resolucion, informe.mensaje(etapa), informe.descartes[:6])

    verificados = []
    pendientes = []
    for candidato in haz:
        resultado = validar_armado(
            **candidato.seleccion,
            memorias_ram=candidato.memorias or None,
            almacenamientos=candidato.discos or None,
        )
        if resultado.estado == ESTADO_COMPATIBLE:
            verificados.append(candidato)
        elif resultado.estado in _ESTADOS_QUE_DESCARTAN:
            informe.anotar(resultado.motivos_de_rechazo)
        else:
            pendientes.extend(
                hallazgo.mensaje
                for hallazgo in resultado.hallazgos
                if hallazgo.mensaje not in pendientes
            )
    if not verificados:
        detalle = informe.descartes[:6] or pendientes[:6]
        texto = informe.mensaje('fuente_de_poder')
        if pendientes and not informe.descartes and not informe.motivo:
            texto = (
                'Las combinaciones que caben en el presupuesto todavía tienen verificaciones pendientes. '
                + ' '.join(pendientes[:4])
            )
        return _sin_resultado(presupuesto_clp, uso, resolucion, texto, detalle)

    informe_discos = Informe()
    con_disco = _ampliar(
        verificados, 'almacenamiento', False, catalogo, presupuesto, uso, resolucion, informe_discos,
        prefs, exigir_opcionales, anchura, distinguir_ram,
    )
    if not (prefs.exigir('disco_tipo', exigir_opcionales) and prefs.disco_tipo == 'ssd'):
        con_disco = _completar_con_hdd(
            con_disco, catalogo, presupuesto, uso, resolucion, informe_discos, prefs, exigir_opcionales,
            anchura, distinguir_ram,
        )
    if prefs.exigir('disco_tipo', exigir_opcionales) or prefs.exigir('disco_gb', exigir_opcionales):
        con_disco = [
            candidato for candidato in con_disco
            if candidato.discos and _disco_cumple(candidato.discos[0], prefs, exigir_opcionales)
        ]
        if not con_disco:
            return _sin_resultado(
                presupuesto_clp, uso, resolucion, _mensaje_disco(prefs), informe_discos.descartes[:6],
            )
    con_disco = _ampliar(
        con_disco, 'refrigeracion', False, catalogo, presupuesto, uso, resolucion, informe,
        prefs, exigir_opcionales, anchura, distinguir_ram,
    )
    elegidos = _elegir_diversos(con_disco, max_resultados)
    if not elegidos:
        return _sin_resultado(
            presupuesto_clp, uso, resolucion,
            informe.motivo or 'No encontré una configuración verificable con el catálogo y el presupuesto indicados.',
            [],
        )
    elegidos = [
        (candidato, rol)
        for candidato, rol in elegidos
        if _parcial_cumple_obligatorios(candidato, prefs)
    ]
    if not elegidos:
        return _sin_resultado(
            presupuesto_clp, uso, resolucion,
            _mensaje_obligatorio(prefs),
            [],
        )

    return {
        'status': 'success',
        'uso': uso,
        'resolucion': resolucion or None,
        'presupuesto': presupuesto_clp,
        'criterios': criterios_de(uso, resolucion),
        'recomendaciones': [
            _serializar(
                candidato, presupuesto_clp, uso, resolucion, indice, rol, prefs,
                _referencia_disco(candidato, catalogo, presupuesto),
            )
            for indice, (candidato, rol) in enumerate(elegidos, start=1)
        ],
    }


def criterios_de(uso, resolucion):
    pesos = _pesos_efectivos(uso, resolucion)
    lineas = [
        'No se usan benchmarks, FPS ni equivalencias de rendimiento.',
        (
            'Cada dato técnico entra con crecimiento decreciente: el doble de núcleos, '
            'GHz, VRAM o capacidad no duplica el indicador y no se presenta como rendimiento.'
        ),
        (
            f'Procesador: promedio del indicador de núcleos y el de frecuencia base, '
            f'peso {pesos["procesador"]}. No se multiplican entre sí.'
        ),
        (
            f'Memoria RAM: capacidad del producto × cantidad, peso {pesos["memoria_ram"]}. '
            f'El indicador llega a 1 en {int(OBJETIVO_RAM_GB[uso])} GB para este uso y ahí se detiene. '
            'Ese objetivo no es un requisito de software ni un máximo de la placa. '
            'No se usa la velocidad en MHz: es la cifra del producto, no la del equipo armado.'
        ),
        (
            f'Tarjeta gráfica: VRAM en GB, peso {pesos["tarjeta_grafica"]}'
            f'{_texto_resolucion(resolucion)}. '
            'El tipo de memoria y la interfaz no se convierten en rendimiento.'
        ),
        (
            f'Almacenamiento: capacidad × cantidad, peso {pesos["almacenamiento"]}. '
            'SSD y HDD se distinguen por el modelo. Si hay un SSD con stock y dentro '
            'del presupuesto que no quede incompatible, se usa como disco principal. '
            'Un HDD queda como alternativa cuando ningún SSD cabe o ninguno pasa las reglas. '
            'Si la placa no registra ranuras y puertos, el disco no se da por verificado. '
            'No se agrega un segundo disco.'
        ),
        (
            'En trabajo y uso general se conserva también un armado sin GPU dedicada '
            'solo si el procesador tiene gráficos integrados confirmados y la placa '
            'tiene salidas de video confirmadas. Un campo vacío o en no no alcanza. '
            'Gaming y edición siguen exigiendo GPU dedicada. '
            'Fuente, placa, gabinete y cooler no suman puntaje. '
            'La fuente solo se acepta si cumple la regla de potencia, y esa regla '
            'exige procesador y GPU.'
        ),
        (
            'En gaming y edición se reserva el precio del cooler de aire compatible '
            'más barato para no dejar el equipo sin refrigeración dedicada. '
            'No se usa la potencia de referencia de la fuente como si fuera calor del procesador. '
            'Si falta la disipación, la altura o el dato de cooler de fábrica, '
            'la respuesta dice que la refrigeración no está verificada.'
        ),
    ]
    if uso == 'general':
        lineas.append(
            'En uso general, parte del puntaje mira cuánto indicador aporta cada peso gastado, '
            'para no elegir la pieza más cara cuando el dato de catálogo no mejora.'
        )
    else:
        lineas.append(
            'La búsqueda reserva una CPU distinta y, cuando ya hay GPU, otra VRAM de catálogo, '
            'para no quedarse solo con la parcial más cara ni solo con la más barata.'
        )
    return lineas


def _pesos_efectivos(uso, resolucion):
    pesos = dict(PESOS_POR_USO[uso])
    pesos['tarjeta_grafica'] *= AJUSTE_VRAM_POR_RESOLUCION.get(resolucion, Decimal('1'))
    return pesos


def _texto_resolucion(resolucion):
    factor = AJUSTE_VRAM_POR_RESOLUCION.get(resolucion, Decimal('1'))
    if not resolucion or factor == 1:
        return ''
    return (
        f'. Pesa un poco más ({factor}) porque la resolución pedida es {resolucion}; '
        'eso no calcula fluidez'
    )


def _entero_positivo(valor, etiqueta):
    if isinstance(valor, bool) or isinstance(valor, float):
        raise EntradaInvalida(f'{etiqueta} debe ser un entero positivo en CLP.')
    if isinstance(valor, str):
        if not valor.isdigit():
            raise EntradaInvalida(f'{etiqueta} debe ser un entero positivo en CLP.')
        valor = int(valor)
    if not isinstance(valor, int) or valor < 1:
        raise EntradaInvalida(f'{etiqueta} debe ser un entero positivo en CLP.')
    return valor


def _sin_resultado(presupuesto, uso, resolucion, mensaje, detalle):
    return {
        'status': 'sin_recomendacion',
        'uso': uso,
        'resolucion': resolucion or None,
        'presupuesto': presupuesto,
        'recomendaciones': [],
        'mensaje': mensaje,
        'detalle': detalle,
        'criterios': criterios_de(uso, resolucion) if uso in USOS and resolucion in RESOLUCIONES else [],
    }


def _rechazo_inicial(parcial, presupuesto):
    for producto, cantidad in _piezas_contadas(parcial):
        if producto.stock < cantidad:
            return (
                f'No hay stock suficiente de {producto.nombre}: '
                f'hay {producto.stock} y se piden {cantidad}.'
            )
    total = _total(parcial)
    if total > presupuesto:
        return (
            f'Los componentes ya seleccionados suman ${_pesos(total)} '
            f'y superan el presupuesto de ${_pesos(presupuesto)}.'
        )
    if not parcial.seleccion and not parcial.memorias and not parcial.discos:
        return None
    resultado = validar_armado(
        **parcial.seleccion,
        memorias_ram=parcial.memorias or None,
        almacenamientos=parcial.discos or None,
    )
    if resultado.estado in _ESTADOS_QUE_DESCARTAN:
        return ' '.join(resultado.motivos_de_rechazo) or 'La selección actual no se puede completar.'
    return None


def _en_stock(modelo):
    consulta = modelo.objects.select_related('proveedor').filter(stock__gt=0)
    if not settings.DEBUG:
        consulta = sin_demo(consulta)
    return list(consulta)


def _catalogo_con_stock():
    return {
        'procesador': _en_stock(Procesador),
        'placa_madre': _en_stock(PlacaMadre),
        'memoria_ram': _en_stock(MemoriaRam),
        'refrigeracion': _en_stock(RefrigeracionCooler),
        'tarjeta_grafica': _en_stock(TarjetaGrafica),
        'gabinete': _en_stock(Gabinete),
        'fuente_de_poder': _en_stock(FuenteDePoder),
        'almacenamiento': (
            [('almacenamiento_ssd', producto) for producto in _en_stock(AlmacenamientoSSD)]
            + [('almacenamiento_hdd', producto) for producto in _en_stock(AlmacenamientoHDD)]
        ),
    }


def _mensaje_obligatorio(prefs):
    partes = []
    if prefs.socket and prefs.socket_modo == 'obligatorio':
        partes.append(f'el socket {prefs.socket}')
    if prefs.ram_gb and prefs.ram_modo == 'obligatorio':
        partes.append(f'al menos {prefs.ram_gb} GB de RAM')
    if prefs.disco_tipo and prefs.disco_tipo_modo == 'obligatorio':
        partes.append('SSD' if prefs.disco_tipo == 'ssd' else 'HDD')
    if prefs.disco_gb and prefs.disco_gb_modo == 'obligatorio':
        partes.append(f'al menos {prefs.disco_gb} GB de almacenamiento')
    if prefs.gpu == 'sin_dedicada' and prefs.gpu_modo == 'obligatorio':
        partes.append('un armado sin GPU dedicada')
    if not partes:
        return 'No encontré una configuración verificable con el catálogo y el presupuesto indicados.'
    return (
        'Ninguna configuración cumple ' + ' y '.join(partes)
        + '. No se relajó ese requisito.'
    )


def _parcial_cumple_obligatorios(parcial, prefs):
    """Red de seguridad: un requisito obligatorio no puede salir en la respuesta."""
    cpu = parcial.seleccion.get('procesador')
    placa = parcial.seleccion.get('placa_madre')
    if prefs.socket and prefs.socket_modo == 'obligatorio':
        if cpu is None or cpu.socket != prefs.socket:
            return False
        if placa is None or placa.socket_cpu != prefs.socket:
            return False
    if prefs.ram_gb and prefs.ram_modo == 'obligatorio':
        if _ram_gb(parcial) < prefs.ram_gb:
            return False
        maximo = getattr(placa, 'capacidad_maxima_ram_gb', None) or 0 if placa is not None else 0
        if maximo < prefs.ram_gb:
            return False
    if parcial.discos and (
        (prefs.disco_tipo and prefs.disco_tipo_modo == 'obligatorio')
        or (prefs.disco_gb and prefs.disco_gb_modo == 'obligatorio')
    ):
        if not _disco_pedido_obligatorio(parcial.discos[0], prefs):
            return False
    elif (prefs.disco_tipo and prefs.disco_tipo_modo == 'obligatorio') or (
        prefs.disco_gb and prefs.disco_gb_modo == 'obligatorio'
    ):
        if not parcial.discos:
            return False
    if prefs.gpu == 'sin_dedicada' and prefs.gpu_modo == 'obligatorio':
        if parcial.seleccion.get('tarjeta_grafica') is not None:
            return False
        if not video_integrado_confirmado(cpu, placa):
            return False
    return True


def _producto_de_etapa_permitido(etapa, producto, prefs, exigir_opcionales):
    if etapa == 'procesador' and prefs.exigir('socket', exigir_opcionales):
        return producto.socket == prefs.socket
    if etapa == 'placa_madre':
        if prefs.exigir('socket', exigir_opcionales) and producto.socket_cpu != prefs.socket:
            return False
        if prefs.exigir('ram', exigir_opcionales):
            maximo = getattr(producto, 'capacidad_maxima_ram_gb', None) or 0
            if maximo < prefs.ram_gb:
                return False
    return True


def _disco_cumple(disco, prefs, exigir_opcionales):
    if prefs.exigir('disco_tipo', exigir_opcionales):
        if disco['tipo'] != _tipo_disco_api(prefs.disco_tipo):
            return False
    if prefs.exigir('disco_gb', exigir_opcionales):
        if disco['producto'].capacidad_gb < prefs.disco_gb:
            return False
    return True


def _disco_pedido_cumplido(disco, prefs):
    if prefs.disco_tipo and disco['tipo'] != _tipo_disco_api(prefs.disco_tipo):
        return False
    if prefs.disco_gb and disco['producto'].capacidad_gb < prefs.disco_gb:
        return False
    return True


def _etapa_ya_cumplida(parcial, etapa, prefs, exigir_opcionales):
    if etapa == 'procesador' and prefs.exigir('socket', exigir_opcionales):
        cpu = parcial.seleccion.get('procesador')
        return cpu is not None and cpu.socket == prefs.socket
    if etapa == 'placa_madre' and (
        prefs.exigir('socket', exigir_opcionales) or prefs.exigir('ram', exigir_opcionales)
    ):
        placa = parcial.seleccion.get('placa_madre')
        return placa is not None and _producto_de_etapa_permitido(
            'placa_madre', placa, prefs, exigir_opcionales,
        )
    if etapa == 'memoria_ram' and prefs.exigir('ram', exigir_opcionales):
        return _ram_gb(parcial) >= prefs.ram_gb
    if etapa == 'almacenamiento' and (
        prefs.exigir('disco_tipo', exigir_opcionales) or prefs.exigir('disco_gb', exigir_opcionales)
    ):
        return bool(parcial.discos) and all(
            _disco_cumple(disco, prefs, exigir_opcionales) for disco in parcial.discos
        )
    return True


def _motivo_opciones_vacias(etapa, catalogo, prefs, exigir_opcionales):
    if prefs.exigir('socket', exigir_opcionales) and etapa == 'procesador':
        hay = any(producto.socket == prefs.socket for producto in catalogo['procesador'])
        if not hay:
            return f'No hay un procesador con socket {prefs.socket} con stock.'
        return f'No hay un procesador con socket {prefs.socket} dentro del presupuesto.'
    if etapa == 'placa_madre' and (
        prefs.exigir('socket', exigir_opcionales) or prefs.exigir('ram', exigir_opcionales)
    ):
        if prefs.exigir('socket', exigir_opcionales):
            hay = any(producto.socket_cpu == prefs.socket for producto in catalogo['placa_madre'])
            if not hay:
                return f'No hay una placa madre con socket {prefs.socket} con stock.'
            return f'No hay una placa madre con socket {prefs.socket} dentro del presupuesto.'
        hay = any(
            (getattr(producto, 'capacidad_maxima_ram_gb', None) or 0) >= prefs.ram_gb
            for producto in catalogo['placa_madre']
        )
        if not hay:
            return f'No hay una placa madre que admita al menos {prefs.ram_gb} GB de RAM.'
        return (
            f'No hay una placa madre que admita al menos {prefs.ram_gb} GB de RAM '
            'dentro del presupuesto.'
        )
    if etapa == 'memoria_ram' and prefs.exigir('ram', exigir_opcionales):
        hay = any(_ram_alcanza(producto, prefs.ram_gb) for producto in catalogo['memoria_ram'])
        if not hay:
            return f'No hay memoria RAM de al menos {prefs.ram_gb} GB con stock.'
        return f'No hay memoria RAM de al menos {prefs.ram_gb} GB dentro del presupuesto.'
    if etapa == 'almacenamiento' and (
        prefs.exigir('disco_tipo', exigir_opcionales) or prefs.exigir('disco_gb', exigir_opcionales)
    ):
        return _mensaje_disco(prefs)
    return None


def _mensaje_disco(prefs):
    if prefs.disco_tipo == 'ssd' and prefs.disco_gb:
        return (
            f'No hay un SSD de al menos {prefs.disco_gb} GB con stock, dentro del presupuesto, '
            'que pase las reglas.'
        )
    if prefs.disco_tipo == 'ssd':
        return 'No hay un SSD con stock, dentro del presupuesto, que pase las reglas.'
    if prefs.disco_tipo == 'hdd' and prefs.disco_gb:
        return (
            f'No hay un HDD de al menos {prefs.disco_gb} GB con stock, dentro del presupuesto, '
            'que pase las reglas.'
        )
    if prefs.disco_tipo == 'hdd':
        return 'No hay un HDD con stock, dentro del presupuesto, que pase las reglas.'
    return (
        f'No hay un disco de al menos {prefs.disco_gb} GB con stock, dentro del presupuesto, '
        'que pase las reglas.'
    )


def _conflicto_obligatorio(parcial, prefs):
    mensajes = []
    cpu = parcial.seleccion.get('procesador')
    placa = parcial.seleccion.get('placa_madre')
    if prefs.ram_gb and prefs.ram_modo == 'obligatorio':
        if parcial.memorias and _ram_gb(parcial) < prefs.ram_gb:
            mensajes.append(
                f'La RAM ya elegida suma {_ram_gb(parcial)} GB y el requisito pide al menos '
                f'{prefs.ram_gb} GB. No se reemplazó la selección.'
            )
        maximo = getattr(placa, 'capacidad_maxima_ram_gb', None) if placa is not None else None
        if maximo and maximo < prefs.ram_gb:
            mensajes.append(
                f'La placa ya elegida admite hasta {maximo} GB de RAM y el requisito pide al menos '
                f'{prefs.ram_gb} GB. No se reemplazó la selección.'
            )
    if prefs.socket and prefs.socket_modo == 'obligatorio':
        if cpu is not None and cpu.socket != prefs.socket:
            mensajes.append(
                f'El procesador ya elegido usa socket {cpu.socket} y el requisito pide {prefs.socket}. '
                'No se reemplazó la selección.'
            )
        if placa is not None and placa.socket_cpu != prefs.socket:
            mensajes.append(
                f'La placa ya elegida usa socket {placa.socket_cpu} y el requisito pide {prefs.socket}. '
                'No se reemplazó la selección.'
            )
    if prefs.gpu == 'sin_dedicada' and prefs.gpu_modo == 'obligatorio':
        if parcial.seleccion.get('tarjeta_grafica') is not None:
            mensajes.append(
                'La selección ya incluye una GPU dedicada y el requisito pide armar sin ella. '
                'No se reemplazó la selección.'
            )
        elif cpu is not None and placa is not None and not video_integrado_confirmado(cpu, placa):
            mensajes.append(
                'El procesador y la placa ya elegidos no tienen confirmados los gráficos integrados '
                'y las salidas de video. No se puede omitir la GPU dedicada ni se reemplazó la selección.'
            )
    if parcial.discos and (
        (prefs.disco_tipo and prefs.disco_tipo_modo == 'obligatorio')
        or (prefs.disco_gb and prefs.disco_gb_modo == 'obligatorio')
    ):
        if not _disco_pedido_obligatorio(parcial.discos[0], prefs):
            mensajes.append(
                'El almacenamiento ya elegido no cumple el requisito de tipo o capacidad. '
                'No se reemplazó la selección.'
            )
    if not mensajes:
        return None
    return ' '.join(mensajes)


def _disco_pedido_obligatorio(disco, prefs):
    if prefs.disco_tipo and prefs.disco_tipo_modo == 'obligatorio':
        if disco['tipo'] != _tipo_disco_api(prefs.disco_tipo):
            return False
    if prefs.disco_gb and prefs.disco_gb_modo == 'obligatorio':
        if disco['producto'].capacidad_gb < prefs.disco_gb:
            return False
    return True


def _opcionales_bloqueadas(parcial, prefs):
    cpu = parcial.seleccion.get('procesador')
    placa = parcial.seleccion.get('placa_madre')
    if prefs.socket and prefs.socket_modo != 'obligatorio':
        if cpu is not None and cpu.socket != prefs.socket:
            return True
        if placa is not None and placa.socket_cpu != prefs.socket:
            return True
    if prefs.ram_gb and prefs.ram_modo != 'obligatorio' and parcial.memorias:
        if _ram_gb(parcial) < prefs.ram_gb:
            return True
    if prefs.gpu == 'sin_dedicada' and prefs.gpu_modo != 'obligatorio':
        if parcial.seleccion.get('tarjeta_grafica') is not None:
            return True
    if parcial.discos and (
        (prefs.disco_tipo and prefs.disco_tipo_modo != 'obligatorio')
        or (prefs.disco_gb and prefs.disco_gb_modo != 'obligatorio')
    ):
        if not _disco_pedido_cumplido(parcial.discos[0], prefs):
            return True
    return False


def _balance_preferencias(parcial, prefs):
    cumplidos = []
    pendientes = []
    if prefs.ram_gb:
        total = _ram_gb(parcial)
        if total >= prefs.ram_gb:
            cumplidos.append(f'{total} GB de RAM: cumple el mínimo solicitado.')
        elif prefs.ram_modo != 'obligatorio':
            pendientes.append(
                f'No se pudo cumplir la preferencia de {prefs.ram_gb} GB de RAM. '
                f'La configuración suma {total} GB.'
            )
    if prefs.disco_tipo or prefs.disco_gb:
        disco = parcial.discos[0] if parcial.discos else None
        tipo_ok = not prefs.disco_tipo or (
            disco is not None and disco['tipo'] == _tipo_disco_api(prefs.disco_tipo)
        )
        cap_ok = not prefs.disco_gb or (
            disco is not None and disco['producto'].capacidad_gb >= prefs.disco_gb
        )
        if disco is not None and tipo_ok and cap_ok:
            clase = 'SSD' if disco['tipo'] == 'almacenamiento_ssd' else 'HDD'
            if prefs.disco_gb:
                cumplidos.append(
                    f'{clase} de {disco["producto"].capacidad_gb} GB: cumple la capacidad solicitada.'
                )
            else:
                cumplidos.append(f'{clase}: cumple el tipo de almacenamiento solicitado.')
        else:
            pedido = []
            if prefs.disco_tipo and not tipo_ok and prefs.disco_tipo_modo != 'obligatorio':
                pedido.append('SSD' if prefs.disco_tipo == 'ssd' else 'HDD')
            if prefs.disco_gb and not cap_ok and prefs.disco_gb_modo != 'obligatorio':
                pedido.append(f'de al menos {prefs.disco_gb} GB')
            if pedido:
                pendientes.append(
                    'No se pudo cumplir la preferencia de almacenamiento ' + ' '.join(pedido) + '.'
                )
    if prefs.socket:
        cpu = parcial.seleccion.get('procesador')
        if cpu is not None and cpu.socket == prefs.socket:
            cumplidos.append(f'Socket {prefs.socket}: cumple la plataforma seleccionada.')
        elif prefs.socket_modo != 'obligatorio':
            actual = cpu.socket if cpu is not None else 'sin procesador'
            pendientes.append(
                f'No se pudo cumplir la preferencia de socket {prefs.socket}. '
                f'El procesador usa {actual}.'
            )
    if prefs.gpu == 'sin_dedicada':
        confirmado = (
            parcial.seleccion.get('tarjeta_grafica') is None
            and video_integrado_confirmado(
                parcial.seleccion.get('procesador'),
                parcial.seleccion.get('placa_madre'),
            )
        )
        if confirmado:
            cumplidos.append(
                'Sin GPU dedicada: el procesador y la placa tienen gráficos integrados '
                'y salidas de video confirmados.'
            )
        elif prefs.gpu_modo != 'obligatorio':
            pendientes.append(
                'No se pudo armar sin GPU dedicada. Se mantuvo una tarjeta gráfica '
                'porque no había evidencia confirmada de video integrado o no cupo en el presupuesto.'
            )
    return cumplidos, pendientes


def _ampliar(
    haz, etapa, obligatoria, catalogo, presupuesto, uso, resolucion, informe,
    preferencias=None, exigir_opcionales=False, anchura=None, distinguir_ram=False,
):
    prefs = preferencias or Preferencias()
    local = Informe()
    siguientes = []
    for parcial in haz:
        if _ya_tiene(parcial, etapa):
            if not _etapa_ya_cumplida(parcial, etapa, prefs, exigir_opcionales):
                local.motivo = _motivo_opciones_vacias(etapa, catalogo, prefs, exigir_opcionales) or (
                    'La selección ya hecha no cumple el requisito. No se reemplazó.'
                )
                continue
            parcial.puntaje = _puntaje(parcial, uso, resolucion)
            siguientes.append(parcial)
            continue
        opciones = _opciones(
            parcial, etapa, catalogo, presupuesto, uso, prefs, exigir_opcionales,
        )
        if not opciones:
            if not obligatoria:
                parcial.puntaje = _puntaje(parcial, uso, resolucion)
                siguientes.append(parcial)
            else:
                motivo = _motivo_opciones_vacias(etapa, catalogo, prefs, exigir_opcionales)
                if motivo:
                    local.motivo = motivo
                elif not catalogo.get(etapa):
                    if ETIQUETAS[etapa] not in local.sin_stock:
                        local.sin_stock.append(ETIQUETAS[etapa])
                elif ETIQUETAS[etapa] not in local.sin_presupuesto:
                    local.sin_presupuesto.append(ETIQUETAS[etapa])
            continue
        acepto_alguna = False
        for opcion in opciones:
            nuevo = _aplicar(parcial, etapa, opcion)
            if _total(nuevo) > presupuesto:
                if ETIQUETAS[etapa] not in local.sin_presupuesto:
                    local.sin_presupuesto.append(ETIQUETAS[etapa])
                continue
            resultado = validar_armado(
                **nuevo.seleccion,
                memorias_ram=nuevo.memorias or None,
                almacenamientos=nuevo.discos or None,
            )
            if resultado.estado in _ESTADOS_QUE_DESCARTAN:
                local.anotar(resultado.motivos_de_rechazo)
                continue
            nuevo.puntaje = _puntaje(nuevo, uso, resolucion)
            siguientes.append(nuevo)
            acepto_alguna = True
        if not acepto_alguna and not obligatoria:
            parcial.puntaje = _puntaje(parcial, uso, resolucion)
            siguientes.append(parcial)
    if obligatoria and not siguientes:
        informe.descartes = local.descartes
        informe.sin_stock = local.sin_stock
        informe.sin_presupuesto = local.sin_presupuesto
        informe.motivo = local.motivo
        return []
    return _quedan_en_el_haz(siguientes, etapa, uso, presupuesto, anchura, distinguir_ram)


def _gpu_obligatoria(parcial, uso):
    """Gaming y edición siempre. El resto, salvo video integrado confirmado."""
    if uso in ('gaming', 'edicion'):
        return True
    if 'tarjeta_grafica' in parcial.seleccion:
        return True
    return not video_integrado_confirmado(
        parcial.seleccion.get('procesador'),
        parcial.seleccion.get('placa_madre'),
    )


def _ampliar_video(
    haz, catalogo, presupuesto, uso, resolucion, informe, preferencias=None, exigir_opcionales=False,
    anchura=None, distinguir_ram=False,
):
    """En oficina y uso general guarda la rama con GPU y la rama sin GPU."""
    prefs = preferencias or Preferencias()
    if prefs.exigir('sin_gpu', exigir_opcionales):
        salida = []
        for parcial in haz:
            if parcial.seleccion.get('tarjeta_grafica') is not None:
                continue
            if not video_integrado_confirmado(
                parcial.seleccion.get('procesador'),
                parcial.seleccion.get('placa_madre'),
            ):
                continue
            copia = Parcial(
                dict(parcial.seleccion),
                list(parcial.memorias),
                [dict(disco) for disco in parcial.discos],
            )
            copia.puntaje = _puntaje(copia, uso, resolucion)
            salida.append(copia)
        if not salida:
            informe.motivo = _MENSAJE_SIN_VIDEO
            return []
        return _quedan_en_el_haz(salida, 'tarjeta_grafica', uso, presupuesto, anchura, distinguir_ram)
    exigir = []
    libres = []
    for parcial in haz:
        if _gpu_obligatoria(parcial, uso):
            exigir.append(parcial)
        else:
            libres.append(parcial)
    salida = []
    if exigir:
        con_gpu = _ampliar(
            exigir, 'tarjeta_grafica', True, catalogo, presupuesto, uso, resolucion, informe,
            prefs, exigir_opcionales, anchura, distinguir_ram,
        )
        if not con_gpu and not libres:
            return []
        salida.extend(con_gpu)
    if libres:
        con_gpu = _ampliar(
            libres, 'tarjeta_grafica', False, catalogo, presupuesto, uso, resolucion, informe,
            prefs, exigir_opcionales, anchura, distinguir_ram,
        )
        salida.extend(con_gpu)
        presentes = {parcial.firma() for parcial in con_gpu}
        for parcial in libres:
            if parcial.firma() in presentes:
                continue
            copia = Parcial(
                dict(parcial.seleccion),
                list(parcial.memorias),
                [dict(disco) for disco in parcial.discos],
            )
            copia.puntaje = _puntaje(copia, uso, resolucion)
            salida.append(copia)
    return _quedan_en_el_haz(salida, 'tarjeta_grafica', uso, presupuesto, anchura, distinguir_ram)


def _completar_con_hdd(
    haz, catalogo, presupuesto, uso, resolucion, informe, preferencias=None, exigir_opcionales=False,
    anchura=None, distinguir_ram=False,
):
    """Si el SSD no cupo o no pasó las reglas, prueba un HDD con stock."""
    sin_disco = [parcial for parcial in haz if not parcial.discos]
    if not sin_disco:
        return haz
    hdd = [item for item in catalogo['almacenamiento'] if item[0] == 'almacenamiento_hdd']
    if not hdd:
        return haz
    reducido = dict(catalogo)
    reducido['almacenamiento'] = hdd
    completados = _ampliar(
        sin_disco, 'almacenamiento', False, reducido, presupuesto, uso, resolucion, informe,
        preferencias, exigir_opcionales, anchura, distinguir_ram,
    )
    return [parcial for parcial in haz if parcial.discos] + completados


def _ya_tiene(parcial, etapa):
    if etapa == 'memoria_ram':
        return bool(parcial.memorias)
    if etapa == 'almacenamiento':
        return bool(parcial.discos)
    return _CLAVE_SELECCION[etapa] in parcial.seleccion


def _politica_cooler(parcial, uso):
    """dedicado reserva presupuesto; si_sobra solo usa lo que quede; omitir no agrega otro."""
    if 'refrigeracion' in parcial.seleccion:
        return 'fijo'
    cpu = parcial.seleccion.get('procesador')
    incluye = getattr(cpu, 'incluye_cooler', None) if cpu else None
    if uso in ('gaming', 'edicion'):
        return 'dedicado'
    if uso == 'trabajo':
        if incluye is False or getattr(cpu, 'potencia_termica_referencia_watts', None):
            return 'dedicado'
        if incluye is True:
            return 'incluido'
        return 'si_sobra'
    if incluye is False:
        return 'dedicado'
    if incluye is True:
        # El dato de fábrica confirma que trae cooler, pero no trae disipación ni altura.
        # Solo se agrega otro si ese otro sí se puede comprobar con las reglas actuales.
        return 'verificado'
    return 'omitir'


def _cooler_datos_insuficientes_para_capacidad(cooler, parcial):
    """True cuando los datos que sí existen muestran que no alcanza.

    Si la disipación o la altura no están guardadas, no se inventa el resultado
    y el cooler sigue siendo candidato. La respuesta lo marca como no verificado.
    """
    if getattr(cooler, 'tipo', None) == 'Líquida':
        return False
    cpu = parcial.seleccion.get('procesador')
    case = parcial.seleccion.get('gabinete')
    altura = getattr(cooler, 'altura_mm', None)
    maximo = getattr(case, 'altura_max_cooler_mm', None) if case is not None else None
    if altura and maximo and altura > maximo:
        return True
    disipacion = getattr(cooler, 'disipacion_referencia_watts', None)
    termica = getattr(cpu, 'potencia_termica_referencia_watts', None) if cpu is not None else None
    if disipacion and termica and disipacion < termica:
        return True
    return False


def _cooler_aceptado(parcial, cooler):
    if cooler.stock < 1 or _cooler_datos_insuficientes_para_capacidad(cooler, parcial):
        return False
    seleccion = dict(parcial.seleccion)
    seleccion['refrigeracion'] = cooler
    resultado = validar_armado(
        **seleccion,
        memorias_ram=parcial.memorias or None,
        almacenamientos=parcial.discos or None,
    )
    return resultado.estado not in _ESTADOS_QUE_DESCARTAN


def _cooler_queda_verificado(parcial, cooler):
    """True solo si las reglas actuales pueden afirmar altura y disipación."""
    if not _cooler_aceptado(parcial, cooler):
        return False
    seleccion = dict(parcial.seleccion)
    seleccion['refrigeracion'] = cooler
    return _refrigeracion_verificada(Parcial(seleccion, list(parcial.memorias), list(parcial.discos)))


def _reserva_para_cooler(parcial, catalogo, uso):
    if _politica_cooler(parcial, uso) != 'dedicado':
        return Decimal('0')
    precios = []
    for cooler in catalogo['refrigeracion']:
        if cooler.tipo != 'Aire':
            continue
        if Decimal(cooler.precio) < 0 or not _cooler_aceptado(parcial, cooler):
            continue
        precios.append(Decimal(cooler.precio))
    if not precios:
        return Decimal('0')
    return min(precios)


def _opciones(parcial, etapa, catalogo, presupuesto, uso, preferencias=None, exigir_opcionales=False):
    prefs = preferencias or Preferencias()
    restante = presupuesto - _total(parcial)
    if etapa == 'almacenamiento':
        restante -= _reserva_para_cooler(parcial, catalogo, uso)
    if restante < 0:
        restante = Decimal('0')
    if etapa == 'memoria_ram':
        opciones = []
        for producto in catalogo['memoria_ram']:
            if producto.precio <= restante and producto.stock >= 1:
                opciones.append([LineaRam(producto, 1)])
            if producto.precio * 2 <= restante and producto.stock >= 2:
                opciones.append([LineaRam(producto, 2)])
        if prefs.exigir('ram', exigir_opcionales):
            opciones = [
                lineas for lineas in opciones
                if sum(linea.producto.capacidad_gb * linea.cantidad for linea in lineas) >= prefs.ram_gb
            ]
        return opciones
    if etapa == 'almacenamiento':
        opciones = []
        for tipo, producto in catalogo['almacenamiento']:
            if producto.precio <= restante and producto.stock >= 1:
                opciones.append({'tipo': tipo, 'producto': producto, 'cantidad': 1})
        opciones = [
            opcion for opcion in opciones
            if _disco_cumple(opcion, prefs, exigir_opcionales)
        ]
        if prefs.exigir('disco_tipo', exigir_opcionales) and prefs.disco_tipo == 'hdd':
            return [opcion for opcion in opciones if opcion['tipo'] == 'almacenamiento_hdd']
        ssds = [opcion for opcion in opciones if opcion['tipo'] == 'almacenamiento_ssd']
        if ssds:
            return ssds
        return opciones
    if etapa == 'refrigeracion':
        politica = _politica_cooler(parcial, uso)
        if politica in ('fijo', 'incluido', 'omitir'):
            return []
        if politica == 'verificado':
            return [
                cooler
                for cooler in catalogo['refrigeracion']
                if cooler.tipo == 'Aire'
                and cooler.precio <= restante
                and _cooler_queda_verificado(parcial, cooler)
            ]
        opciones = [
            cooler
            for cooler in catalogo['refrigeracion']
            if cooler.precio <= restante and _cooler_aceptado(parcial, cooler)
        ]
        aire = [cooler for cooler in opciones if cooler.tipo == 'Aire']
        return aire or opciones
    clave = _CLAVE_SELECCION[etapa]
    productos = [
        producto
        for producto in catalogo[clave]
        if producto.precio <= restante and producto.stock >= 1
        and _producto_de_etapa_permitido(etapa, producto, prefs, exigir_opcionales)
    ]
    return productos


def _aplicar(parcial, etapa, opcion):
    nuevo = Parcial(
        seleccion=dict(parcial.seleccion),
        memorias=list(parcial.memorias),
        discos=[dict(disco) for disco in parcial.discos],
    )
    if etapa == 'memoria_ram':
        nuevo.memorias = list(opcion)
    elif etapa == 'almacenamiento':
        nuevo.discos = [opcion]
    else:
        nuevo.seleccion[_CLAVE_SELECCION[etapa]] = opcion
    return nuevo


def _piezas_contadas(parcial):
    for producto in parcial.seleccion.values():
        yield producto, 1
    for linea in parcial.memorias:
        yield linea.producto, linea.cantidad
    for disco in parcial.discos:
        yield disco['producto'], disco['cantidad']


def _total(parcial):
    total = Decimal('0')
    for producto, cantidad in _piezas_contadas(parcial):
        total += Decimal(producto.precio) * cantidad
    return total


def _gpu_de(parcial):
    gpu = parcial.seleccion.get('tarjeta_grafica')
    return getattr(gpu, 'pk', None)


def _cupo_ram(parcial, uso):
    """Separa placas que pueden llegar al objetivo de las que se quedan cortas.

    Antes de elegir la GPU solo se conserva una placa por procesador. Si esa
    placa tiene un máximo inferior al objetivo, la búsqueda ya no puede
    probar el kit que sí lo cubre.
    """
    if _gpu_de(parcial) is not None:
        return None
    placa = parcial.seleccion.get('placa_madre')
    if placa is None:
        return None
    maximo = getattr(placa, 'capacidad_maxima_ram_gb', None)
    if not maximo:
        return 'desconocido'
    if Decimal(maximo) >= OBJETIVO_RAM_GB[uso]:
        return 'alcanza'
    return 'no_alcanza'


def _clave_plataforma(parcial, uso):
    gpu = parcial.seleccion.get('tarjeta_grafica')
    # La VRAM, no el id: dos tarjetas con los mismos GB no ocupan dos cupos.
    # El desempate se queda con la que tiene watts y largo, porque la otra
    # no pasa la regla de potencia.
    grafica = None if gpu is None else gpu.vram_gb
    return (_cpu_de(parcial), grafica, _cupo_ram(parcial, uso))


def _completitud(parcial):
    """Cuenta datos que las reglas ya exigen para poder aprobar la parcial.

    No agrega reglas. Sirve para desempatar: si dos piezas tienen el mismo
    indicador, se conserva la que trae watts, largo o formato de RAM, porque
    la otra se va a descartar más adelante por datos insuficientes.
    """
    puntos = 0
    cpu = parcial.seleccion.get('procesador')
    if cpu is not None and getattr(cpu, 'potencia_referencia_watts', None):
        puntos += 1
    gpu = parcial.seleccion.get('tarjeta_grafica')
    if gpu is not None and getattr(gpu, 'consumo_referencia_watts', None):
        puntos += 1
    if gpu is not None and getattr(gpu, 'largo_mm', None):
        puntos += 1
    placa = parcial.seleccion.get('placa_madre')
    if placa is not None and getattr(placa, 'formato_ram_soportado', None):
        puntos += 1
    gabinete = parcial.seleccion.get('gabinete')
    if gabinete is not None and getattr(gabinete, 'largo_max_gpu_mm', None):
        puntos += 1
    if placa is not None and _conteos_de_placa_conocidos(placa):
        puntos += 1
    if gabinete is not None and getattr(gabinete, 'altura_max_cooler_mm', None):
        puntos += 1
    cooler = parcial.seleccion.get('refrigeracion')
    if cooler is not None and getattr(cooler, 'altura_mm', None) and getattr(cooler, 'disipacion_referencia_watts', None):
        puntos += 1
    return puntos


def _conteos_de_placa_conocidos(placa):
    """True cuando los cuatro conteos que ya usa la regla de discos están guardados.

    0 es un dato. Vacío no lo es. No decide si el disco cabe.
    """
    campos = (
        'ranuras_m2_solo_nvme',
        'ranuras_m2_solo_sata',
        'ranuras_m2_nvme_o_sata',
        'puertos_sata',
    )
    return all(getattr(placa, campo, None) is not None for campo in campos)


def _vram_de(parcial):
    gpu = parcial.seleccion.get('tarjeta_grafica')
    return getattr(gpu, 'vram_gb', None)


def _cpu_de(parcial):
    cpu = parcial.seleccion.get('procesador')
    return getattr(cpu, 'pk', None)


def _quedan_en_el_haz(siguientes, etapa, uso, presupuesto, anchura=None, distinguir_ram=False):
    del etapa, presupuesto
    limite = ANCHURA if anchura is None else anchura
    siguientes.sort(key=lambda item: (
        -item.puntaje,
        -_completitud(item),
        _total(item),
        item.firma(),
    ))
    unicos = []
    claves = set()
    for item in siguientes:
        clave = _clave_plataforma(item, uso)
        if distinguir_ram:
            clave = clave + (_ram_gb(item),)
        if clave in claves:
            continue
        claves.add(clave)
        unicos.append(item)
    if len(unicos) <= limite:
        return unicos

    elegidos = [unicos[0]]
    firmas = {unicos[0].firma()}

    def tomar(item):
        if item.firma() in firmas or len(elegidos) >= limite:
            return False
        elegidos.append(item)
        firmas.add(item.firma())
        return True

    tomar(min(unicos, key=lambda item: (_total(item), item.firma())))
    for item in unicos:
        if _cpu_de(item) != _cpu_de(unicos[0]) and tomar(item):
            break
    for item in unicos:
        if _vram_de(item) not in (None, _vram_de(unicos[0])) and tomar(item):
            break
    for item in unicos:
        if not tomar(item):
            continue
        if len(elegidos) >= limite:
            break
    return elegidos


def _ram_gb(parcial):
    return sum(linea.producto.capacidad_gb * linea.cantidad for linea in parcial.memorias)


def _huella(parcial):
    discos = tuple(sorted(
        (disco['tipo'], disco['producto'].pk, disco['cantidad'])
        for disco in parcial.discos
    ))
    return (_cpu_de(parcial), _gpu_de(parcial), _ram_gb(parcial), discos)


def _distinta_plataforma(item, otras):
    return any(
        _cpu_de(item) != _cpu_de(otra) or _vram_de(item) != _vram_de(otra)
        for otra in otras
    )


def _comprobacion_pendiente(parcial):
    """True si el armado todavía no puede declararse verificado de punta a punta."""
    if not parcial.discos or _aviso_refrigeracion(parcial):
        return True
    resultado, _por_categoria = evaluaciones_de_seleccion(
        parcial.seleccion,
        memorias_ram=parcial.memorias or None,
        almacenamientos=parcial.discos or None,
    )
    if resultado.estado != ESTADO_COMPATIBLE:
        return True
    almacenamiento = resultado.almacenamiento
    return almacenamiento is not None and almacenamiento.estado == ESTADO_NO_EVALUADA


def _elegir_diversos(candidatos, max_resultados):
    """La primera es la de mayor puntaje. Las otras solo entran si cambian CPU o VRAM.

    Si hay alguna configuración con almacenamiento, las finales salen solo de ese
    grupo. Un armado sin disco puede puntuar más por CPU o GPU, pero no ocupa
    un cupo mientras exista uno completo. Sin ningún disco viable se informan
    las parciales, marcadas después como configuración incompleta.
    """
    con_disco = [item for item in candidatos if item.discos]
    if con_disco:
        candidatos = con_disco
    ordenados = sorted(candidatos, key=lambda item: (
        -item.puntaje,
        1 if _comprobacion_pendiente(item) else 0,
        _total(item),
        item.firma(),
    ))
    unicos = []
    huellas = set()
    for item in ordenados:
        huella = _huella(item)
        if huella in huellas:
            continue
        huellas.add(huella)
        unicos.append(item)
    if not unicos or max_resultados < 1:
        return []

    elegidos = [(unicos[0], 'mejor')]
    if max_resultados >= 2:
        baratas = [
            item for item in unicos
            if item is not unicos[0]
            and _total(item) < _total(unicos[0])
            and _distinta_plataforma(item, [unico for unico, _rol in elegidos])
        ]
        if baratas:
            elegidos.append((
                min(baratas, key=lambda item: (_total(item), -item.puntaje, item.firma())),
                'economica',
            ))
    if max_resultados >= 3:
        ya = [unico for unico, _rol in elegidos]
        for item in unicos:
            if any(item.firma() == otro.firma() for otro in ya):
                continue
            if _distinta_plataforma(item, ya):
                elegidos.append((item, 'equilibrio'))
                break
    elegidos.sort(key=lambda par: (-par[0].puntaje, _total(par[0]), par[0].firma()))
    return elegidos


def _saturar(valor, referencia):
    magnitud = Decimal(valor)
    if magnitud <= 0:
        return Decimal('0')
    tope = Decimal(referencia)
    return magnitud / (magnitud + tope)


def _indice_cpu(cpu):
    nucleos = _saturar(cpu.nucleos, REFERENCIAS['nucleos'])
    frecuencia = _saturar(cpu.frecuencia_base, REFERENCIAS['frecuencia'])
    return (nucleos + frecuencia) / 2


def _indice_ram(capacidad, uso):
    objetivo = OBJETIVO_RAM_GB[uso]
    magnitud = Decimal(capacidad)
    if magnitud <= 0:
        return Decimal('0')
    if magnitud >= objetivo:
        return Decimal('1')
    return magnitud / objetivo


def _aporte(indice, peso, precio, uso):
    if uso != 'general' or precio is None or Decimal(precio) <= 0:
        return peso * indice
    relacion = Decimal('100000') / Decimal(precio)
    if relacion > 2:
        relacion = Decimal('2')
    eficiencia = _saturar(indice * relacion, Decimal('1'))
    return peso * (indice * Decimal('0.70') + eficiencia * Decimal('0.30'))


def _puntaje(parcial, uso, resolucion):
    pesos = _pesos_efectivos(uso, resolucion)
    puntaje = Decimal('0')
    cpu = parcial.seleccion.get('procesador')
    if cpu is not None:
        puntaje += _aporte(_indice_cpu(cpu), pesos['procesador'], cpu.precio, uso)
    if parcial.memorias:
        capacidad = sum(Decimal(linea.producto.capacidad_gb) * linea.cantidad for linea in parcial.memorias)
        precio = sum(Decimal(linea.producto.precio) * linea.cantidad for linea in parcial.memorias)
        puntaje += _aporte(_indice_ram(capacidad, uso), pesos['memoria_ram'], precio, uso)
    gpu = parcial.seleccion.get('tarjeta_grafica')
    if gpu is not None:
        puntaje += _aporte(
            _saturar(gpu.vram_gb, REFERENCIAS['vram_gb']),
            pesos['tarjeta_grafica'],
            gpu.precio,
            uso,
        )
    if parcial.discos:
        capacidad = sum(Decimal(disco['producto'].capacidad_gb) * disco['cantidad'] for disco in parcial.discos)
        precio = sum(Decimal(disco['producto'].precio) * disco['cantidad'] for disco in parcial.discos)
        puntaje += _aporte(_saturar(capacidad, REFERENCIAS['disco_gb']), pesos['almacenamiento'], precio, uso)
    return puntaje


def _pesos(valor):
    return f'{int(valor):,}'.replace(',', '.')


def _refrigeracion_verificada(parcial):
    cooler = parcial.seleccion.get('refrigeracion')
    cpu = parcial.seleccion.get('procesador')
    case = parcial.seleccion.get('gabinete')
    if cooler is None or cpu is None or case is None or getattr(cooler, 'tipo', None) != 'Aire':
        return False
    termica = getattr(cpu, 'potencia_termica_referencia_watts', None)
    disipacion = getattr(cooler, 'disipacion_referencia_watts', None)
    altura = getattr(cooler, 'altura_mm', None)
    maximo = getattr(case, 'altura_max_cooler_mm', None)
    if not termica or not disipacion or not altura or not maximo:
        return False
    return disipacion >= termica and altura <= maximo


def _aviso_refrigeracion(parcial):
    if _refrigeracion_verificada(parcial):
        return None
    cooler = parcial.seleccion.get('refrigeracion')
    cpu = parcial.seleccion.get('procesador')
    incluye = getattr(cpu, 'incluye_cooler', None) if cpu is not None else None
    if cooler is None and incluye is True:
        return (
            'Refrigeración no verificada. El procesador indica cooler de fábrica '
            'y no se agregó otro. La disipación de ese cooler no está registrada, '
            'así que no se afirma que el equipo esté listo para funcionar.'
        )
    if cooler is None and incluye is False:
        return (
            'Refrigeración no verificada. El procesador no incluye cooler de fábrica '
            'y no entró un cooler dedicado compatible dentro del presupuesto. '
            'No se afirma que el equipo esté listo para funcionar.'
        )
    if cooler is None:
        return (
            'Refrigeración no verificada. El procesador no registra si incluye cooler '
            'de fábrica y esta configuración no trae un cooler dedicado. '
            'No se afirma que el equipo esté listo para funcionar.'
        )
    if getattr(cooler, 'tipo', None) == 'Líquida':
        return (
            'Refrigeración no verificada. El socket del cooler se comprobó, pero el '
            'gabinete no registra espacio para el radiador. No se afirma que el equipo '
            'esté listo para funcionar.'
        )
    return (
        'Refrigeración no verificada. El socket del cooler dedicado se comprobó '
        'con las reglas actuales. Falta la disipación de referencia o la altura '
        'frente al gabinete, así que no se afirma que el equipo esté listo para funcionar.'
    )


def _serializar(parcial, presupuesto, uso, resolucion, indice, rol, preferencias=None, referencia_disco=None):
    resultado, por_categoria = evaluaciones_de_seleccion(
        parcial.seleccion,
        memorias_ram=parcial.memorias or None,
        almacenamientos=parcial.discos or None,
    )
    componentes = _componentes_serializados(parcial, por_categoria, uso)
    limitaciones = []
    incompleta = not parcial.discos
    motivo_disco = ''
    if incompleta:
        motivo_disco = (
            'Falta almacenamiento. No se encontró un componente compatible dentro del presupuesto disponible. '
            'Esta configuración no está lista para comprar.'
        )
        if referencia_disco:
            motivo_disco += (
                f' El disco compatible más barato con stock es '
                f'{referencia_disco["nombre"]} (${_pesos(referencia_disco["precio"])}). '
                f'Para esta configuración faltan ${_pesos(referencia_disco["adicional"])}. '
                'Ese monto corresponde solo a esta selección y no es el mínimo de todo el catálogo.'
            )
        else:
            motivo_disco += (
                ' No fue posible verificar la compatibilidad de un disco para esta selección, '
                'así que no se calcula un monto adicional.'
            )
        limitaciones.append(motivo_disco)
    elif (
        resultado.almacenamiento is not None
        and resultado.almacenamiento.estado == ESTADO_NO_EVALUADA
    ):
        limitaciones.extend(textos_almacenamiento_no_verificado(resultado.almacenamiento, parcial.discos))
    aviso_cooler = _aviso_refrigeracion(parcial)
    if aviso_cooler:
        limitaciones.append(aviso_cooler)
    usa_video = (
        parcial.seleccion.get('tarjeta_grafica') is None
        and video_integrado_confirmado(
            parcial.seleccion.get('procesador'),
            parcial.seleccion.get('placa_madre'),
        )
    )
    if usa_video:
        limitaciones.append(MENSAJE_POTENCIA_INTEGRADA)
    prefs = preferencias or Preferencias()
    cumplidos, pendientes_pref = _balance_preferencias(parcial, prefs)
    completamente = resultado.estado == ESTADO_COMPATIBLE and not limitaciones
    if incompleta:
        compatibilidad = 'Configuración incompleta'
    elif completamente:
        compatibilidad = 'Compatible'
    else:
        compatibilidad = 'Reglas comprobadas, con limitaciones'
    return {
        'titulo': 'Configuración incompleta' if incompleta else _titulo(rol, indice),
        'rol': rol,
        'total': int(_total(parcial)),
        'presupuesto': presupuesto,
        'uso': uso,
        'resolucion': resolucion or None,
        'puntaje': float(parcial.puntaje),
        'estado_reglas': resultado.estado,
        'completamente_compatible': completamente,
        'compatibilidad': compatibilidad,
        'explicacion': _explicacion(parcial, uso, resolucion, rol),
        'criterios': criterios_de(uso, resolucion),
        'limitaciones': limitaciones,
        'advertencias': list(resultado.advertencias),
        'usa_graficos_integrados': usa_video,
        'nota_video': MENSAJE_POTENCIA_INTEGRADA if usa_video else '',
        'configuracion_incompleta': incompleta,
        'pieza_faltante': 'Almacenamiento' if incompleta else '',
        'motivo_incompleto': motivo_disco,
        'presupuesto_adicional': referencia_disco['adicional'] if referencia_disco else None,
        'disco_para_completar': referencia_disco['nombre'] if referencia_disco else '',
        'requisitos_cumplidos': cumplidos,
        'preferencias_no_cumplidas': pendientes_pref,
        'componentes': componentes,
    }


def _titulo(rol, indice):
    titulos = {
        'mejor': 'Mejor clasificada',
        'economica': 'Alternativa económica',
        'equilibrio': 'Otro equilibrio de CPU y GPU',
    }
    return titulos.get(rol, f'Opción {indice}')


def _explicacion(parcial, uso, resolucion, rol):
    nombres = {
        'procesador': 'el procesador',
        'memoria_ram': 'la memoria',
        'tarjeta_grafica': 'la tarjeta gráfica',
        'almacenamiento': 'el almacenamiento',
    }
    pesos = _pesos_efectivos(uso, resolucion)
    orden = sorted(pesos, key=lambda clave: pesos[clave], reverse=True)
    prioridad = ', '.join(nombres[clave] for clave in orden[:3])
    texto = (
        f'Para {uso} se prioriza {prioridad}, usando solo los datos técnicos guardados. '
        'El indicador crece cada vez menos y no mide rendimiento. '
        f'El puntaje de esta opción es {parcial.puntaje.quantize(Decimal("0.01"))}.'
    )
    if resolucion in ('1440p', '4k'):
        texto += (
            f' La VRAM de catálogo pesa un poco más porque se indicó {resolucion}; '
            'no se calcula fluidez a esa resolución.'
        )
    texto += (
        f' La memoria se valora hasta {int(OBJETIVO_RAM_GB[uso])} GB para este uso; '
        'por encima de eso el indicador no sube.'
    )
    texto += (
        ' Si dos piezas dejan el mismo indicador de catálogo, se conserva la más barata.'
    )
    if (
        parcial.seleccion.get('tarjeta_grafica') is None
        and video_integrado_confirmado(
            parcial.seleccion.get('procesador'),
            parcial.seleccion.get('placa_madre'),
        )
    ):
        texto += (
            ' Esta opción no trae GPU dedicada: el procesador y la placa tienen '
            'confirmados los gráficos integrados y las salidas de video.'
        )
    if rol == 'economica':
        texto += (
            ' Esta alternativa cuesta menos. No es equivalente a la mejor clasificada: '
            'su puntaje, con los mismos indicadores de catálogo, es más bajo.'
        )
    elif rol == 'equilibrio':
        texto += (
            ' Cambia el procesador o la VRAM de catálogo respecto de la mejor clasificada. '
            'Eso no indica más o menos fluidez.'
        )
    texto += ' No se estiman FPS.'
    return texto


def _componentes_serializados(parcial, por_categoria, uso):
    filas = []
    orden = (
        ('procesador', 'procesador'),
        ('placa_madre', 'placa_madre'),
        ('memoria_ram', 'memoria_ram'),
        ('refrigeracion', 'refrigeracion_cooler'),
        ('tarjeta_grafica', 'tarjeta_grafica'),
        ('gabinete', 'gabinete'),
        ('fuente_de_poder', 'fuente_de_poder'),
    )
    for clave, ui in orden:
        if clave == 'memoria_ram':
            evaluacion = por_categoria.get('memoria_ram')
            for linea in parcial.memorias:
                filas.append(_fila(
                    'memoria_ram',
                    'Memoria RAM',
                    linea.producto,
                    linea.cantidad,
                    _frase_ram(linea, uso),
                    evaluacion,
                ))
            continue
        producto = parcial.seleccion.get(clave)
        if producto is None:
            continue
        filas.append(_fila(
            _TIPO_API[clave],
            ETIQUETAS[clave],
            producto,
            1,
            _frase_producto(clave, producto, uso),
            por_categoria.get(ui),
        ))
    evaluacion_disco = por_categoria.get('almacenamiento')
    if evaluacion_disco is not None and evaluacion_disco.estado == ESTADO_NO_EVALUADA:
        # La explicación queda una sola vez en las limitaciones. La etiqueta
        # genérica repetiría el mismo párrafo dentro de la tarjeta y el detalle.
        evaluacion_disco = None
    for disco in parcial.discos:
        filas.append(_fila(
            disco['tipo'],
            'Almacenamiento',
            disco['producto'],
            disco['cantidad'],
            _frase_disco(disco, uso),
            evaluacion_disco,
        ))
    return filas


def _fila(tipo, etiqueta, producto, cantidad, frase, evaluacion):
    precio = Decimal(producto.precio)
    motivo = frase
    if evaluacion is not None and evaluacion.etiqueta:
        motivo = f'{frase} {evaluacion.etiqueta}'
    return {
        'tipo': tipo,
        'id': producto.pk,
        'cantidad': cantidad,
        'nombre': producto.nombre,
        'categoria': etiqueta,
        'precio': str(precio),
        'subtotal': int(precio * cantidad),
        'motivo': motivo.strip(),
    }


def _frase_producto(clave, producto, uso):
    del uso
    if clave == 'procesador':
        return (
            f'Se eligió por {producto.nucleos} núcleos y {producto.frecuencia_base} GHz de catálogo, '
            f'socket {producto.socket}. Esos dos datos forman el indicador del procesador. '
            'No es una medición de rendimiento.'
        )
    if clave == 'placa_madre':
        return (
            f'Socket {producto.socket_cpu}, {producto.tipo_ram_soportado}, '
            f'formato {producto.formato}. No suma puntaje: se conserva porque cumple '
            'el socket y la memoria dentro del presupuesto.'
        )
    if clave == 'tarjeta_grafica':
        largo = f', {producto.largo_mm} mm de largo' if producto.largo_mm else ', sin largo registrado'
        return (
            f'Se eligió por {producto.vram_gb} GB de VRAM de catálogo{largo}. '
            'La VRAM es el indicador de la tarjeta. El tipo de memoria y la interfaz '
            'no se usan como rendimiento.'
        )
    if clave == 'gabinete':
        largo = (
            f', admite GPU de hasta {producto.largo_max_gpu_mm} mm'
            if producto.largo_max_gpu_mm else ', sin largo máximo registrado'
        )
        altura = (
            f' Admite un cooler de aire de hasta {producto.altura_max_cooler_mm} mm.'
            if producto.altura_max_cooler_mm else ' Sin altura máxima de cooler registrada.'
        )
        return (
            f'Formato {producto.formato_soporte}{largo}.{altura} '
            'No suma puntaje: entra si la placa y la GPU caben.'
        )
    if clave == 'fuente_de_poder':
        return (
            f'{producto.potencia_watts} W nominales. No suma puntaje: entra si cubre '
            'la estimación de catálogo. Esa cifra no es una garantía eléctrica.'
        )
    if clave == 'refrigeracion':
        altura = f' Altura {producto.altura_mm} mm.' if producto.altura_mm else ' Sin altura registrada.'
        disipacion = (
            f' Disipación de referencia {producto.disipacion_referencia_watts} W.'
            if producto.disipacion_referencia_watts else ' Sin disipación de referencia registrada.'
        )
        return (
            f'Cooler {producto.tipo}, sockets indicados: {producto.socket_compatibles}.'
            f'{altura}{disipacion} No suma puntaje.'
        )
    return producto.nombre


def _frase_ram(linea, uso):
    return (
        f'Se eligió por {linea.producto.capacidad_gb} GB {linea.producto.tipo_ddr} por unidad, '
        f'cantidad {linea.cantidad}. El indicador de {uso} llega a 1 en '
        f'{int(OBJETIVO_RAM_GB[uso])} GB y ahí se detiene.'
    )


def _frase_disco(disco, uso):
    del uso
    clase = 'SSD' if disco['tipo'] == 'almacenamiento_ssd' else 'HDD'
    return (
        f'Se eligió este {clase} por {disco["producto"].capacidad_gb} GB de catálogo, '
        f'cantidad {disco["cantidad"]}. Si un SSD cabe y pasa las reglas, tiene prioridad sobre un HDD.'
    )
