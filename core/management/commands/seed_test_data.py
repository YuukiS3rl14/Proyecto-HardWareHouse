from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from core.seed_sql import load_sql_file


class Command(BaseCommand):
    help = (
        "Carga data/seed_test_data.sql. Borra catálogo, pedidos y carritos. "
        "No usarlo sobre una base con pedidos reales. Para corregir solo el "
        "catálogo demo, usa sincronizar_catalogo_demo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/seed_test_data.sql",
            help="Ruta al archivo .sql (relativa al directorio del proyecto).",
        )
        parser.add_argument(
            "--generate",
            action="store_true",
            help="Regenera el .sql con scripts/generate_seed_test_data.py antes de cargar.",
        )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError(
                "Este seed está pensado para PostgreSQL. Base actual: "
                f"{connection.vendor!r}."
            )

        if options["generate"]:
            self._run_generator()

        rel_path = options["file"]
        sql_path = Path(settings.BASE_DIR) / rel_path
        if not sql_path.is_file():
            raise CommandError(
                f"No existe {sql_path}. Genera el archivo con:\n"
                "  python scripts/generate_seed_test_data.py\n"
                "o ejecuta este comando con --generate."
            )

        self.stdout.write(f"Cargando {sql_path} ...")
        with transaction.atomic():
            with connection.cursor() as cursor:
                count = load_sql_file(sql_path, cursor)

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {count} sentencias SQL ejecutadas (regiones, comunas, "
                "proveedores y productos de prueba)."
            )
        )

    def _run_generator(self):
        import runpy

        script = Path(settings.BASE_DIR) / "scripts" / "generate_seed_test_data.py"
        if not script.is_file():
            raise CommandError(f"No se encontró el generador: {script}")
        self.stdout.write("Regenerando seed_test_data.sql ...")
        runpy.run_path(str(script), run_name="__main__")
