"""Reglas de compatibilidad del armado de PC.

La función no declara compatible un socket "Otro" ni un formato que no esté
en la jerarquía conocida. Los espacios y las mayúsculas no cambian el resultado.
"""

import re
from dataclasses import dataclass, field


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
}

CLAVE_POR_CATEGORIA = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'memoria_ram': 'memoria_ram',
    'gabinete': 'gabinete',
    'refrigeracion': 'refrigeracion',
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
            return 'Coincide: ' + ', '.join(self.coincidencias)
        if self.estado == ESTADO_INCOMPLETO:
            return 'Selección incompleta'
        if self.estado == ESTADO_DATOS_INSUFICIENTES:
            return 'Datos insuficientes'
        return 'Incompatible'


def evaluar_candidato(categoria, candidato, procesador=None, placa_madre=None, memoria_ram=None, gabinete=None, refrigeracion=None):
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
    }
    piezas[CLAVE_POR_CATEGORIA[categoria]] = candidato
    resultado = validar_armado(**piezas)
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
        if _regla_puede_comprobarse(regla, piezas):
            estados.append(ESTADO_COMPATIBLE)
            coincidencias.append(_texto_coincidencia(regla, piezas))
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


def _regla_puede_comprobarse(regla, piezas):
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
    return False


def _texto_coincidencia(regla, piezas):
    if regla == 'socket':
        return f"Socket {normalizar_spec(piezas['procesador'].socket)}"
    if regla == 'ddr':
        return f"DDR {normalizar_spec(piezas['memoria_ram'].tipo_ddr)}"
    if regla == 'formato':
        return f"Formato {normalizar_spec(piezas['placa_madre'].formato)}"
    sockets = []
    if piezas['procesador'] is not None:
        sockets.append(normalizar_spec(piezas['procesador'].socket))
    if piezas['placa_madre'] is not None:
        socket_placa = normalizar_spec(piezas['placa_madre'].socket_cpu)
        if socket_placa not in sockets:
            sockets.append(socket_placa)
    return 'Cooler para ' + ', '.join(sockets)


def validar_armado(procesador=None, placa_madre=None, memoria_ram=None, gabinete=None, refrigeracion=None):
    """Valida las piezas presentes. Las que no participan en estas reglas se ignoran.

    Devuelve compatible solo si cada regla aplicable quedó resuelta con datos conocidos.
    Una pieza sin su par es selección incompleta y no se trata como conflicto.
    """
    candidatos = (
        _evaluar_socket(procesador, placa_madre),
        _evaluar_ddr(memoria_ram, placa_madre),
        _evaluar_formato(placa_madre, gabinete),
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
