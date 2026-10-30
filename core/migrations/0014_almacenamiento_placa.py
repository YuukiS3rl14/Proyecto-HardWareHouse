import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_refrigeracion_referencia'),
    ]

    operations = [
        migrations.AddField(
            model_name='placamadre',
            name='ranuras_m2_solo_nvme',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Ranuras M.2 físicas que aceptan NVMe y no SATA. No incluyas aquí las que también aceptan SATA. 0 significa que no hay ninguna. Vacío si no se sabe.',
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Ranuras M.2 solo NVMe',
            ),
        ),
        migrations.AddField(
            model_name='placamadre',
            name='ranuras_m2_solo_sata',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Ranuras M.2 físicas que aceptan SATA y no NVMe. No incluyas aquí las compartidas. 0 significa que no hay ninguna. Vacío si no se sabe.',
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Ranuras M.2 solo SATA',
            ),
        ),
        migrations.AddField(
            model_name='placamadre',
            name='ranuras_m2_nvme_o_sata',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Ranuras M.2 físicas que aceptan NVMe o SATA, una unidad a la vez. No las sumes otra vez en los campos exclusivos. 0 significa que no hay ninguna. Vacío si no se sabe.',
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Ranuras M.2 NVMe o SATA',
            ),
        ),
        migrations.AddField(
            model_name='placamadre',
            name='puertos_sata',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Puertos SATA para SSD de 2,5 pulgadas y discos duros. No cuenta las ranuras M.2. 0 significa que no hay ninguno. Vacío si no se sabe.',
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Puertos SATA',
            ),
        ),
        migrations.AddField(
            model_name='almacenamientohdd',
            name='interfaz',
            field=models.CharField(
                blank=True,
                choices=[('SATA III', 'SATA III')],
                help_text='SATA III si el disco usa un puerto SATA. Vacío si no se sabe; no se deduce del nombre.',
                max_length=20,
                null=True,
                verbose_name='Interfaz',
            ),
        ),
        migrations.AddField(
            model_name='almacenamientohdd',
            name='formato',
            field=models.CharField(
                blank=True,
                choices=[('3.5"', '3.5"'), ('2.5"', '2.5"')],
                help_text='3.5" o 2.5". Vacío si no se sabe. No cambia el puerto: un HDD SATA usa un puerto SATA.',
                max_length=10,
                null=True,
                verbose_name='Formato',
            ),
        ),
    ]
