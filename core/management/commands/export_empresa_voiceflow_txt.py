from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.empresa_conocimiento import EMPRESA_CONOCIMIENTO_VOICEFLOW


class Command(BaseCommand):
    help = (
        'Genera data/hardwarehouse_empresa_voiceflow.txt con información '
        'institucional para Voiceflow (sobre nosotros, FAQ, políticas).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            '-o',
            type=str,
            default='data/hardwarehouse_empresa_voiceflow.txt',
            help='Ruta de salida relativa al proyecto.',
        )

    def handle(self, *args, **options):
        destino = Path(settings.BASE_DIR) / options['output']
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(EMPRESA_CONOCIMIENTO_VOICEFLOW + '\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Archivo generado: {destino}'))
