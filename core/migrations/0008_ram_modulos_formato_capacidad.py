from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_largo_gpu_gabinete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memoriaram',
            name='capacidad_gb',
            field=models.IntegerField(
                help_text=(
                    'Capacidad del producto tal como se vende: el módulo suelto o el kit completo. '
                    'La capacidad del armado suma cantidad × este valor. No la multipliques por '
                    'los módulos, porque este número ya incluye todos los del kit.'
                ),
                verbose_name='Capacidad del producto (GB)',
            ),
        ),
        migrations.AlterField(
            model_name='memoriaram',
            name='velocidad_mhz',
            field=models.IntegerField(
                help_text='Ej: 3200, 5600. Es la velocidad indicada del producto, no la velocidad final del equipo.',
                verbose_name='Velocidad (MHz)',
            ),
        ),
        migrations.AddField(
            model_name='memoriaram',
            name='modulos_por_producto',
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    'Cuántos módulos trae este producto o kit. Las ranuras ocupadas son '
                    'cantidad × este número. Vacío si no se sabe; no se deduce del nombre.'
                ),
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Módulos por producto',
            ),
        ),
        migrations.AddField(
            model_name='memoriaram',
            name='capacidad_modulo_gb',
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    'Capacidad de un solo módulo. Si la indicas junto con los módulos, debe '
                    'cumplirse capacidad del producto = módulos × esta cifra. No se suma aparte '
                    'de la capacidad del producto. Vacío si no se sabe.'
                ),
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Capacidad por módulo (GB)',
            ),
        ),
        migrations.AddField(
            model_name='memoriaram',
            name='formato_ram',
            field=models.CharField(
                blank=True,
                choices=[('DIMM', 'DIMM'), ('SO-DIMM', 'SO-DIMM')],
                help_text='DIMM o SO-DIMM. Vacío si no se sabe; no se deduce del nombre del producto.',
                max_length=10,
                null=True,
                verbose_name='Formato',
            ),
        ),
        migrations.AddField(
            model_name='placamadre',
            name='formato_ram_soportado',
            field=models.CharField(
                blank=True,
                choices=[('DIMM', 'DIMM'), ('SO-DIMM', 'SO-DIMM')],
                help_text='DIMM o SO-DIMM. Vacío si no se sabe.',
                max_length=10,
                null=True,
                verbose_name='Formato de RAM admitido',
            ),
        ),
        migrations.AddField(
            model_name='placamadre',
            name='capacidad_maxima_ram_gb',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Capacidad total máxima de la placa, en GB. Vacío si no se sabe; no uses 0.',
                null=True,
                validators=[MinValueValidator(1)],
                verbose_name='Capacidad máxima de RAM (GB)',
            ),
        ),
    ]
