from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_ram_modulos_formato_capacidad'),
    ]

    operations = [
        migrations.AddField(
            model_name='itempedido',
            name='producto_modelo',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Modelo del producto'),
        ),
        migrations.AddField(
            model_name='itempedido',
            name='producto_pk',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='ID del producto'),
        ),
    ]
