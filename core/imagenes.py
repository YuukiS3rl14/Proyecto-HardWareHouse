from django.templatetags.static import static

ARCHIVOS_CATEGORIA = {
    'CPU': 'core/img/categorias/01_CPU.webp',
    'Tarjeta Gráfica': 'core/img/categorias/02_GPU.webp',
    'Memoria RAM': 'core/img/categorias/03_RAM.webp',
    'Placa Madre': 'core/img/categorias/04_Placa_madre.webp',
    'SSD': 'core/img/categorias/05_SSD.webp',
    'Disco Duro HDD': 'core/img/categorias/06_HDD.webp',
    'Fuente de Poder': 'core/img/categorias/07_Fuente_de_poder.webp',
    'Gabinete': 'core/img/categorias/08_Gabinete.webp',
    'Refrigeración': 'core/img/categorias/09_Refrigeracion.webp',
    'Ventilador': 'core/img/categorias/10_Ventilador.webp',
}
ARCHIVO_GENERICO = 'core/img/categorias/11_Componentes_PC_generico.webp'

CLAVES_ARMADO = {
    'procesador': 'CPU',
    'tarjeta_grafica': 'Tarjeta Gráfica',
    'memoria_ram': 'Memoria RAM',
    'placa_madre': 'Placa Madre',
    'almacenamiento': 'SSD',
    'almacenamiento_ssd': 'SSD',
    'almacenamiento_hdd': 'Disco Duro HDD',
    'gabinete': 'Gabinete',
    'fuente_de_poder': 'Fuente de Poder',
    'refrigeracion': 'Refrigeración',
    'refrigeracion_cooler': 'Refrigeración',
    'ventilador': 'Ventilador',
}


def archivo_imagen_categoria(categoria):
    return ARCHIVOS_CATEGORIA.get(categoria or '', ARCHIVO_GENERICO)


def url_imagen_producto(producto):
    """Devuelve la foto subida o, si no hay, el estático de la categoría."""
    if producto is None:
        return static(ARCHIVO_GENERICO)
    imagen = getattr(producto, 'imagen', None)
    if imagen:
        try:
            return imagen.url
        except ValueError:
            pass
    return static(archivo_imagen_categoria(getattr(producto, 'categoria', None)))


def urls_imagen_armado():
    return {
        clave: static(archivo_imagen_categoria(categoria))
        for clave, categoria in CLAVES_ARMADO.items()
    }
