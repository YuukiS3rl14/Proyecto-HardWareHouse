from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.catalogo_migracion import (
    CatalogoMigracionError,
    destino_legible,
    escribir_exportacion,
)


class Command(BaseCommand):
    help = (
        'Exporta solo el catálogo a un JSON fuera del repositorio. '
        'No incluye IDs, usuarios, pedidos, boletas, IPN, carritos ni sesiones.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--salida',
            required=True,
            help='Ruta del JSON, en una carpeta que no pertenezca al proyecto.',
        )

    def handle(self, *args, **options):
        destino = _ruta_fuera_del_repo(Path(options['salida']))
        self.stdout.write(destino_legible())
        try:
            documento = escribir_exportacion(destino)
        except CatalogoMigracionError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            f"Proveedores: {len(documento['proveedores'])}. "
            f"Productos: {len(documento['productos'])}."
        )
        self.stdout.write(self.style.SUCCESS(f'Exportación escrita fuera del repositorio: {destino.name}'))


def _ruta_fuera_del_repo(destino: Path) -> Path:
    raiz = Path(settings.BASE_DIR).resolve()
    final = destino.expanduser()
    if not final.is_absolute():
        raise CommandError('La ruta de salida tiene que ser absoluta y estar fuera del proyecto.')
    final = final.resolve()
    try:
        final.relative_to(raiz)
    except ValueError:
        if not final.parent.is_dir():
            raise CommandError('La carpeta de destino no existe.')
        return final
    raise CommandError(
        'La exportación no puede guardarse dentro del proyecto. '
        'Usa una carpeta fuera del repositorio para que el archivo no entre en Git.'
    )
