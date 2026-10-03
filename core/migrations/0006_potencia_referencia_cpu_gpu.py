from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_pedido_paypal_transaccion_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='procesador',
            name='potencia_referencia_watts',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Watts de referencia para estimar la fuente. No es el consumo máximo ni equivale al TDP. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Potencia de referencia (W)',
            ),
        ),
        migrations.AddField(
            model_name='tarjetagrafica',
            name='consumo_referencia_watts',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Consumo de referencia de la tarjeta, en watts. Sirve para estimar la fuente. No es el consumo máximo ni el TDP. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Consumo de referencia (W)',
            ),
        ),
        migrations.AddField(
            model_name='tarjetagrafica',
            name='potencia_minima_fuente_watts',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Potencia mínima de fuente que indica el fabricante para un equipo con esta GPU. No es el consumo de la tarjeta. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Fuente mínima recomendada (W)',
            ),
        ),
    ]
