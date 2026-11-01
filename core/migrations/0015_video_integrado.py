from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_almacenamiento_placa'),
    ]

    operations = [
        migrations.AddField(
            model_name='procesador',
            name='graficos_integrados',
            field=models.BooleanField(
                blank=True,
                help_text=(
                    'Sí: se confirmó que el procesador incluye gráficos. '
                    'No: se confirmó que no incluye. '
                    'Desconocido: no se sabe. '
                    'No lo deduzcas del nombre, la marca ni la descripción.'
                ),
                null=True,
                verbose_name='Gráficos integrados',
            ),
        ),
        migrations.AddField(
            model_name='placamadre',
            name='tiene_salidas_video',
            field=models.BooleanField(
                blank=True,
                help_text=(
                    'Sí: se confirmó que la placa tiene al menos una salida de video '
                    'para el gráfico integrado, como HDMI, DisplayPort o VGA. '
                    'No: se confirmó que no tiene. '
                    'Desconocido: no se sabe. '
                    'No lo deduzcas del nombre, la marca, la descripción ni el chipset.'
                ),
                null=True,
                verbose_name='Salidas de video',
            ),
        ),
    ]
