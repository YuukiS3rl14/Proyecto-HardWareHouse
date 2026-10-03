from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_potencia_referencia_cpu_gpu'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarjetagrafica',
            name='largo_mm',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Largo de la tarjeta en milímetros. Solo sirve para compararlo con el máximo del gabinete. No describe grosor ni altura. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Largo (mm)',
            ),
        ),
        migrations.AddField(
            model_name='gabinete',
            name='largo_max_gpu_mm',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Largo máximo de tarjeta que admite el gabinete, en milímetros. No reserva espacio de radiadores ni limita grosor o altura. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Largo máximo de GPU (mm)',
            ),
        ),
    ]
