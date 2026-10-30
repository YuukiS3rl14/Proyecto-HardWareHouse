from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_pedido_paypal_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='procesador',
            name='incluye_cooler',
            field=models.BooleanField(
                blank=True,
                help_text='Sí: el procesador trae cooler. No: se confirmó que no trae. Vacío: no se sabe. No lo deduzcas del nombre.',
                null=True,
                verbose_name='Incluye cooler de fábrica',
            ),
        ),
        migrations.AddField(
            model_name='procesador',
            name='potencia_termica_referencia_watts',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Watts de referencia para comparar con la disipación declarada de un cooler. No es el TDP ni la potencia que usa la fuente. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Referencia térmica (W)',
            ),
        ),
        migrations.AddField(
            model_name='gabinete',
            name='altura_max_cooler_mm',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Altura máxima de un cooler de aire que admite el gabinete. No describe radiadores ni el largo de la GPU. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Altura máxima de cooler (mm)',
            ),
        ),
        migrations.AddField(
            model_name='refrigeracioncooler',
            name='disipacion_referencia_watts',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Watts de disipación declarados para este cooler de demostración o de catálogo. No es una medición del equipo armado. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Disipación de referencia (W)',
            ),
        ),
        migrations.AddField(
            model_name='refrigeracioncooler',
            name='altura_mm',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Altura de un cooler de aire, en milímetros. No aplica a un radiador líquido. Déjalo vacío si no se conoce; no uses 0.',
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Altura (mm)',
            ),
        ),
    ]
