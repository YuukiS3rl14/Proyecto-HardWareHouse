"""Reglas de compatibilidad del armado de PC.

La función no declara compatible un socket "Otro" ni un formato que no esté
en la jerarquía conocida. Los espacios y las mayúsculas no cambian el resultado.

Estimación de potencia de la fuente
-----------------------------------
Con CPU, GPU y fuente presentes:

    base = potencia_referencia_cpu + consumo_referencia_gpu + reserva_otros_watts
    estimacion = techo(base * margen)
    minimo = max(estimacion, potencia_minima_fuente_gpu) si esa cifra existe

La política por defecto usa 150 W de reserva y un margen de 1.20. Se puede
cambiar con el argumento ``politica`` o con el ajuste
``POLITICA_POTENCIA_ARMADO = {'reserva_otros_watts': 150, 'margen': '1.20'}``.

Es una estimación de catálogo, no una garantía eléctrica. No mide picos,
eficiencia, rieles, conectores, largo de la fuente ni temperatura. La
potencia de referencia no es el consumo máximo ni el TDP. Cumplir el mínimo
no declara la fuente completamente compatible.

La reserva de 150 W es un margen fijo para placa, memoria, discos y
ventiladores. No aumenta al agregar SSD o HDD y no mide el consumo de cada
unidad. Unos pocos discos caben en ese margen junto con el resto del equipo;
muchas unidades exigirían revisar la reserva, porque la fórmula no lo hace.

Largo de la GPU
---------------
Si hay GPU y gabinete, la tarjeta cabe en largo cuando largo_mm es menor o
igual que largo_max_gpu_mm. La igualdad cumple. Un milímetro de más no.
Esta regla no valida grosor, altura ni el espacio que ocupan los radiadores.

Memoria RAM
-----------
``capacidad_gb`` es la capacidad del producto tal como se vende: un módulo
suelto o el kit completo. La capacidad del armado es la suma de
cantidad × capacidad_gb. No se multiplica otra vez por ``modulos_por_producto``,
porque ese número ya está dentro de la capacidad del kit.

``capacidad_modulo_gb`` es la capacidad de un solo módulo. Si ambos datos
existen, debe cumplirse capacidad_gb = módulos × capacidad por módulo. Si no
coinciden, el dato es insuficiente y no se elige una de las dos cifras.

Las ranuras ocupadas son la suma de cantidad × módulos por producto.
Un dato técnico vacío queda NULL y no se deduce del nombre. Eso es dato
insuficiente, no una compatibilidad. Faltar la RAM o la placa es selección
incompleta.

Mezclar productos o kits distintos avisa que no se garantiza la estabilidad
ni el perfil XMP/EXPO, aunque compartan DDR y velocidad. Esa advertencia no
bloquea. No se promete dual channel ni una velocidad final.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_CEILING


SOCKETS_CONOCIDOS = frozenset({'AM4', 'AM5', 'LGA1200', 'LGA1700'})
TIPOS_DDR_CONOCIDOS = frozenset({'DDR3', 'DDR4', 'DDR5'})
FORMATOS_RAM_CONOCIDOS = frozenset({'DIMM', 'SO-DIMM'})
FORMATOS_ORDENADOS = ('MINI-ITX', 'MICRO-ATX', 'ATX')

ESTADO_COMPATIBLE = 'compatible'
ESTADO_INCOMPATIBLE = 'incompatible'
ESTADO_DATOS_INSUFICIENTES = 'datos_insuficientes'
ESTADO_INCOMPLETO = 'incompleto'
ESTADO_NO_EVALUADA = 'no_evaluada'
MENSAJE_NO_EVALUADA = 'Compatibilidad no evaluada'
MENSAJE_ALMACENAMIENTO = (
    'Compatibilidad no evaluada. No se comprueban puertos SATA, ranuras M.2 '
    'ni bahías. La reserva de potencia es un margen fijo para placa, memoria, '
    'discos y ventiladores; no suma el consumo de cada unidad.'
)
MENSAJE_ELEGIR_GABINETE = 'Selecciona un gabinete para comprobar el largo.'
MENSAJE_ELEGIR_GPU = 'Selecciona una GPU para comprobar el largo.'
MENSAJE_MEZCLA_RAM = (
    'Hay productos o kits de RAM distintos. No se garantiza la estabilidad ni '
    'el funcionamiento del perfil XMP/EXPO, aunque compartan DDR y velocidad.'
)
ACLARACION_RAM = (
    'La capacidad total suma la cantidad de cada producto por su capacidad_gb. '
    'Esa cifra es la del producto vendido, módulo suelto o kit completo, y no se '
    'multiplica por los módulos. No se comprueba dual channel ni la velocidad final.'
)

REGLAS_POR_CATEGORIA = {
    'procesador': ('socket',),
    'placa_madre': ('socket', 'ddr', 'formato', 'formato_ram', 'ranuras_ram', 'capacidad_ram'),
    'memoria_ram': ('ddr', 'formato_ram', 'ranuras_ram', 'capacidad_ram'),
    'gabinete': ('formato', 'largo'),
    'refrigeracion': ('cooler',),
    'fuente_de_poder': ('potencia',),
    'tarjeta_grafica': ('largo',),
}

CLAVE_POR_CATEGORIA = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'memoria_ram': 'memoria_ram',
    'gabinete': 'gabinete',
    'refrigeracion': 'refrigeracion',
    'fuente_de_poder': 'fuente_de_poder',
    'tarjeta_grafica': 'tarjeta_grafica',
}

_PRIORIDAD = {
    ESTADO_COMPATIBLE: 0,
    ESTADO_INCOMPLETO: 1,
    ESTADO_DATOS_INSUFICIENTES: 2,
    ESTADO_INCOMPATIBLE: 3,
}

_ESTADOS_QUE_BLOQUEAN = frozenset({ESTADO_INCOMPATIBLE, ESTADO_DATOS_INSUFICIENTES})


def normalizar_spec(valor):
    """Quita espacios y pasa a mayúsculas. None y vacío quedan en cadena vacía."""
    if valor is None:
        return ''
    return re.sub(r'\s+', '', str(valor).strip().upper())


def _etiqueta(valor):
    return valor or 'vacío'


@dataclass(frozen=True)
class Hallazgo:
    regla: str
    estado: str
    mensaje: str


@dataclass(frozen=True)
class LineaRam:
    """Una línea de RAM: el producto vendido y cuántas unidades se piden."""

    producto: object
    cantidad: int = 1


@dataclass
class ResultadoCompatibilidad:
    hallazgos: list = field(default_factory=list)
    advertencias: list = field(default_factory=list)

    @property
    def estado(self):
        if not self.hallazgos:
            return ESTADO_COMPATIBLE
        return max(self.hallazgos, key=lambda hallazgo: _PRIORIDAD[hallazgo.estado]).estado

    @property
    def es_compatible(self):
        return self.estado == ESTADO_COMPATIBLE

    @property
    def motivos_de_rechazo(self):
        return [
            hallazgo.mensaje
            for hallazgo in self.hallazgos
            if hallazgo.estado in _ESTADOS_QUE_BLOQUEAN
        ]

    @property
    def bloquea_agregar(self):
        """Incompatibilidad o datos insuficientes impiden agregar el armado."""
        return bool(self.motivos_de_rechazo)


@dataclass(frozen=True)
class EvaluacionCandidato:
    estado: str
    coincidencias: tuple = ()
    motivos: tuple = ()
    pendientes: tuple = ()
    advertencias: tuple = ()

    @property
    def etiqueta(self):
        if self.estado == ESTADO_NO_EVALUADA:
            return self.motivos[0] if self.motivos else MENSAJE_NO_EVALUADA
        if self.estado == ESTADO_COMPATIBLE:
            if (
                len(self.coincidencias) == 1
                and (
                    self.coincidencias[0].startswith('Cumple la estimación de potencia')
                    or self.coincidencias[0].startswith('Cumple el límite de largo')
                )
            ):
                return self.coincidencias[0]
            return 'Coincide: ' + ', '.join(self.coincidencias)
        if self.estado == ESTADO_INCOMPLETO:
            return 'Selección incompleta'
        if self.estado == ESTADO_DATOS_INSUFICIENTES:
            return 'Datos insuficientes'
        return 'Incompatible'


def evaluar_candidato(
    categoria,
    candidato,
    procesador=None,
    placa_madre=None,
    memoria_ram=None,
    gabinete=None,
    refrigeracion=None,
    tarjeta_grafica=None,
    fuente_de_poder=None,
    politica=None,
    memorias_ram=None,
):
    """Clasifica un candidato reemplazando la pieza previa de su categoría.

    Usa validar_armado() como única fuente de las reglas. Una categoría sin
    regla queda como no evaluada: no se afirma que sea compatible.
    """
    if categoria not in REGLAS_POR_CATEGORIA:
        return EvaluacionCandidato(
            ESTADO_NO_EVALUADA,
            motivos=(MENSAJE_NO_EVALUADA,),
        )

    piezas = {
        'procesador': procesador,
        'placa_madre': placa_madre,
        'memoria_ram': memoria_ram,
        'gabinete': gabinete,
        'refrigeracion': refrigeracion,
        'tarjeta_grafica': tarjeta_grafica,
        'fuente_de_poder': fuente_de_poder,
    }
    if categoria == 'memoria_ram' and memorias_ram is not None:
        piezas['memorias_ram'] = memorias_ram
    else:
        piezas[CLAVE_POR_CATEGORIA[categoria]] = candidato
        if memorias_ram is not None:
            piezas['memoria_ram'] = None
            piezas['memorias_ram'] = memorias_ram
    politica_activa = politica or politica_potencia()
    argumentos = {clave: valor for clave, valor in piezas.items() if clave != 'memorias_ram'}
    resultado = validar_armado(
        **argumentos,
        politica=politica_activa,
        memorias_ram=piezas.get('memorias_ram'),
    )
    hallazgos_por_regla = {}
    for hallazgo in resultado.hallazgos:
        if hallazgo.regla not in REGLAS_POR_CATEGORIA[categoria]:
            continue
        previo = hallazgos_por_regla.get(hallazgo.regla)
        if previo is None or _PRIORIDAD[hallazgo.estado] > _PRIORIDAD[previo.estado]:
            hallazgos_por_regla[hallazgo.regla] = hallazgo

    coincidencias = []
    motivos = []
    pendientes = []
    estados = []
    for regla in REGLAS_POR_CATEGORIA[categoria]:
        hallazgo = hallazgos_por_regla.get(regla)
        if hallazgo is not None:
            estados.append(hallazgo.estado)
            if hallazgo.estado == ESTADO_INCOMPLETO:
                pendientes.append(hallazgo.mensaje)
            else:
                motivos.append(hallazgo.mensaje)
            continue
        if _regla_puede_comprobarse(regla, piezas, politica_activa):
            estados.append(ESTADO_COMPATIBLE)
            coincidencias.append(_texto_coincidencia(regla, piezas, politica_activa))
        else:
            estados.append(ESTADO_INCOMPLETO)
            pendientes.append('Selección incompleta para comprobar esta regla.')

    avisos = ()
    if categoria in ('memoria_ram', 'placa_madre'):
        avisos = tuple(resultado.advertencias)
    return EvaluacionCandidato(
        _estado_de_candidato(estados),
        tuple(coincidencias),
        tuple(motivos),
        tuple(pendientes),
        avisos,
    )


def _estado_de_candidato(estados):
    if ESTADO_INCOMPATIBLE in estados:
        return ESTADO_INCOMPATIBLE
    if ESTADO_DATOS_INSUFICIENTES in estados:
        return ESTADO_DATOS_INSUFICIENTES
    if ESTADO_COMPATIBLE in estados:
        return ESTADO_COMPATIBLE
    return ESTADO_INCOMPLETO


def _regla_puede_comprobarse(regla, piezas, politica):
    if regla == 'socket':
        return piezas['procesador'] is not None and piezas['placa_madre'] is not None
    if regla == 'ddr':
        return _memoria_comprobada('ddr', piezas)
    if regla == 'formato_ram':
        return _memoria_comprobada('formato_ram', piezas)
    if regla == 'ranuras_ram':
        return _memoria_comprobada('ranuras_ram', piezas)
    if regla == 'capacidad_ram':
        return _memoria_comprobada('capacidad_ram', piezas)
    if regla == 'formato':
        return piezas['placa_madre'] is not None and piezas['gabinete'] is not None
    if regla == 'cooler':
        return piezas['refrigeracion'] is not None and (
            piezas['procesador'] is not None or piezas['placa_madre'] is not None
        )
    if regla == 'potencia':
        return _potencia_cumplida(piezas, politica)
    if regla == 'largo':
        return _largo_cumplido(piezas)
    return False


def _texto_coincidencia(regla, piezas, politica):
    if regla == 'socket':
        return f"Socket {normalizar_spec(piezas['procesador'].socket)}"
    if regla == 'ddr':
        return _texto_ddr(piezas)
    if regla == 'formato_ram':
        return _texto_formato_ram(piezas)
    if regla == 'ranuras_ram':
        return _texto_ranuras_ram(piezas)
    if regla == 'capacidad_ram':
        return _texto_capacidad_ram(piezas)
    if regla == 'formato':
        return f"Formato {normalizar_spec(piezas['placa_madre'].formato)}"
    if regla == 'potencia':
        return _texto_potencia_cumplida(piezas, politica)
    if regla == 'largo':
        return _texto_largo_cumplido(piezas)
    sockets = []
    if piezas['procesador'] is not None:
        sockets.append(normalizar_spec(piezas['procesador'].socket))
    if piezas['placa_madre'] is not None:
        socket_placa = normalizar_spec(piezas['placa_madre'].socket_cpu)
        if socket_placa not in sockets:
            sockets.append(socket_placa)
    return 'Cooler para ' + ', '.join(sockets)


_UI_POR_CLAVE = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'memoria_ram': 'memoria_ram',
    'gabinete': 'gabinete',
    'refrigeracion': 'refrigeracion_cooler',
    'fuente_de_poder': 'fuente_de_poder',
    'tarjeta_grafica': 'tarjeta_grafica',
}

_CATEGORIA_POR_CLAVE = {
    clave: categoria for categoria, clave in CLAVE_POR_CATEGORIA.items()
}

_TEXTO_ARMADO = {
    ESTADO_COMPATIBLE: 'Compatible',
    ESTADO_INCOMPATIBLE: 'Incompatible (Revisar Componentes)',
    ESTADO_DATOS_INSUFICIENTES: 'Datos insuficientes (no se declara compatible)',
    ESTADO_INCOMPLETO: 'Selección incompleta',
}


def evaluaciones_de_seleccion(piezas, memorias_ram=None):
    """Evalúa cada pieza presente con las reglas de su categoría.

    La única fuente es validar_armado(), a través de evaluar_candidato().
    Si hay varias RAM, se evalúan como un conjunto y no como una sola pieza.
    """
    presentes = {clave: pieza for clave, pieza in piezas.items() if pieza is not None}
    if memorias_ram is not None:
        presentes.pop('memoria_ram', None)
    resultado = validar_armado(**presentes, memorias_ram=memorias_ram)
    por_categoria = {}
    for clave, pieza in presentes.items():
        otras = {nombre: valor for nombre, valor in presentes.items() if nombre != clave}
        por_categoria[_UI_POR_CLAVE[clave]] = evaluar_candidato(
            _CATEGORIA_POR_CLAVE[clave],
            pieza,
            memorias_ram=memorias_ram,
            **otras,
        )
    if memorias_ram:
        por_categoria['memoria_ram'] = evaluar_candidato(
            'memoria_ram',
            memorias_ram[0].producto,
            memorias_ram=memorias_ram,
            **presentes,
        )
    return resultado, por_categoria


def texto_del_armado(resultado, hay_pieza_sin_regla, hay_pieza_con_regla):
    """Texto único del armado exportado. No reutiliza una consulta anterior."""
    if not hay_pieza_con_regla:
        return MENSAJE_NO_EVALUADA
    if resultado.estado == ESTADO_COMPATIBLE and hay_pieza_sin_regla:
        return 'Reglas comprobadas; hay piezas sin regla de compatibilidad'
    return _TEXTO_ARMADO[resultado.estado]


def validar_armado(
    procesador=None,
    placa_madre=None,
    memoria_ram=None,
    gabinete=None,
    refrigeracion=None,
    tarjeta_grafica=None,
    fuente_de_poder=None,
    politica=None,
    memorias_ram=None,
):
    """Valida las piezas presentes. Las que no participan en estas reglas se ignoran.

    ``memoria_ram`` es una sola pieza con cantidad 1. ``memorias_ram`` es el
    conjunto de líneas y, si viene, reemplaza a esa pieza suelta.
    Devuelve compatible solo si cada regla aplicable quedó resuelta con datos conocidos.
    Una pieza sin su par es selección incompleta y no se trata como conflicto.
    """
    lineas = _lineas_ram(memoria_ram, memorias_ram)
    candidatos = (
        _evaluar_socket(procesador, placa_madre),
        _evaluar_formato(placa_madre, gabinete),
        _evaluar_largo(tarjeta_grafica, gabinete),
        _evaluar_potencia(procesador, tarjeta_grafica, fuente_de_poder, politica or politica_potencia()),
    )
    hallazgos = [hallazgo for hallazgo in candidatos if hallazgo is not None]
    hallazgos.extend(_evaluar_cooler(refrigeracion, procesador, placa_madre))
    hallazgos.extend(_evaluar_memorias(lineas, placa_madre))
    return ResultadoCompatibilidad(hallazgos, _advertencias_ram(lineas))


def _evaluar_socket(procesador, placa_madre):
    if procesador is None and placa_madre is None:
        return None
    if procesador is None or placa_madre is None:
        return Hallazgo(
            'socket',
            ESTADO_INCOMPLETO,
            'Falta el procesador o la placa madre para comprobar el socket.',
        )

    socket_cpu = normalizar_spec(procesador.socket)
    socket_placa = normalizar_spec(placa_madre.socket_cpu)
    desconocidos = [valor for valor in (socket_cpu, socket_placa) if valor not in SOCKETS_CONOCIDOS]
    if desconocidos:
        detalle = ', '.join(_etiqueta(valor) for valor in desconocidos)
        return Hallazgo(
            'socket',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede verificar el socket porque hay un valor desconocido '
            f'({detalle}). Un socket "Otro" no se considera compatible.',
        )
    if socket_cpu != socket_placa:
        return Hallazgo(
            'socket',
            ESTADO_INCOMPATIBLE,
            f'El socket del procesador ({socket_cpu}) no coincide con el de la placa madre ({socket_placa}).',
        )
    return None


def _lineas_ram(memoria_ram, memorias_ram):
    """Una lista explícita gana. Si no hay lista, la pieza suelta cuenta como una."""
    if memorias_ram is not None:
        return [_como_linea(item) for item in memorias_ram]
    if memoria_ram is None:
        return []
    return [LineaRam(memoria_ram, 1)]


def _como_linea(item):
    if isinstance(item, LineaRam):
        return item
    if isinstance(item, tuple) and len(item) == 2:
        return LineaRam(item[0], int(item[1]))
    return LineaRam(item, 1)


def _lineas_en(piezas):
    return _lineas_ram(piezas.get('memoria_ram'), piezas.get('memorias_ram'))


def _memoria_comprobada(regla, piezas):
    lineas = _lineas_en(piezas)
    placa = piezas.get('placa_madre')
    if not lineas or placa is None:
        return False
    return _hallazgo_memoria(regla, lineas, placa) is None


def _evaluar_memorias(lineas, placa_madre):
    return [
        hallazgo
        for hallazgo in (
            _hallazgo_memoria('ddr', lineas, placa_madre),
            _hallazgo_memoria('formato_ram', lineas, placa_madre),
            _hallazgo_memoria('ranuras_ram', lineas, placa_madre),
            _hallazgo_memoria('capacidad_ram', lineas, placa_madre),
        )
        if hallazgo is not None
    ]


def _hallazgo_memoria(regla, lineas, placa):
    if regla == 'ddr':
        return _evaluar_ddr(lineas, placa)
    if regla == 'formato_ram':
        return _evaluar_formato_ram(lineas, placa)
    if regla == 'ranuras_ram':
        return _evaluar_ranuras_ram(lineas, placa)
    if regla == 'capacidad_ram':
        return _evaluar_capacidad_ram(lineas, placa)
    return None


def _identidad_producto(producto):
    pk = getattr(producto, 'pk', None)
    if pk is not None:
        return ('pk', pk)
    identificador = getattr(producto, 'id', None)
    if identificador is not None:
        return ('id', identificador)
    return ('obj', id(producto))


def _advertencias_ram(lineas):
    identidades = {_identidad_producto(linea.producto) for linea in lineas}
    if len(identidades) < 2:
        return []
    return [MENSAJE_MEZCLA_RAM]


def _tipos_ddr(lineas):
    conocidos = []
    desconocido = False
    for linea in lineas:
        tipo = normalizar_spec(getattr(linea.producto, 'tipo_ddr', None))
        if tipo not in TIPOS_DDR_CONOCIDOS:
            desconocido = True
        elif tipo not in conocidos:
            conocidos.append(tipo)
    return conocidos, desconocido


def _formatos_ram(lineas):
    conocidos = []
    desconocido = False
    for linea in lineas:
        formato = normalizar_spec(getattr(linea.producto, 'formato_ram', None))
        if formato not in FORMATOS_RAM_CONOCIDOS:
            desconocido = True
        elif formato not in conocidos:
            conocidos.append(formato)
    return conocidos, desconocido


def _evaluar_ddr(lineas, placa_madre):
    if not lineas and placa_madre is None:
        return None
    conocidos, desconocido = _tipos_ddr(lineas)
    if len(conocidos) > 1:
        return Hallazgo(
            'ddr',
            ESTADO_INCOMPATIBLE,
            f"Hay RAM {' y '.join(conocidos)}. No se pueden mezclar tipos DDR.",
        )
    if desconocido and (len(lineas) > 1 or placa_madre is not None):
        return Hallazgo(
            'ddr',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede verificar la RAM porque el tipo DDR no es conocido.',
        )
    if not lineas or placa_madre is None:
        return Hallazgo(
            'ddr',
            ESTADO_INCOMPLETO,
            'Falta la memoria RAM o la placa madre para comprobar el tipo DDR.',
        )
    tipo_placa = normalizar_spec(placa_madre.tipo_ram_soportado)
    if tipo_placa not in TIPOS_DDR_CONOCIDOS:
        return Hallazgo(
            'ddr',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede verificar la RAM porque el tipo DDR no es conocido '
            f'({_etiqueta(tipo_placa)}).',
        )
    tipo_ram = conocidos[0]
    if tipo_ram != tipo_placa:
        return Hallazgo(
            'ddr',
            ESTADO_INCOMPATIBLE,
            f'El tipo de RAM ({tipo_ram}) no coincide con el que admite la placa madre ({tipo_placa}).',
        )
    return None


def _evaluar_formato_ram(lineas, placa_madre):
    if not lineas and placa_madre is None:
        return None
    conocidos, desconocido = _formatos_ram(lineas)
    if len(conocidos) > 1:
        return Hallazgo(
            'formato_ram',
            ESTADO_INCOMPATIBLE,
            f"Hay RAM {' y '.join(conocidos)}. No se pueden mezclar esos formatos.",
        )
    if desconocido and (len(lineas) > 1 or placa_madre is not None):
        return Hallazgo(
            'formato_ram',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede comprobar el formato DIMM o SO-DIMM porque falta un dato. '
            'No se deduce del nombre.',
        )
    if not lineas or placa_madre is None:
        return Hallazgo(
            'formato_ram',
            ESTADO_INCOMPLETO,
            'Falta la memoria RAM o la placa madre para comprobar el formato DIMM o SO-DIMM.',
        )
    formato_placa = normalizar_spec(getattr(placa_madre, 'formato_ram_soportado', None))
    if formato_placa not in FORMATOS_RAM_CONOCIDOS:
        return Hallazgo(
            'formato_ram',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede comprobar el formato DIMM o SO-DIMM porque la placa no lo tiene registrado.',
        )
    formato_ram = conocidos[0]
    if formato_ram != formato_placa:
        return Hallazgo(
            'formato_ram',
            ESTADO_INCOMPATIBLE,
            f'El formato de la RAM ({formato_ram}) no coincide con el que admite la placa ({formato_placa}).',
        )
    return None


def _suma_modulos(lineas):
    conocidos = 0
    falta = False
    for linea in lineas:
        modulos = _entero_positivo(getattr(linea.producto, 'modulos_por_producto', None))
        if modulos is None:
            falta = True
        else:
            conocidos += linea.cantidad * modulos
    return conocidos, falta


def _evaluar_ranuras_ram(lineas, placa_madre):
    if not lineas and placa_madre is None:
        return None
    if not lineas or placa_madre is None:
        return Hallazgo(
            'ranuras_ram',
            ESTADO_INCOMPLETO,
            'Falta la memoria RAM o la placa madre para comprobar las ranuras.',
        )
    ranuras = _entero_positivo(getattr(placa_madre, 'ranuras_ram', None))
    if ranuras is None:
        return Hallazgo(
            'ranuras_ram',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede comprobar las ranuras porque la placa no tiene un número conocido.',
        )
    ocupadas, falta = _suma_modulos(lineas)
    if ocupadas > ranuras:
        return Hallazgo(
            'ranuras_ram',
            ESTADO_INCOMPATIBLE,
            f'Las RAM ocupan {ocupadas} ranuras y la placa tiene {ranuras}.',
        )
    if falta:
        return Hallazgo(
            'ranuras_ram',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede comprobar las ranuras porque falta cuántos módulos trae un producto. '
            'Un valor vacío no se deduce del nombre.',
        )
    return None


def _linea_inconsistente(linea):
    modulos = _entero_positivo(getattr(linea.producto, 'modulos_por_producto', None))
    por_modulo = _entero_positivo(getattr(linea.producto, 'capacidad_modulo_gb', None))
    total = _entero_positivo(getattr(linea.producto, 'capacidad_gb', None))
    if modulos is None or por_modulo is None or total is None:
        return False
    return modulos * por_modulo != total


def _suma_capacidad(lineas):
    """Suma cantidad × capacidad del producto. No vuelve a multiplicar por los módulos."""
    total = 0
    falta = False
    inconsistente = False
    for linea in lineas:
        if _linea_inconsistente(linea):
            inconsistente = True
            continue
        capacidad = _entero_positivo(getattr(linea.producto, 'capacidad_gb', None))
        if capacidad is None:
            falta = True
        else:
            total += linea.cantidad * capacidad
    return total, falta, inconsistente


def _evaluar_capacidad_ram(lineas, placa_madre):
    if not lineas and placa_madre is None:
        return None
    if not lineas or placa_madre is None:
        return Hallazgo(
            'capacidad_ram',
            ESTADO_INCOMPLETO,
            'Falta la memoria RAM o la placa madre para comprobar la capacidad máxima.',
        )
    maximo = _entero_positivo(getattr(placa_madre, 'capacidad_maxima_ram_gb', None))
    if maximo is None:
        return Hallazgo(
            'capacidad_ram',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede comprobar la capacidad máxima porque la placa no la tiene registrada.',
        )
    total, falta, inconsistente = _suma_capacidad(lineas)
    if total > maximo:
        return Hallazgo(
            'capacidad_ram',
            ESTADO_INCOMPATIBLE,
            f'La RAM suma {total} GB y la placa admite hasta {maximo} GB. '
            'El total usa la capacidad de cada producto, sin multiplicarla por los módulos.',
        )
    if inconsistente:
        return Hallazgo(
            'capacidad_ram',
            ESTADO_DATOS_INSUFICIENTES,
            'La capacidad del producto no coincide con módulos × capacidad por módulo. '
            'No se suman las dos cifras.',
        )
    if falta:
        return Hallazgo(
            'capacidad_ram',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede comprobar la capacidad porque falta la capacidad de un producto.',
        )
    return None


def _texto_ddr(piezas):
    conocidos, _desconocido = _tipos_ddr(_lineas_en(piezas))
    return f"DDR {conocidos[0]}"


def _texto_formato_ram(piezas):
    conocidos, _desconocido = _formatos_ram(_lineas_en(piezas))
    return f"formato {conocidos[0]}"


def _texto_ranuras_ram(piezas):
    ocupadas, _falta = _suma_modulos(_lineas_en(piezas))
    ranuras = _entero_positivo(piezas['placa_madre'].ranuras_ram)
    return f"{ocupadas} de {ranuras} ranuras"


def _texto_capacidad_ram(piezas):
    total, _falta, _inconsistente = _suma_capacidad(_lineas_en(piezas))
    maximo = _entero_positivo(piezas['placa_madre'].capacidad_maxima_ram_gb)
    return f"{total} GB de {maximo} GB"


def _evaluar_formato(placa_madre, gabinete):
    if placa_madre is None and gabinete is None:
        return None
    if placa_madre is None or gabinete is None:
        return Hallazgo(
            'formato',
            ESTADO_INCOMPLETO,
            'Falta la placa madre o el gabinete para comprobar el formato.',
        )

    formato_placa = normalizar_spec(placa_madre.formato)
    formato_gabinete = normalizar_spec(gabinete.formato_soporte)
    desconocidos = [
        valor for valor in (formato_placa, formato_gabinete)
        if valor not in FORMATOS_ORDENADOS
    ]
    if desconocidos:
        detalle = ', '.join(_etiqueta(valor) for valor in desconocidos)
        return Hallazgo(
            'formato',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede verificar el formato porque hay un valor desconocido '
            f'({detalle}). No se asume que quepa.',
        )
    if FORMATOS_ORDENADOS.index(formato_gabinete) < FORMATOS_ORDENADOS.index(formato_placa):
        return Hallazgo(
            'formato',
            ESTADO_INCOMPATIBLE,
            f'El gabinete ({formato_gabinete}) no admite el formato de la placa madre ({formato_placa}).',
        )
    return None


def _evaluar_largo(tarjeta_grafica, gabinete):
    """Solo compara milímetros de largo. No mira grosor, altura ni radiadores."""
    if tarjeta_grafica is None and gabinete is None:
        return None
    if tarjeta_grafica is None or gabinete is None:
        return Hallazgo(
            'largo',
            ESTADO_INCOMPLETO,
            MENSAJE_ELEGIR_GPU if tarjeta_grafica is None else MENSAJE_ELEGIR_GABINETE,
        )

    largo_gpu = _entero_positivo(getattr(tarjeta_grafica, 'largo_mm', None))
    largo_maximo = _entero_positivo(getattr(gabinete, 'largo_max_gpu_mm', None))
    faltan = []
    if largo_gpu is None:
        faltan.append('el largo de la GPU')
    if largo_maximo is None:
        faltan.append('el largo máximo del gabinete')
    if faltan:
        return Hallazgo(
            'largo',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede comprobar el largo porque falta '
            + ' y '.join(faltan)
            + '. Un valor vacío o 0 no se toma como medida conocida.',
        )
    if largo_gpu > largo_maximo:
        return Hallazgo(
            'largo',
            ESTADO_INCOMPATIBLE,
            f'La GPU mide {largo_gpu} mm y el gabinete admite hasta {largo_maximo} mm. '
            'Solo se comprueba el largo; no el grosor, la altura ni el espacio de radiadores.',
        )
    return None


def _largo_cumplido(piezas):
    gpu = piezas.get('tarjeta_grafica')
    gabinete = piezas.get('gabinete')
    return (
        gpu is not None
        and gabinete is not None
        and _evaluar_largo(gpu, gabinete) is None
    )


def _texto_largo_cumplido(piezas):
    largo_gpu = _entero_positivo(piezas['tarjeta_grafica'].largo_mm)
    largo_maximo = _entero_positivo(piezas['gabinete'].largo_max_gpu_mm)
    return (
        f'Cumple el límite de largo ({largo_gpu} mm de {largo_maximo} mm). '
        'Solo se comprueba el largo; no el grosor, la altura ni el espacio de radiadores.'
    )


def _sockets_conocidos_del_cooler(texto):
    tokens = [normalizar_spec(parte) for parte in str(texto or '').split(',')]
    return frozenset(token for token in tokens if token in SOCKETS_CONOCIDOS)


def _evaluar_cooler(refrigeracion, procesador, placa_madre):
    if refrigeracion is None:
        return []
    if procesador is None and placa_madre is None:
        return [Hallazgo(
            'cooler',
            ESTADO_INCOMPLETO,
            'Falta el procesador o la placa madre para comprobar los sockets del cooler.',
        )]

    sockets = _sockets_conocidos_del_cooler(getattr(refrigeracion, 'socket_compatibles', ''))
    hallazgos = []
    if procesador is not None:
        hallazgo = _cooler_contra_socket(sockets, procesador.socket, 'procesador')
        if hallazgo is not None:
            hallazgos.append(hallazgo)
    if placa_madre is not None:
        hallazgo = _cooler_contra_socket(sockets, placa_madre.socket_cpu, 'placa madre')
        if hallazgo is not None:
            hallazgos.append(hallazgo)
    return hallazgos


def _cooler_contra_socket(sockets_conocidos, socket_objetivo, nombre_pieza):
    objetivo = normalizar_spec(socket_objetivo)
    if objetivo not in SOCKETS_CONOCIDOS or not sockets_conocidos:
        return Hallazgo(
            'cooler',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede verificar el cooler porque falta un socket conocido. '
            'Un valor "Otro" o una lista vacía no se considera compatible.',
        )
    if objetivo not in sockets_conocidos:
        return Hallazgo(
            'cooler',
            ESTADO_INCOMPATIBLE,
            f'El cooler no admite el socket {objetivo} de {nombre_pieza}.',
        )
    return None


@dataclass(frozen=True)
class PoliticaPotencia:
    """Parámetros de la estimación de fuente. Ver el docstring del módulo."""

    reserva_otros_watts: int = 150
    margen: Decimal = Decimal('1.20')

    def __post_init__(self):
        if self.reserva_otros_watts < 0:
            raise ValueError('La reserva de potencia no puede ser negativa.')
        margen = Decimal(self.margen)
        if margen <= 0:
            raise ValueError('El margen de potencia debe ser mayor que cero.')
        object.__setattr__(self, 'margen', margen)

    def estimar(self, potencia_cpu, consumo_gpu, minimo_fuente_gpu=None):
        """Devuelve (estimacion, minimo_aplicado), ambos en watts enteros."""
        base = potencia_cpu + consumo_gpu + self.reserva_otros_watts
        estimacion = int((Decimal(base) * self.margen).to_integral_value(rounding=ROUND_CEILING))
        if minimo_fuente_gpu is None:
            return estimacion, estimacion
        return estimacion, max(estimacion, minimo_fuente_gpu)


POLITICA_POTENCIA_DEFECTO = PoliticaPotencia()


def politica_potencia():
    """Política activa: el ajuste del proyecto, o la de defecto si no existe."""
    from django.conf import settings

    cruda = getattr(settings, 'POLITICA_POTENCIA_ARMADO', None)
    if not cruda:
        return POLITICA_POTENCIA_DEFECTO
    return PoliticaPotencia(
        reserva_otros_watts=cruda['reserva_otros_watts'],
        margen=cruda['margen'],
    )


def _entero_positivo(valor):
    """Entero mayor que cero. NULL, 0 y decimales no son un dato conocido."""
    if isinstance(valor, bool) or valor is None or isinstance(valor, float):
        return None
    if isinstance(valor, Decimal):
        if valor != valor.to_integral_value():
            return None
        valor = int(valor)
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    if numero <= 0:
        return None
    return numero


_watts_conocido = _entero_positivo


def _potencia_cumplida(piezas, politica):
    return _evaluar_potencia(
        piezas.get('procesador'),
        piezas.get('tarjeta_grafica'),
        piezas.get('fuente_de_poder'),
        politica,
    ) is None and piezas.get('fuente_de_poder') is not None and piezas.get('procesador') is not None and piezas.get('tarjeta_grafica') is not None


def _texto_potencia_cumplida(piezas, politica):
    _estimacion, minimo = _cifras_potencia(piezas, politica)
    return (
        f'Cumple la estimación de potencia ({minimo} W). '
        'No se validan conectores ni dimensiones; no es una garantía eléctrica.'
    )


def _cifras_potencia(piezas, politica):
    cpu = _watts_conocido(getattr(piezas['procesador'], 'potencia_referencia_watts', None))
    gpu = _watts_conocido(getattr(piezas['tarjeta_grafica'], 'consumo_referencia_watts', None))
    minimo_gpu = _watts_conocido(getattr(piezas['tarjeta_grafica'], 'potencia_minima_fuente_watts', None))
    return politica.estimar(cpu, gpu, minimo_gpu)


def _evaluar_potencia(procesador, tarjeta_grafica, fuente_de_poder, politica):
    """Solo corre si hay una fuente. Sin ella, la regla no aplica al resto del armado."""
    if fuente_de_poder is None:
        return None
    if procesador is None or tarjeta_grafica is None:
        return Hallazgo(
            'potencia',
            ESTADO_INCOMPLETO,
            'Falta el procesador o la tarjeta gráfica para estimar la potencia de la fuente.',
        )

    cpu_w = _watts_conocido(getattr(procesador, 'potencia_referencia_watts', None))
    gpu_w = _watts_conocido(getattr(tarjeta_grafica, 'consumo_referencia_watts', None))
    fuente_w = _watts_conocido(getattr(fuente_de_poder, 'potencia_watts', None))
    faltan = []
    if cpu_w is None:
        faltan.append('la potencia de referencia del procesador')
    if gpu_w is None:
        faltan.append('el consumo de referencia de la GPU')
    if fuente_w is None:
        faltan.append('la potencia nominal de la fuente')
    if faltan:
        return Hallazgo(
            'potencia',
            ESTADO_DATOS_INSUFICIENTES,
            'No se puede estimar la potencia porque falta '
            + ' y '.join(faltan)
            + '. Un valor vacío o 0 no se toma como consumo conocido.',
        )

    estimacion, minimo = politica.estimar(
        cpu_w,
        gpu_w,
        _watts_conocido(getattr(tarjeta_grafica, 'potencia_minima_fuente_watts', None)),
    )
    if fuente_w < minimo:
        return Hallazgo(
            'potencia',
            ESTADO_INCOMPATIBLE,
            'Potencia insuficiente según la política de estimación: '
            f'la fuente ofrece {fuente_w} W y el mínimo estimado es {minimo} W '
            f'(cálculo con reserva y margen: {estimacion} W). '
            'Es una estimación, no una garantía eléctrica.',
        )
    return None
