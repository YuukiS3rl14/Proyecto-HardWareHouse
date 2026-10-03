from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import (
    AlmacenamientoHDD,
    AlmacenamientoSSD,
    FuenteDePoder,
    Gabinete,
    MemoriaRam,
    PlacaMadre,
    Procesador,
    Proveedor,
    RefrigeracionCooler,
    TarjetaGrafica,
)

PROVEEDOR_DEMO = 'DEMO'
STOCK_DEMO = 10

CATALOGO_DEMO = (
    {
        'modelo': Procesador,
        'nombre': 'DEMO CPU AM4',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Socket AM4, 6 núcleos, 3.60 GHz.',
            'precio': Decimal('79990.00'),
            'stock': STOCK_DEMO,
            'socket': 'AM4',
            'nucleos': 6,
            'frecuencia_base': Decimal('3.60'),
        },
    },
    {
        'modelo': Procesador,
        'nombre': 'DEMO CPU AM5',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Socket AM5, 8 núcleos, 4.20 GHz.',
            'precio': Decimal('149990.00'),
            'stock': STOCK_DEMO,
            'socket': 'AM5',
            'nucleos': 8,
            'frecuencia_base': Decimal('4.20'),
        },
    },
    {
        'modelo': PlacaMadre,
        'nombre': 'DEMO Placa AM4 DDR4 ATX',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Socket AM4, RAM DDR4, formato ATX, chipset B550.',
            'precio': Decimal('89990.00'),
            'stock': STOCK_DEMO,
            'socket_cpu': 'AM4',
            'chipset': 'B550',
            'formato': 'ATX',
            'ranuras_ram': 4,
            'tipo_ram_soportado': 'DDR4',
        },
    },
    {
        'modelo': PlacaMadre,
        'nombre': 'DEMO Placa AM5 DDR5 ATX',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Socket AM5, RAM DDR5, formato ATX, chipset B650.',
            'precio': Decimal('129990.00'),
            'stock': STOCK_DEMO,
            'socket_cpu': 'AM5',
            'chipset': 'B650',
            'formato': 'ATX',
            'ranuras_ram': 4,
            'tipo_ram_soportado': 'DDR5',
        },
    },
    {
        'modelo': MemoriaRam,
        'nombre': 'DEMO RAM DDR4',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. 16 GB DDR4 a 3200 MHz.',
            'precio': Decimal('29990.00'),
            'stock': STOCK_DEMO,
            'capacidad_gb': 16,
            'tipo_ddr': 'DDR4',
            'velocidad_mhz': 3200,
        },
    },
    {
        'modelo': MemoriaRam,
        'nombre': 'DEMO RAM DDR5',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. 16 GB DDR5 a 5600 MHz.',
            'precio': Decimal('49990.00'),
            'stock': STOCK_DEMO,
            'capacidad_gb': 16,
            'tipo_ddr': 'DDR5',
            'velocidad_mhz': 5600,
        },
    },
    {
        'modelo': Gabinete,
        'nombre': 'DEMO Gabinete Mini-ITX',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Solo admite placas Mini-ITX.',
            'precio': Decimal('39990.00'),
            'stock': STOCK_DEMO,
            'formato_soporte': 'Mini-ITX',
            'ventiladores_incluidos': False,
            'material': 'Acero',
        },
    },
    {
        'modelo': Gabinete,
        'nombre': 'DEMO Gabinete ATX',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Admite placas hasta formato ATX.',
            'precio': Decimal('59990.00'),
            'stock': STOCK_DEMO,
            'formato_soporte': 'ATX',
            'ventiladores_incluidos': True,
            'material': 'Acero',
        },
    },
    {
        'modelo': RefrigeracionCooler,
        'nombre': 'DEMO Cooler AM4',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Cooler de aire compatible solo con socket AM4.',
            'precio': Decimal('19990.00'),
            'stock': STOCK_DEMO,
            'tipo': 'Aire',
            'socket_compatibles': 'AM4',
        },
    },
    {
        'modelo': RefrigeracionCooler,
        'nombre': 'DEMO Cooler AM5',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Cooler de aire compatible solo con socket AM5.',
            'precio': Decimal('24990.00'),
            'stock': STOCK_DEMO,
            'tipo': 'Aire',
            'socket_compatibles': 'AM5',
        },
    },
    {
        'modelo': AlmacenamientoSSD,
        'nombre': 'DEMO SSD NVMe 1TB',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. SSD de 1000 GB, NVMe PCIe 4.0, formato M.2 2280.',
            'precio': Decimal('54990.00'),
            'stock': STOCK_DEMO,
            'capacidad_gb': 1000,
            'interfaz': 'NVMe PCIe 4.0',
            'formato': 'M.2 2280',
        },
    },
    {
        'modelo': AlmacenamientoHDD,
        'nombre': 'DEMO HDD 2TB',
        'campos': {
            'descripcion': 'Pieza ficticia de demostración. Disco duro de 2000 GB, 7200 RPM y 256 MB de caché.',
            'precio': Decimal('44990.00'),
            'stock': STOCK_DEMO,
            'capacidad_gb': 2000,
            'velocidad_rpm': 7200,
            'cache_mb': 256,
        },
    },
)

# Watts ficticios. Solo los escribe la opción --potencia, y solo en estos nombres.
POTENCIA_CPU_DEMO = {
    'DEMO CPU AM4': 65,
    'DEMO CPU AM5': 120,
}

GPU_DEMO = {
    'nombre': 'DEMO GPU',
    'consumo_referencia_watts': 220,
    'potencia_minima_fuente_watts': 650,
    'campos': {
        'descripcion': (
            'Pieza ficticia de demostración. Consumo de referencia 220 W y fuente mínima '
            'recomendada 650 W. Esas cifras no son un TDP ni un consumo máximo.'
        ),
        'precio': Decimal('199990.00'),
        'stock': STOCK_DEMO,
        'vram_gb': 8,
        'tipo_memoria': 'GDDR6',
        'interfaz': 'PCIe 4.0',
    },
}

FUENTES_DEMO = (
    {
        'nombre': 'DEMO Fuente 550W',
        'potencia_watts': 550,
        'campos': {
            'descripcion': (
                'Pieza ficticia de demostración. 550 W nominales: queda bajo el mínimo '
                'estimado con DEMO CPU AM5 y DEMO GPU usando la política por defecto.'
            ),
            'precio': Decimal('39990.00'),
            'stock': STOCK_DEMO,
            'certificacion': '80+ Bronze',
            'modular': False,
        },
    },
    {
        'nombre': 'DEMO Fuente 750W',
        'potencia_watts': 750,
        'campos': {
            'descripcion': (
                'Pieza ficticia de demostración. 750 W nominales: alcanza la estimación '
                'de potencia con DEMO CPU AM5 y DEMO GPU. No valida conectores ni dimensiones.'
            ),
            'precio': Decimal('69990.00'),
            'stock': STOCK_DEMO,
            'certificacion': '80+ Gold',
            'modular': True,
        },
    },
)

# Datos ficticios de RAM. Solo los escribe --ram, y solo en estos nombres.
# capacidad_gb es la del producto vendido. En el kit ya incluye los dos módulos,
# así que no se vuelve a multiplicar por modulos_por_producto.
RAM_DEMO = (
    {
        'nombre': 'DEMO RAM módulo DDR5 16GB',
        'campos': {
            'descripcion': (
                'Pieza ficticia de demostración. Un módulo DIMM de 16 GB DDR5 a 5600 MHz. '
                'La capacidad del producto es 16 GB y trae 1 módulo.'
            ),
            'precio': Decimal('39990.00'),
            'stock': STOCK_DEMO,
            'capacidad_gb': 16,
            'tipo_ddr': 'DDR5',
            'velocidad_mhz': 5600,
            'modulos_por_producto': 1,
            'capacidad_modulo_gb': 16,
            'formato_ram': 'DIMM',
        },
    },
    {
        'nombre': 'DEMO RAM kit DDR5 32GB',
        'campos': {
            'descripcion': (
                'Pieza ficticia de demostración. Kit DIMM de dos módulos DDR5 a 5600 MHz. '
                'La capacidad del producto es 32 GB; cada módulo es de 16 GB. '
                'No se suman 32 y 16.'
            ),
            'precio': Decimal('69990.00'),
            'stock': STOCK_DEMO,
            'capacidad_gb': 32,
            'tipo_ddr': 'DDR5',
            'velocidad_mhz': 5600,
            'modulos_por_producto': 2,
            'capacidad_modulo_gb': 16,
            'formato_ram': 'DIMM',
        },
    },
    {
        'nombre': 'DEMO RAM SO-DIMM DDR5 16GB',
        'campos': {
            'descripcion': (
                'Pieza ficticia de demostración. Un módulo SO-DIMM de 16 GB DDR5. '
                'No cabe en una placa que solo admite DIMM.'
            ),
            'precio': Decimal('42990.00'),
            'stock': STOCK_DEMO,
            'capacidad_gb': 16,
            'tipo_ddr': 'DDR5',
            'velocidad_mhz': 5600,
            'modulos_por_producto': 1,
            'capacidad_modulo_gb': 16,
            'formato_ram': 'SO-DIMM',
        },
    },
)
PLACAS_RAM_DEMO = {
    'DEMO Placa AM4 DDR4 ATX': {
        'formato_ram_soportado': 'DIMM',
        'capacidad_maxima_ram_gb': 128,
    },
    'DEMO Placa AM5 DDR5 ATX': {
        'formato_ram_soportado': 'DIMM',
        'capacidad_maxima_ram_gb': 48,
    },
}

# Milímetros ficticios. Solo los escribe --dimensiones, y solo en estos nombres.
LARGO_GABINETE_DEMO = {
    'DEMO Gabinete Mini-ITX': 200,
    'DEMO Gabinete ATX': 320,
}
LARGO_GPU_DEMO = {
    'DEMO GPU': 280,
}
GPUS_LARGO_DEMO = (
    {
        'nombre': 'DEMO GPU 280mm',
        'largo_mm': 280,
        'campos': {
            'descripcion': (
                'Pieza ficticia de demostración. Largo 280 mm: cabe en DEMO Gabinete ATX (320 mm) '
                'y excede DEMO Gabinete Mini-ITX (200 mm). No describe grosor ni altura.'
            ),
            'precio': Decimal('179990.00'),
            'stock': STOCK_DEMO,
            'vram_gb': 8,
            'tipo_memoria': 'GDDR6',
            'interfaz': 'PCIe 4.0',
        },
    },
    {
        'nombre': 'DEMO GPU 321mm',
        'largo_mm': 321,
        'campos': {
            'descripcion': (
                'Pieza ficticia de demostración. Largo 321 mm: excede por 1 mm el máximo de '
                'DEMO Gabinete ATX (320 mm). No describe grosor ni altura.'
            ),
            'precio': Decimal('219990.00'),
            'stock': STOCK_DEMO,
            'vram_gb': 8,
            'tipo_memoria': 'GDDR6',
            'interfaz': 'PCIe 4.0',
        },
    },
)


class Command(BaseCommand):
    help = 'Carga piezas DEMO para probar el armador. No modifica productos que ya existen.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--potencia',
            action='store_true',
            help=(
                'Escribe la potencia de referencia solo en las piezas DEMO de este comando '
                'y crea la GPU y las dos fuentes de prueba si faltan.'
            ),
        )
        parser.add_argument(
            '--dimensiones',
            action='store_true',
            help=(
                'Escribe el largo de GPU solo en las piezas DEMO de este comando '
                'y crea ejemplos que caben y que exceden el límite.'
            ),
        )
        parser.add_argument(
            '--ram',
            action='store_true',
            help=(
                'Crea un módulo individual y un kit de dos módulos, más un SO-DIMM, '
                'y escribe formato y capacidad máxima solo en las placas DEMO de este comando.'
            ),
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('cargar_demo_armado solo puede ejecutarse con DEBUG=True.')

        self._crear_faltantes_del_catalogo()
        if options['potencia']:
            self._aplicar_potencia_demo()
        if options['dimensiones']:
            self._aplicar_dimensiones_demo()
        if options['ram']:
            self._aplicar_ram_demo()

    def _crear_faltantes_del_catalogo(self):
        faltantes = [
            item for item in CATALOGO_DEMO
            if not item['modelo'].objects.filter(nombre=item['nombre']).exists()
        ]
        if not faltantes:
            self.stdout.write(self.style.SUCCESS(
                'Catálogo DEMO: todos los productos ya existen. No se creó ni se modificó ninguno de ellos.'
            ))
            return

        with transaction.atomic():
            proveedor, proveedor_nuevo = Proveedor.objects.get_or_create(nombre=PROVEEDOR_DEMO)
            creados = []
            for item in faltantes:
                producto = item['modelo'](
                    proveedor=proveedor,
                    nombre=item['nombre'],
                    **item['campos'],
                )
                producto.full_clean()
                producto.save()
                creados.append(item['nombre'])

        if proveedor_nuevo:
            self.stdout.write(f'Proveedor creado: {PROVEEDOR_DEMO}')
        else:
            self.stdout.write(f'Proveedor existente, sin cambios: {PROVEEDOR_DEMO}')
        for nombre in creados:
            self.stdout.write(f'Creado: {nombre}')
        self.stdout.write(self.style.SUCCESS(
            f'Listo. Creados: {len(creados)}. Omitidos porque ya existían: {len(CATALOGO_DEMO) - len(creados)}.'
        ))

    def _aplicar_potencia_demo(self):
        """Completa watts solo en nombres DEMO de este comando. No toca otros productos."""
        with transaction.atomic():
            proveedor, _creado = Proveedor.objects.get_or_create(nombre=PROVEEDOR_DEMO)
            for nombre, watts in POTENCIA_CPU_DEMO.items():
                actualizados = Procesador.objects.filter(nombre=nombre).update(
                    potencia_referencia_watts=watts,
                )
                if actualizados:
                    self.stdout.write(f'Potencia de referencia en {nombre}: {watts} W')
                else:
                    self.stdout.write(self.style.WARNING(
                        f'No existe {nombre}; no se creó un procesador fuera del catálogo.'
                    ))

            gpu = TarjetaGrafica.objects.filter(nombre=GPU_DEMO['nombre']).first()
            if gpu is None:
                gpu = TarjetaGrafica(
                    proveedor=proveedor,
                    nombre=GPU_DEMO['nombre'],
                    consumo_referencia_watts=GPU_DEMO['consumo_referencia_watts'],
                    potencia_minima_fuente_watts=GPU_DEMO['potencia_minima_fuente_watts'],
                    **GPU_DEMO['campos'],
                )
                gpu.full_clean()
                gpu.save()
                self.stdout.write(f"Creada: {GPU_DEMO['nombre']}")
            else:
                TarjetaGrafica.objects.filter(pk=gpu.pk).update(
                    consumo_referencia_watts=GPU_DEMO['consumo_referencia_watts'],
                    potencia_minima_fuente_watts=GPU_DEMO['potencia_minima_fuente_watts'],
                )
                self.stdout.write(
                    f"Potencia de referencia en {GPU_DEMO['nombre']}: "
                    f"{GPU_DEMO['consumo_referencia_watts']} W, "
                    f"fuente mínima {GPU_DEMO['potencia_minima_fuente_watts']} W"
                )

            for item in FUENTES_DEMO:
                fuente = FuenteDePoder.objects.filter(nombre=item['nombre']).first()
                if fuente is None:
                    fuente = FuenteDePoder(
                        proveedor=proveedor,
                        nombre=item['nombre'],
                        potencia_watts=item['potencia_watts'],
                        **item['campos'],
                    )
                    fuente.full_clean()
                    fuente.save()
                    self.stdout.write(f"Creada: {item['nombre']}")
                else:
                    FuenteDePoder.objects.filter(pk=fuente.pk).update(
                        potencia_watts=item['potencia_watts'],
                    )
                    self.stdout.write(f"Potencia nominal en {item['nombre']}: {item['potencia_watts']} W")

        self.stdout.write(self.style.SUCCESS(
            'Potencia DEMO aplicada solo a los nombres ficticios de este comando.'
        ))

    def _aplicar_dimensiones_demo(self):
        """Completa el largo solo en nombres DEMO de este comando."""
        with transaction.atomic():
            proveedor, _creado = Proveedor.objects.get_or_create(nombre=PROVEEDOR_DEMO)
            for nombre, largo in LARGO_GABINETE_DEMO.items():
                actualizados = Gabinete.objects.filter(nombre=nombre).update(largo_max_gpu_mm=largo)
                if actualizados:
                    self.stdout.write(f'Largo máximo de GPU en {nombre}: {largo} mm')
                else:
                    self.stdout.write(self.style.WARNING(
                        f'No existe {nombre}; no se creó un gabinete fuera del catálogo.'
                    ))
            for nombre, largo in LARGO_GPU_DEMO.items():
                actualizados = TarjetaGrafica.objects.filter(nombre=nombre).update(largo_mm=largo)
                if actualizados:
                    self.stdout.write(f'Largo en {nombre}: {largo} mm')
            for item in GPUS_LARGO_DEMO:
                gpu = TarjetaGrafica.objects.filter(nombre=item['nombre']).first()
                if gpu is None:
                    gpu = TarjetaGrafica(
                        proveedor=proveedor,
                        nombre=item['nombre'],
                        largo_mm=item['largo_mm'],
                        **item['campos'],
                    )
                    gpu.full_clean()
                    gpu.save()
                    self.stdout.write(f"Creada: {item['nombre']}")
                else:
                    TarjetaGrafica.objects.filter(pk=gpu.pk).update(largo_mm=item['largo_mm'])
                    self.stdout.write(f"Largo en {item['nombre']}: {item['largo_mm']} mm")
        self.stdout.write(self.style.SUCCESS(
            'Dimensiones DEMO aplicadas solo a los nombres ficticios de este comando.'
        ))

    def _aplicar_ram_demo(self):
        """Completa módulos, formato y capacidad máxima solo en los nombres de esta opción."""
        with transaction.atomic():
            proveedor, _creado = Proveedor.objects.get_or_create(nombre=PROVEEDOR_DEMO)
            for item in RAM_DEMO:
                ram = MemoriaRam.objects.filter(nombre=item['nombre']).first()
                datos = {
                    'modulos_por_producto': item['campos']['modulos_por_producto'],
                    'capacidad_modulo_gb': item['campos']['capacidad_modulo_gb'],
                    'formato_ram': item['campos']['formato_ram'],
                    'capacidad_gb': item['campos']['capacidad_gb'],
                }
                if ram is None:
                    ram = MemoriaRam(
                        proveedor=proveedor,
                        nombre=item['nombre'],
                        **item['campos'],
                    )
                    ram.full_clean()
                    ram.save()
                    self.stdout.write(f"Creada: {item['nombre']}")
                else:
                    MemoriaRam.objects.filter(pk=ram.pk).update(**datos)
                    self.stdout.write(
                        f"{item['nombre']}: {datos['modulos_por_producto']} módulos, "
                        f"{datos['capacidad_gb']} GB en total, formato {datos['formato_ram']}"
                    )
            for nombre, campos in PLACAS_RAM_DEMO.items():
                actualizados = PlacaMadre.objects.filter(nombre=nombre).update(**campos)
                if actualizados:
                    self.stdout.write(
                        f"{nombre}: formato {campos['formato_ram_soportado']}, "
                        f"máximo {campos['capacidad_maxima_ram_gb']} GB"
                    )
                else:
                    self.stdout.write(self.style.WARNING(
                        f'No existe {nombre}; no se creó una placa fuera del catálogo.'
                    ))
        self.stdout.write(self.style.SUCCESS(
            'RAM DEMO aplicada solo a los nombres ficticios de este comando.'
        ))
