from pathlib import Path

from django.db import migrations, models

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


class RunSQLPostgreSQL(migrations.RunSQL):
    """Aplica el SQL de analytics solo en PostgreSQL.

    El script usa CREATE SCHEMA, security_barrier, AT TIME ZONE y COMMENT ON.
    SQLite no entiende SCHEMA y las pruebas locales fallan al crear la base.
    En otro motor la operación no hace nada, ni al avanzar ni al revertir.

    Si esta migración ya está registrada en django_migrations, Django no la
    vuelve a ejecutar. Cambiar esta clase no altera las vistas ya creadas
    en PostgreSQL.
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_itempedido_producto"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="pedido",
            index=models.Index(fields=["estado", "fecha_pedido"], name="pedido_estado_fecha_idx"),
        ),
        migrations.AddIndex(
            model_name="pagoboleta",
            index=models.Index(fields=["fecha_pago"], name="boleta_fecha_pago_idx"),
        ),
        migrations.AddIndex(
            model_name="itempedido",
            index=models.Index(fields=["producto_modelo", "producto_pk"], name="itempedido_producto_idx"),
        ),
        RunSQLPostgreSQL(
            sql=(SQL_DIR / "analytics_views.sql").read_text(encoding="utf-8"),
            reverse_sql=(SQL_DIR / "analytics_views_reverse.sql").read_text(encoding="utf-8"),
        ),
    ]
