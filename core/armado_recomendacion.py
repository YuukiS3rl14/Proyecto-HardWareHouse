"""
Recomendación de piezas para armado de PC (misma lógica que el armador web).

Usa evaluar_candidato() / validar_armado(); no modifica carrito ni stock.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from django.conf import settings

from core.compatibilidad import (
    ESTADO_DATOS_INSUFICIENTES,
    ESTADO_INCOMPATIBLE,
    LineaRam,
    evaluar_candidato,
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

RECOMENDACIONES_POR_CATEGORIA: dict[str, tuple] = {
    'procesador': ((Procesador, 'procesador', 'procesador'),),
    'placa_madre': ((PlacaMadre, 'placa_madre', 'placa_madre'),),
    'memoria_ram': ((MemoriaRam, 'memoria_ram', 'memoria_ram'),),
    'gabinete': ((Gabinete, 'gabinete', 'gabinete'),),
    'refrigeracion_cooler': ((RefrigeracionCooler, 'refrigeracion', 'refrigeracion'),),
    'tarjeta_grafica': ((TarjetaGrafica, 'tarjeta_grafica', 'tarjeta_grafica'),),
    'fuente_de_poder': ((FuenteDePoder, 'fuente_de_poder', 'fuente_de_poder'),),
    'almacenamiento': (
        (AlmacenamientoSSD, 'almacenamiento_ssd', 'almacenamiento_ssd'),
        (AlmacenamientoHDD, 'almacenamiento_hdd', 'almacenamiento_hdd'),
    ),
}

_ORDEN_ESTADO = {
    'compatible': 0,
    'incompleto': 1,
    'no_evaluada': 2,
    'datos_insuficientes': 3,
    'incompatible': 4,
}

ORDEN_ARMADO_CHAT = (
    'procesador',
    'placa_madre',
    'memoria_ram',
    'tarjeta_grafica',
    'almacenamiento',
    'gabinete',
    'refrigeracion_cooler',
    'fuente_de_poder',
)

_REPARTO_PRESUPUESTO = {
    'gaming': {
        'procesador': 0.22,
        'placa_madre': 0.14,
        'memoria_ram': 0.08,
        'tarjeta_grafica': 0.32,
        'almacenamiento': 0.08,
        'gabinete': 0.05,
        'refrigeracion_cooler': 0.04,
        'fuente_de_poder': 0.07,
    },
    'editing': {
        'procesador': 0.28,
        'placa_madre': 0.14,
        'memoria_ram': 0.12,
        'tarjeta_grafica': 0.22,
        'almacenamiento': 0.10,
        'gabinete': 0.04,
        'refrigeracion_cooler': 0.04,
        'fuente_de_poder': 0.06,
    },
    'office': {
        'procesador': 0.30,
        'placa_madre': 0.18,
        'memoria_ram': 0.12,
        'tarjeta_grafica': 0.05,
        'almacenamiento': 0.12,
        'gabinete': 0.06,
        'refrigeracion_cooler': 0.05,
        'fuente_de_poder': 0.12,
    },
    'general': {
        'procesador': 0.25,
        'placa_madre': 0.15,
        'memoria_ram': 0.10,
        'tarjeta_grafica': 0.20,
        'almacenamiento': 0.10,
        'gabinete': 0.05,
        'refrigeracion_cooler': 0.05,
        'fuente_de_poder': 0.10,
    },
}


def _orden_candidato(candidato: dict) -> tuple:
    precio = candidato['precio']
    if not isinstance(precio, Decimal):
        precio = Decimal(str(precio))
    return (
        0 if candidato['stock'] > 0 else 1,
        _ORDEN_ESTADO.get(candidato['estado'], 9),
        precio,
        candidato['nombre'],
    )


def candidatos_para_categoria(
    categoria: str,
    seleccion: dict,
    memorias: list[LineaRam] | None = None,
    almacenamientos: list | None = None,
) -> list[dict]:
    """Misma clasificación que POST /armado/recomendar/."""
    fuentes = RECOMENDACIONES_POR_CATEGORIA.get(categoria)
    if fuentes is None:
        return []

    candidatos: list[dict] = []
    for modelo, categoria_regla, model_name in fuentes:
        consulta = modelo.objects.select_related('proveedor')
        if not settings.DEBUG:
            consulta = sin_demo(consulta)
        for producto in consulta:
            evaluacion = evaluar_candidato(
                categoria_regla,
                producto,
                memorias_ram=memorias or None,
                almacenamientos=almacenamientos,
                **seleccion,
            )
            candidatos.append(
                {
                    'id': producto.id,
                    'model_name': model_name,
                    'nombre': producto.nombre,
                    'precio': producto.precio,
                    'stock': producto.stock,
                    'estado': evaluacion.estado,
                    'etiqueta': evaluacion.etiqueta,
                    'coincidencias': list(evaluacion.coincidencias),
                    'motivos': list(evaluacion.motivos),
                    'pendientes': list(evaluacion.pendientes),
                    'advertencias': list(evaluacion.advertencias),
                    'seleccionable': producto.stock > 0,
                    'producto': producto,
                }
            )
    candidatos.sort(key=_orden_candidato)
    return candidatos


def serializar_candidatos_api(candidatos: list[dict]) -> list[dict]:
    salida = []
    for c in candidatos:
        copia = {k: v for k, v in c.items() if k != 'producto'}
        copia['precio'] = str(copia['precio'])
        salida.append(copia)
    return salida


def _filtrar_cpu_preferencia(candidatos: list[dict], preferencia: str | None) -> list[dict]:
    if not preferencia:
        return candidatos
    pref = preferencia.lower()
    if pref == 'amd':
        return [
            c
            for c in candidatos
            if 'amd' in c['nombre'].lower() or 'ryzen' in c['nombre'].lower()
        ] or candidatos
    if pref == 'intel':
        return [c for c in candidatos if 'intel' in c['nombre'].lower()] or candidatos
    return candidatos


def _elegir(
    candidatos: list[dict],
    max_precio: Decimal,
    indice_economico: int = 0,
) -> dict | None:
    validos = [
        c
        for c in candidatos
        if c['stock'] > 0
        and c['estado'] not in (ESTADO_INCOMPATIBLE, ESTADO_DATOS_INSUFICIENTES)
        and c['precio'] <= max_precio
    ]
    if not validos:
        return None
    validos.sort(key=_orden_candidato)
    indice = min(indice_economico, len(validos) - 1)
    return validos[indice]


@dataclass
class ResultadoArmadoAutomatico:
    ok: bool
    presupuesto_clp: int
    proposito: str
    total_clp: int = 0
    componentes: list[dict] = field(default_factory=list)
    seleccion: dict = field(default_factory=dict)
    memorias: list[LineaRam] = field(default_factory=list)
    almacenamiento: list[dict] = field(default_factory=list)
    motivo_fallo: str | None = None
    advertencias: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    evaluacion_estado: str | None = None

    def armado_context(self) -> dict[str, Any]:
        return {
            'presupuesto_clp': self.presupuesto_clp,
            'proposito': self.proposito,
            'total_clp': self.total_clp,
            'componentes': self.componentes,
            'indice_economico': getattr(self, '_indice_economico', 0),
            'preferencia_cpu': getattr(self, '_preferencia_cpu', None),
        }


def construir_armado_automatico(
    presupuesto_clp: int,
    *,
    proposito: str = 'general',
    preferencia_cpu: str | None = None,
    indice_economico: int = 0,
    incluir_gpu: bool | None = None,
) -> ResultadoArmadoAutomatico:
    if presupuesto_clp < 150_000:
        return ResultadoArmadoAutomatico(
            ok=False,
            presupuesto_clp=presupuesto_clp,
            proposito=proposito,
            motivo_fallo='El presupuesto es muy bajo para armar un PC con piezas compatibles en catálogo.',
        )

    proposito = proposito if proposito in _REPARTO_PRESUPUESTO else 'general'
    reparto = _REPARTO_PRESUPUESTO[proposito]
    if incluir_gpu is None:
        incluir_gpu = proposito in ('gaming', 'editing', 'general')

    seleccion: dict = {}
    memorias: list[LineaRam] = []
    almacenamientos: list[dict] = []
    componentes_api: list[dict] = []
    total = Decimal('0')
    presupuesto = Decimal(presupuesto_clp)
    tradeoffs: list[str] = []

    for categoria in ORDEN_ARMADO_CHAT:
        if categoria == 'tarjeta_grafica' and not incluir_gpu:
            tradeoffs.append('Sin tarjeta gráfica dedicada: adecuado para ofimática si el CPU trae gráficos integrados.')
            continue

        restante_global = presupuesto - total
        techo_guia = presupuesto * Decimal(str(reparto.get(categoria, 0.12)))
        max_pieza = restante_global
        if max_pieza <= 0:
            return ResultadoArmadoAutomatico(
                ok=False,
                presupuesto_clp=presupuesto_clp,
                proposito=proposito,
                total_clp=int(total),
                motivo_fallo='No alcanza el presupuesto para completar el armado con piezas compatibles.',
                tradeoffs=tradeoffs,
            )

        candidatos = candidatos_para_categoria(
            categoria, seleccion, memorias or None, almacenamientos or None,
        )
        if categoria == 'procesador':
            candidatos = _filtrar_cpu_preferencia(candidatos, preferencia_cpu)

        elegido = _elegir(candidatos, max_pieza, indice_economico=indice_economico)
        if elegido is None and techo_guia < restante_global:
            elegido = _elegir(candidatos, techo_guia, indice_economico=indice_economico)
        if elegido is None and categoria == 'tarjeta_grafica':
            tradeoffs.append('No cupo una GPU compatible en el presupuesto; el resto del armado sigue siendo válido.')
            continue
        if elegido is None:
            return ResultadoArmadoAutomatico(
                ok=False,
                presupuesto_clp=presupuesto_clp,
                proposito=proposito,
                total_clp=int(total),
                componentes=componentes_api,
                motivo_fallo=(
                    f'No encontré pieza compatible en {categoria} dentro del presupuesto restante '
                    f'(${int(restante_global):,} CLP).'.replace(',', '.')
                ),
                tradeoffs=tradeoffs,
            )

        producto = elegido['producto']
        precio = producto.precio
        total += precio

        if categoria == 'memoria_ram':
            memorias = [LineaRam(producto, 1)]
            componentes_api.append({'tipo': 'memoria_ram', 'id': producto.id, 'cantidad': 1})
        elif categoria == 'almacenamiento':
            tipo = elegido['model_name']
            almacenamientos.append({'tipo': tipo, 'producto': producto, 'cantidad': 1})
            componentes_api.append({'tipo': tipo, 'id': producto.id, 'cantidad': 1})
        else:
            clave = {
                'procesador': 'procesador',
                'placa_madre': 'placa_madre',
                'gabinete': 'gabinete',
                'refrigeracion_cooler': 'refrigeracion',
                'tarjeta_grafica': 'tarjeta_grafica',
                'fuente_de_poder': 'fuente_de_poder',
            }[categoria]
            seleccion[clave] = producto
            componentes_api.append({'tipo': elegido['model_name'], 'id': producto.id, 'cantidad': 1})

    resultado = validar_armado(
        **seleccion,
        memorias_ram=memorias or None,
        almacenamientos=almacenamientos or None,
    )
    advertencias = list(resultado.advertencias)
    if resultado.estado in (ESTADO_INCOMPATIBLE, ESTADO_DATOS_INSUFICIENTES):
        return ResultadoArmadoAutomatico(
            ok=False,
            presupuesto_clp=presupuesto_clp,
            proposito=proposito,
            total_clp=int(total),
            componentes=componentes_api,
            motivo_fallo='La combinación elegida no pasa todas las reglas de compatibilidad.',
            advertencias=advertencias + list(resultado.motivos_de_rechazo),
            evaluacion_estado=resultado.estado,
            tradeoffs=tradeoffs,
        )

    if total > presupuesto:
        tradeoffs.append(
            f'El total (${int(total):,} CLP) supera levemente el presupuesto indicado; '
            'puedes pedir una versión más económica.'.replace(',', '.')
        )

    out = ResultadoArmadoAutomatico(
        ok=True,
        presupuesto_clp=presupuesto_clp,
        proposito=proposito,
        total_clp=int(total),
        componentes=componentes_api,
        seleccion=seleccion,
        memorias=memorias,
        almacenamiento=almacenamientos,
        advertencias=advertencias,
        tradeoffs=tradeoffs,
        evaluacion_estado=resultado.estado,
    )
    out._indice_economico = indice_economico
    out._preferencia_cpu = preferencia_cpu
    return out
