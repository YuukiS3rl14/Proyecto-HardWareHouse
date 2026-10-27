"""Rol de solo lectura para Power BI. La contraseña llega por el entorno."""
from __future__ import annotations

import os

import psycopg
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from psycopg import sql

ROL = "powerbi_reader"
HOSTS_LOCALES = {"", "localhost", "127.0.0.1", "::1"}


class Command(BaseCommand):
    help = (
        "Crea o actualiza el rol PostgreSQL powerbi_reader con SELECT solo sobre "
        "el esquema analytics. La contraseña se lee de POWERBI_DB_PASSWORD y no se guarda."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--apply", action="store_true")
        parser.add_argument(
            "--update-password",
            action="store_true",
            help="Cambia la contraseña si el rol ya existe. Requiere POWERBI_DB_PASSWORD.",
        )

    def handle(self, *args, **options):
        if options["dry_run"] == options["apply"]:
            raise CommandError("Indica exactamente una opción: --dry-run o --apply.")
        self._exigir_local()
        password = os.environ.get("POWERBI_DB_PASSWORD", "")
        with self._conectar() as conn:
            with conn.cursor() as cursor:
                if not self._puede_crear_roles(cursor):
                    raise CommandError("El usuario de la base no puede crear roles.")
                existe = self._existe(cursor)
                if options["dry_run"]:
                    self._informe(existe, actualiza_clave=False, simulado=True)
                    return
                if not existe and len(password) < 16:
                    raise CommandError(
                        "Define POWERBI_DB_PASSWORD con al menos 16 caracteres para crear el rol."
                    )
                if existe and options["update_password"] and len(password) < 16:
                    raise CommandError(
                        "Define POWERBI_DB_PASSWORD con al menos 16 caracteres para cambiar la clave."
                    )
                if not existe:
                    cursor.execute(
                        sql.SQL(
                            "CREATE ROLE {} WITH LOGIN PASSWORD {} "
                            "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT CONNECTION LIMIT 10"
                        ).format(sql.Identifier(ROL), sql.Literal(password))
                    )
                elif options["update_password"]:
                    cursor.execute(
                        sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(
                            sql.Identifier(ROL), sql.Literal(password)
                        )
                    )
                self._conceder(cursor)
                self._informe(True, actualiza_clave=options["update_password"] or not existe, simulado=False)

    def _exigir_local(self):
        if connection.vendor != "postgresql":
            raise CommandError(f"Se requiere PostgreSQL. Base actual: {connection.vendor!r}.")
        config = connection.settings_dict
        host = (config.get("HOST") or "").strip().lower()
        if host not in HOSTS_LOCALES or "railway" in host or "rlwy.net" in host:
            raise CommandError(
                f"No se crea el rol en una base remota ({host or 'sin host'} / {config.get('NAME')})."
            )

    def _conectar(self):
        config = connection.settings_dict
        return psycopg.connect(
            host=config.get("HOST") or "127.0.0.1",
            port=config.get("PORT") or 5432,
            dbname=config.get("NAME"),
            user=config.get("USER"),
            password=config.get("PASSWORD") or "",
            autocommit=True,
        )

    def _puede_crear_roles(self, cursor) -> bool:
        cursor.execute("SELECT rolsuper OR rolcreaterole FROM pg_roles WHERE rolname = current_user")
        fila = cursor.fetchone()
        return bool(fila and fila[0])

    def _existe(self, cursor) -> bool:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (ROL,))
        return cursor.fetchone() is not None

    def _conceder(self, cursor):
        cursor.execute("SELECT current_database()")
        base = cursor.fetchone()[0]
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(base), sql.Identifier(ROL))
        )
        cursor.execute("REVOKE ALL ON SCHEMA analytics FROM PUBLIC")
        cursor.execute(
            sql.SQL("GRANT USAGE ON SCHEMA analytics TO {}").format(sql.Identifier(ROL))
        )
        cursor.execute(
            sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO {}").format(sql.Identifier(ROL))
        )
        cursor.execute(
            sql.SQL("REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics FROM {}").format(
                sql.Identifier(ROL)
            )
        )
        cursor.execute(
            sql.SQL("ALTER ROLE {} SET search_path = analytics").format(sql.Identifier(ROL))
        )
        cursor.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO powerbi_reader"
        )

    def _informe(self, existe: bool, *, actualiza_clave: bool, simulado: bool):
        self.stdout.write(f"Rol: {ROL}")
        self.stdout.write(f"Existe: {'sí' if existe else 'no'}")
        self.stdout.write("Permisos: CONNECT, USAGE en analytics, SELECT en sus vistas.")
        self.stdout.write("Sin INSERT, UPDATE, DELETE ni acceso a las tablas operacionales.")
        if simulado:
            self.stdout.write("Dry-run: no se modificó el rol.")
            return
        self.stdout.write(
            "Contraseña actualizada." if actualiza_clave else "Se conservó la contraseña existente."
        )
        self.stdout.write(self.style.SUCCESS("Rol powerbi_reader listo."))
