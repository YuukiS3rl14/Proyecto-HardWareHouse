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
  Un HDD solo entra cuando ningún SSD cabe. No se comprueban SATA, M.2 ni NVMe
- uso general: el mismo indicador se combina con lo que aporta por peso
  gastado, para no pagar más si el dato de catálogo no mejora

La fuente no suma puntaje. Sus watts solo aprueban o rechazan la regla de
potencia. Placa, gabinete y cooler tampoco suman: solo cumplen las reglas.
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
    MENSAJE_ALMACENAMIENTO,
    LineaRam,
    evaluaciones_de_seleccion,
    validar_armado,
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


@dataclass
class Informe:
    sin_stock: list = field(default_factory=list)
    sin_presupuesto: list = field(default_factory=list)
    descartes: list = field(default_factory=list)

    def anotar(self, textos):
        for texto in textos:
            limpio = str(texto or '').strip()
            if limpio and limpio not in self.descartes:
                self.descartes.append(limpio)

    def mensaje(self, etapa):
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
    }


def generar_recomendaciones(
    presupuesto_clp,
    uso,
    *,
    resolucion='',
    seleccion=None,
    memorias=None,
    almacenamientos=None,
    max_resultados=3,
):
    """Devuelve hasta ``max_resultados`` armados, o el motivo por el que no hay ninguno."""
    if uso not in USOS:
        raise EntradaInvalida('El uso debe ser gaming, trabajo, edición o general.')
    if resolucion not in RESOLUCIONES:
        raise EntradaInvalida('La resolución debe ser 1080p, 1440p, 4K o quedar vacía.')
    if not isinstance(presupuesto_clp, int) or isinstance(presupuesto_clp, bool) or presupuesto_clp < 1:
        raise EntradaInvalida('El presupuesto máximo debe ser un entero positivo en CLP.')

    presupuesto = Decimal(presupuesto_clp)
    parcial = Parcial(
        seleccion=dict(seleccion or {}),
        memorias=list(memorias or []),
        discos=[dict(item) for item in (almacenamientos or [])],
    )
    fallo = _rechazo_inicial(parcial, presupuesto)
    if fallo:
        return _sin_resultado(presupuesto_clp, uso, resolucion, fallo, [])

    catalogo = _catalogo_con_stock()
    informe = Informe()
    haz = [parcial]
    for etapa in _OBLIGATORIAS:
        haz = _ampliar(haz, etapa, True, catalogo, presupuesto, uso, resolucion, informe)
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
        if pendientes and not informe.descartes:
            texto = (
                'Las combinaciones que caben en el presupuesto todavía tienen verificaciones pendientes. '
                + ' '.join(pendientes[:4])
            )
        return _sin_resultado(presupuesto_clp, uso, resolucion, texto, detalle)

    informe_discos = Informe()
    con_disco = _ampliar(
        verificados, 'almacenamiento', False, catalogo, presupuesto, uso, resolucion, informe_discos,
    )
    con_disco = _ampliar(con_disco, 'refrigeracion', False, catalogo, presupuesto, uso, resolucion, informe)
    elegidos = _elegir_diversos(con_disco, max_resultados)

    return {
        'status': 'success',
        'uso': uso,
        'resolucion': resolucion or None,
        'presupuesto': presupuesto_clp,
        'criterios': criterios_de(uso, resolucion),
        'recomendaciones': [
            _serializar(candidato, presupuesto_clp, uso, resolucion, indice, rol)
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
            'del presupuesto, se usa como disco principal. Un HDD queda como alternativa '
            'solo cuando ningún SSD cabe. No se comprueban puertos SATA, M.2 ni NVMe, '
            'y no se agrega un segundo disco.'
        ),
        (
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


def _ampliar(haz, etapa, obligatoria, catalogo, presupuesto, uso, resolucion, informe):
    local = Informe()
    siguientes = []
    for parcial in haz:
        if _ya_tiene(parcial, etapa):
            parcial.puntaje = _puntaje(parcial, uso, resolucion)
            siguientes.append(parcial)
            continue
        opciones = _opciones(parcial, etapa, catalogo, presupuesto, uso)
        if not opciones:
            if not obligatoria:
                parcial.puntaje = _puntaje(parcial, uso, resolucion)
                siguientes.append(parcial)
            elif not catalogo.get(etapa):
                if ETIQUETAS[etapa] not in local.sin_stock:
                    local.sin_stock.append(ETIQUETAS[etapa])
            else:
                if ETIQUETAS[etapa] not in local.sin_presupuesto:
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
        return []
    return _quedan_en_el_haz(siguientes, etapa, uso, presupuesto)


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


def _opciones(parcial, etapa, catalogo, presupuesto, uso):
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
        return opciones
    if etapa == 'almacenamiento':
        opciones = []
        for tipo, producto in catalogo['almacenamiento']:
            if producto.precio <= restante and producto.stock >= 1:
                opciones.append({'tipo': tipo, 'producto': producto, 'cantidad': 1})
        ssds = [opcion for opcion in opciones if opcion['tipo'] == 'almacenamiento_ssd']
        if ssds:
            return ssds
        return opciones
    if etapa == 'refrigeracion':
        politica = _politica_cooler(parcial, uso)
        if politica in ('fijo', 'incluido', 'omitir'):
            return []
        opciones = [
            cooler
            for cooler in catalogo['refrigeracion']
            if cooler.precio <= restante and _cooler_aceptado(parcial, cooler)
        ]
        aire = [cooler for cooler in opciones if cooler.tipo == 'Aire']
        return aire or opciones
    clave = _CLAVE_SELECCION[etapa]
    return [
        producto
        for producto in catalogo[clave]
        if producto.precio <= restante and producto.stock >= 1
    ]


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
    return puntos


def _vram_de(parcial):
    gpu = parcial.seleccion.get('tarjeta_grafica')
    return getattr(gpu, 'vram_gb', None)


def _cpu_de(parcial):
    cpu = parcial.seleccion.get('procesador')
    return getattr(cpu, 'pk', None)


def _quedan_en_el_haz(siguientes, etapa, uso, presupuesto):
    del etapa, presupuesto
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
        if clave in claves:
            continue
        claves.add(clave)
        unicos.append(item)
    if len(unicos) <= ANCHURA:
        return unicos

    elegidos = [unicos[0]]
    firmas = {unicos[0].firma()}

    def tomar(item):
        if item.firma() in firmas or len(elegidos) >= ANCHURA:
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
        if len(elegidos) >= ANCHURA:
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


def _elegir_diversos(candidatos, max_resultados):
    """La primera es la de mayor puntaje. Las otras solo entran si cambian CPU o VRAM."""
    ordenados = sorted(candidatos, key=lambda item: (-item.puntaje, _total(item), item.firma()))
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


def _serializar(parcial, presupuesto, uso, resolucion, indice, rol):
    resultado, por_categoria = evaluaciones_de_seleccion(
        parcial.seleccion,
        memorias_ram=parcial.memorias or None,
        almacenamientos=parcial.discos or None,
    )
    componentes = _componentes_serializados(parcial, por_categoria)
    limitaciones = []
    if (
        parcial.discos
        and resultado.almacenamiento is not None
        and resultado.almacenamiento.estado == ESTADO_NO_EVALUADA
    ):
        limitaciones.append(MENSAJE_ALMACENAMIENTO)
    aviso_cooler = _aviso_refrigeracion(parcial)
    if aviso_cooler:
        limitaciones.append(aviso_cooler)
    completamente = resultado.estado == ESTADO_COMPATIBLE and not limitaciones
    if completamente:
        compatibilidad = 'Compatible'
    else:
        compatibilidad = 'Reglas comprobadas, con limitaciones'
    return {
        'titulo': _titulo(rol, indice),
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


def _componentes_serializados(parcial, por_categoria):
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
                    _frase_ram(linea),
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
            _frase_producto(clave, producto),
            por_categoria.get(ui),
        ))
    evaluacion_disco = por_categoria.get('almacenamiento')
    for disco in parcial.discos:
        filas.append(_fila(
            disco['tipo'],
            'Almacenamiento',
            disco['producto'],
            disco['cantidad'],
            _frase_disco(disco),
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


def _frase_producto(clave, producto):
    if clave == 'procesador':
        return f'{producto.nucleos} núcleos a {producto.frecuencia_base} GHz, socket {producto.socket}.'
    if clave == 'placa_madre':
        return (
            f'Socket {producto.socket_cpu}, {producto.tipo_ram_soportado}, '
            f'formato {producto.formato}.'
        )
    if clave == 'tarjeta_grafica':
        largo = f', {producto.largo_mm} mm de largo' if producto.largo_mm else ', sin largo registrado'
        return f'{producto.vram_gb} GB de VRAM{largo}.'
    if clave == 'gabinete':
        largo = (
            f', admite GPU de hasta {producto.largo_max_gpu_mm} mm'
            if producto.largo_max_gpu_mm else ', sin largo máximo registrado'
        )
        return f'Formato {producto.formato_soporte}{largo}.'
    if clave == 'fuente_de_poder':
        return (
            f'{producto.potencia_watts} W nominales. '
            'La cifra de potencia es una estimación de catálogo, no una garantía eléctrica.'
        )
    if clave == 'refrigeracion':
        return f'Cooler {producto.tipo}, sockets indicados: {producto.socket_compatibles}.'
    return producto.nombre


def _frase_ram(linea):
    return (
        f'{linea.producto.capacidad_gb} GB {linea.producto.tipo_ddr} por unidad, '
        f'cantidad {linea.cantidad}.'
    )


def _frase_disco(disco):
    return f'{disco["producto"].capacidad_gb} GB, cantidad {disco["cantidad"]}.'
