from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.productos_csv import generar_csv_bytes


class Command(BaseCommand):
    help = (
        'Genera un CSV solo con componentes del catálogo (para asistentes o integraciones). '
        'Por defecto escribe data/productos_componentes.csv'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            '-o',
            type=str,
            default='data/productos_componentes.csv',
            help='Ruta de salida relativa al proyecto.',
        )

    def handle(self, *args, **options):
        destino = Path(settings.BASE_DIR) / options['output']
        destino.parent.mkdir(parents=True, exist_ok=True)
        contenido = generar_csv_bytes()
        destino.write_bytes(contenido)
        total = max(0, contenido.decode('utf-8-sig').count('\n') - 1)
        self.stdout.write(
            self.style.SUCCESS(
                f'Exportados {total} productos en {destino}'
            )
        )
