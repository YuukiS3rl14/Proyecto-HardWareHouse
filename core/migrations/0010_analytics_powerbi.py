from pathlib import Path

from django.db import migrations, models

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


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
        migrations.RunSQL(
            sql=(SQL_DIR / "analytics_views.sql").read_text(encoding="utf-8"),
            reverse_sql=(SQL_DIR / "analytics_views_reverse.sql").read_text(encoding="utf-8"),
        ),
    ]
