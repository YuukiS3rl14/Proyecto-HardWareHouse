from django.core.management.base import BaseCommand, CommandError

from core.pedidos_demo_pbi import PedidosDemoError, generar_pedidos_demo


class Command(BaseCommand):
    help = (
        "Crea pedidos pagados sintéticos para analítica, con transacción DEMO-PBI-. "
        "No llama a PayPal, no envía correos, no descuenta stock y no modifica pedidos reales. "
        "Los montos son sintéticos. --apply exige --confirm."
    )

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=1000)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--apply", action="store_true")
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirmación explícita para escribir pedidos sintéticos.",
        )

    def handle(self, *args, **options):
        if options["dry_run"] == options["apply"]:
            raise CommandError("Indica exactamente una opción: --dry-run o --apply.")
        if options["count"] < 1:
            raise CommandError("--count debe ser al menos 1.")
        if options["apply"] and not options["confirm"]:
            raise CommandError(
                "Escritura cancelada. Vuelve a ejecutar con --apply --confirm "
                "para crear los pedidos sintéticos en la base local."
            )
        try:
            resumen = generar_pedidos_demo(
                count=options["count"],
                seed=options["seed"],
                apply=options["apply"],
            )
        except PedidosDemoError as exc:
            raise CommandError(str(exc)) from exc
        self._imprimir(resumen, options["seed"])

    def _imprimir(self, resumen: dict, seed: int) -> None:
        modo = "apply" if resumen["apply"] else "dry-run"
        self.stdout.write(f"Base: {resumen['base']} @ {resumen['host']}")
        self.stdout.write(f"Modo: {modo}. Semilla: {seed}.")
        self.stdout.write(f"Pedidos del plan: {resumen['pedidos_plan']}")
        self.stdout.write(f"Ya existentes: {resumen['ya_existentes']}")
        self.stdout.write(f"Por crear: {resumen['por_crear']}")
        self.stdout.write(f"Creados: {resumen['creados']}")
        self.stdout.write(f"Clientes nuevos: {resumen['clientes_nuevos']}")
        if resumen["desde"] and resumen["hasta"]:
            self.stdout.write(f"Rango de fechas: {resumen['desde']} → {resumen['hasta']}")
        self.stdout.write(f"Monto sintético del lote nuevo: {resumen['total_clp']} CLP")
        if resumen["apply"] and resumen["creados"]:
            self.stdout.write(self.style.SUCCESS("Pedidos sintéticos DEMO-PBI creados."))
        elif resumen["apply"]:
            self.stdout.write(self.style.SUCCESS("No había pedidos DEMO-PBI nuevos que crear."))
        else:
            self.stdout.write("Dry-run: no se escribió en la base.")
