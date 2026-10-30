"""Registro único de modelos de producto del catálogo (ORM Django)."""
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
    Ventilador,
)

# (Modelo ORM, nombre usado en URLs y APIs)
CATALOGO_MODELOS: list[tuple[type, str]] = [
    (Procesador, 'procesador'),
    (TarjetaGrafica, 'tarjeta_grafica'),
    (MemoriaRam, 'memoria_ram'),
    (PlacaMadre, 'placa_madre'),
    (AlmacenamientoSSD, 'almacenamiento_ssd'),
    (AlmacenamientoHDD, 'almacenamiento_hdd'),
    (Gabinete, 'gabinete'),
    (FuenteDePoder, 'fuente_de_poder'),
    (RefrigeracionCooler, 'refrigeracion'),
    (Ventilador, 'ventilador'),
]

MODEL_BY_API_NAME = {name: model for model, name in CATALOGO_MODELOS}

_MODEL_NAME_OVERRIDES = {
    RefrigeracionCooler: 'refrigeracion',
}


def model_name_for(model_class: type) -> str:
    if model_class in _MODEL_NAME_OVERRIDES:
        return _MODEL_NAME_OVERRIDES[model_class]
    name = model_class._meta.model_name
    return (
        name.replace('tarjetagrafica', 'tarjeta_grafica')
        .replace('memoriaram', 'memoria_ram')
        .replace('placamadre', 'placa_madre')
        .replace('almacenamientossd', 'almacenamiento_ssd')
        .replace('almacenamientohdd', 'almacenamiento_hdd')
        .replace('fuentedepoder', 'fuente_de_poder')
        .replace('refrigeracioncooler', 'refrigeracion')
    )


def categorias_disponibles() -> list[str]:
    return sorted(
        {model._meta.get_field('categoria').default for model, _ in CATALOGO_MODELOS}
    )
