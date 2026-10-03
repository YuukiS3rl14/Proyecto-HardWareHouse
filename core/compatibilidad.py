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
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_CEILING


SOCKETS_CONOCIDOS = frozenset({'AM4', 'AM5', 'LGA1200', 'LGA1700'})
TIPOS_DDR_CONOCIDOS = frozenset({'DDR3', 'DDR4', 'DDR5'})
FORMATOS_ORDENADOS = ('MINI-ITX', 'MICRO-ATX', 'ATX')

ESTADO_COMPATIBLE = 'compatible'
ESTADO_INCOMPATIBLE = 'incompatible'
ESTADO_DATOS_INSUFICIENTES = 'datos_insuficientes'
ESTADO_INCOMPLETO = 'incompleto'
ESTADO_NO_EVALUADA = 'no_evaluada'
MENSAJE_NO_EVALUADA = 'Compatibilidad no evaluada'

REGLAS_POR_CATEGORIA = {
    'procesador': ('socket',),
    'placa_madre': ('socket', 'ddr', 'formato'),
    'memoria_ram': ('ddr',),
    'gabinete': ('formato',),
    'refrigeracion': ('cooler',),
    'fuente_de_poder': ('potencia',),
}

CLAVE_POR_CATEGORIA = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'memoria_ram': 'memoria_ram',
    'gabinete': 'gabinete',
    'refrigeracion': 'refrigeracion',
    'fuente_de_poder': 'fuente_de_poder',
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


@dataclass
class ResultadoCompatibilidad:
    hallazgos: list = field(default_factory=list)

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

    @property
    def etiqueta(self):
        if self.estado == ESTADO_NO_EVALUADA:
            return MENSAJE_NO_EVALUADA
        if self.estado == ESTADO_COMPATIBLE:
            if (
                len(self.coincidencias) == 1
                and self.coincidencias[0].startswith('Cumple la estimación de potencia')
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
    piezas[CLAVE_POR_CATEGORIA[categoria]] = candidato
    politica_activa = politica or politica_potencia()
    resultado = validar_armado(**piezas, politica=politica_activa)
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

    return EvaluacionCandidato(
        _estado_de_candidato(estados),
        tuple(coincidencias),
        tuple(motivos),
        tuple(pendientes),
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
        return piezas['memoria_ram'] is not None and piezas['placa_madre'] is not None
    if regla == 'formato':
        return piezas['placa_madre'] is not None and piezas['gabinete'] is not None
    if regla == 'cooler':
        return piezas['refrigeracion'] is not None and (
            piezas['procesador'] is not None or piezas['placa_madre'] is not None
        )
    if regla == 'potencia':
        return _potencia_cumplida(piezas, politica)
    return False


def _texto_coincidencia(regla, piezas, politica):
    if regla == 'socket':
        return f"Socket {normalizar_spec(piezas['procesador'].socket)}"
    if regla == 'ddr':
        return f"DDR {normalizar_spec(piezas['memoria_ram'].tipo_ddr)}"
    if regla == 'formato':
        return f"Formato {normalizar_spec(piezas['placa_madre'].formato)}"
    if regla == 'potencia':
        return _texto_potencia_cumplida(piezas, politica)
    sockets = []
    if piezas['procesador'] is not None:
        sockets.append(normalizar_spec(piezas['procesador'].socket))
    if piezas['placa_madre'] is not None:
        socket_placa = normalizar_spec(piezas['placa_madre'].socket_cpu)
        if socket_placa not in sockets:
            sockets.append(socket_placa)
    return 'Cooler para ' + ', '.join(sockets)


def validar_armado(
    procesador=None,
    placa_madre=None,
    memoria_ram=None,
    gabinete=None,
    refrigeracion=None,
    tarjeta_grafica=None,
    fuente_de_poder=None,
    politica=None,
):
    """Valida las piezas presentes. Las que no participan en estas reglas se ignoran.

    Devuelve compatible solo si cada regla aplicable quedó resuelta con datos conocidos.
    Una pieza sin su par es selección incompleta y no se trata como conflicto.
    """
    candidatos = (
        _evaluar_socket(procesador, placa_madre),
        _evaluar_ddr(memoria_ram, placa_madre),
        _evaluar_formato(placa_madre, gabinete),
        _evaluar_potencia(procesador, tarjeta_grafica, fuente_de_poder, politica or politica_potencia()),
    )
    hallazgos = [hallazgo for hallazgo in candidatos if hallazgo is not None]
    hallazgos.extend(_evaluar_cooler(refrigeracion, procesador, placa_madre))
    return ResultadoCompatibilidad(hallazgos)


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


def _evaluar_ddr(memoria_ram, placa_madre):
    if memoria_ram is None and placa_madre is None:
        return None
    if memoria_ram is None or placa_madre is None:
        return Hallazgo(
            'ddr',
            ESTADO_INCOMPLETO,
            'Falta la memoria RAM o la placa madre para comprobar el tipo DDR.',
        )

    tipo_ram = normalizar_spec(memoria_ram.tipo_ddr)
    tipo_placa = normalizar_spec(placa_madre.tipo_ram_soportado)
    desconocidos = [valor for valor in (tipo_ram, tipo_placa) if valor not in TIPOS_DDR_CONOCIDOS]
    if desconocidos:
        detalle = ', '.join(_etiqueta(valor) for valor in desconocidos)
        return Hallazgo(
            'ddr',
            ESTADO_DATOS_INSUFICIENTES,
            f'No se puede verificar la RAM porque el tipo DDR no es conocido ({detalle}).',
        )
    if tipo_ram != tipo_placa:
        return Hallazgo(
            'ddr',
            ESTADO_INCOMPATIBLE,
            f'El tipo de RAM ({tipo_ram}) no coincide con el que admite la placa madre ({tipo_placa}).',
        )
    return None


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


def _watts_conocido(valor):
    """Un watt conocido es un entero mayor que cero. NULL y 0 no son dato."""
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
