from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.demo_catalog import validar_catalogo
from core.demo_catalog_io import comparar_fuentes, parse_csv, parse_product_inserts
from core.demo_catalog_sync import CatalogoDemoError, sincronizar_filas


class Command(BaseCommand):
    help = (
        "Sincroniza solo los productos demo desde data/seed_test_data.sql y "
        "data/productos_componentes.csv. No borra pedidos ni pisa registros reales. "
        "Los precios y el stock de la fuente son sintéticos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra el resumen sin escribir en la base.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica los cambios en una transacción.",
        )
        parser.add_argument("--sql", default="data/seed_test_data.sql")
        parser.add_argument("--csv", default="data/productos_componentes.csv")

    def handle(self, *args, **options):
        if options["dry_run"] == options["apply"]:
            raise CommandError("Indica exactamente una opción: --dry-run o --apply.")

        sql_path = Path(options["sql"])
        csv_path = Path(options["csv"])
        if not sql_path.is_absolute():
            sql_path = Path(settings.BASE_DIR) / sql_path
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path
        if not sql_path.is_file() or not csv_path.is_file():
            raise CommandError(f"No están las fuentes {sql_path} y {csv_path}.")

        try:
            filas_sql = parse_product_inserts(sql_path.read_text(encoding="utf-8"))
            filas_csv = parse_csv(csv_path.read_text(encoding="utf-8-sig"))
            validar_catalogo(filas_sql)
            comparar_fuentes(filas_sql, filas_csv)
            resumen = sincronizar_filas(filas_sql, apply=options["apply"])
        except (CatalogoDemoError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        self._imprimir(resumen)

    def _imprimir(self, resumen: dict) -> None:
        modo = "apply" if resumen["apply"] else "dry-run"
        verbo = "creados" if resumen["apply"] else "por crear"
        self.stdout.write(f"Base: {resumen['base']} @ {resumen['host']}")
        self.stdout.write(f"Modo: {modo}")
        self.stdout.write(
            f"Proveedores {verbo}: {len(resumen['proveedores_creados'])}"
        )
        if resumen["proveedores_creados"]:
            self.stdout.write(", ".join(resumen["proveedores_creados"]))
        self.stdout.write(f"Insertados: {resumen['insertados']}")
        self.stdout.write(f"Actualizados: {resumen['actualizados']}")
        self.stdout.write(f"Sin cambios: {resumen['sin_cambios']}")
        self.stdout.write(f"Omitidos por ser registros reales: {len(resumen['omitidos'])}")
        for item in resumen["omitidos"][:20]:
            self.stdout.write(f"  {item['modelo']}:{item['pk']} {item['nombre']}")
        if resumen["apply"]:
            self.stdout.write(self.style.SUCCESS("Catálogo demo sincronizado."))
        else:
            self.stdout.write("Dry-run: no se escribió en la base.")
