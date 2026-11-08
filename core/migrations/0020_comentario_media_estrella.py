from django.db import migrations, models
import core.calificaciones
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_movimiento_stock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comentario',
            name='calificacion',
            field=models.DecimalField(
                decimal_places=1,
                help_text='Calificación de 0,5 a 5 estrellas, en medios puntos.',
                max_digits=2,
                validators=[core.calificaciones.validar_media_estrella],
            ),
        ),
        migrations.AlterField(
            model_name='comentario',
            name='texto',
            field=models.TextField(
                max_length=1500,
                validators=[django.core.validators.MaxLengthValidator(1500)],
            ),
        ),
    ]
