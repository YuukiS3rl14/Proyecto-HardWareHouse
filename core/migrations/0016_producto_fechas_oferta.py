import decimal

import django.core.validators
from django.db import migrations, models
from django.db.models import F, Q

# Django aplica esta migración al correr migrate, también en la base temporal de
# manage.py test. No hay otra migración que agregue estas columnas: la última es
# 0015_video_integrado. Agrega cuatro columnas y un CHECK en las diez tablas de
# producto, sin cambiar ids ni pedidos. El DEFAULT se conserva para que el código
# anterior pueda insertar después de migrar. Las filas existentes quedan con la
# fecha de esta migración, no con una fecha histórica reconstruida.

_MODELOS = (
    'procesador',
    'tarjetagrafica',
    'memoriaram',
    'placamadre',
    'almacenamientossd',
    'almacenamientohdd',
    'gabinete',
    'fuentedepoder',
    'refrigeracioncooler',
    'ventilador',
)

_AYUDA_CREADO = (
    'Se completa solo. En productos que ya existían, esta fecha es la de la '
    'migración que agregó el campo, no la fecha real de alta.'
)
_AYUDA_ACTUALIZADO = (
    'Se actualiza solo al guardar. No reconstruye cambios anteriores a este campo.'
)


def _estado(model_name):
    tabla = f'core_{model_name}'
    restriccion = f'{tabla}_oferta_valida'
    campos = [
        migrations.AddField(
            model_name=model_name,
            name='creado_en',
            field=models.DateTimeField(
                auto_now_add=True,
                help_text=_AYUDA_CREADO,
                verbose_name='Registrado en',
            ),
        ),
        migrations.AddField(
            model_name=model_name,
            name='actualizado_en',
            field=models.DateTimeField(
                auto_now=True,
                help_text=_AYUDA_ACTUALIZADO,
                verbose_name='Actualizado en',
            ),
        ),
        migrations.AddField(
            model_name=model_name,
            name='en_oferta',
            field=models.BooleanField(default=False, verbose_name='En oferta'),
        ),
        migrations.AddField(
            model_name=model_name,
            name='precio_oferta',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))],
                verbose_name='Precio de oferta',
            ),
        ),
        migrations.AddConstraint(
            model_name=model_name,
            constraint=models.CheckConstraint(
                check=(
                    Q(precio_oferta__isnull=True)
                    | (Q(precio_oferta__gt=0) & Q(precio_oferta__lt=F('precio')))
                ) & (
                    Q(en_oferta=False) | Q(precio_oferta__isnull=False)
                ),
                name=restriccion,
            ),
        ),
    ]
    columnas = (
        f'ALTER TABLE {tabla} '
        f'ADD COLUMN creado_en timestamp with time zone NOT NULL DEFAULT NOW(), '
        f'ADD COLUMN actualizado_en timestamp with time zone NOT NULL DEFAULT NOW(), '
        f'ADD COLUMN en_oferta boolean NOT NULL DEFAULT false, '
        f'ADD COLUMN precio_oferta numeric(10, 2) NULL'
    )
    quitar_columnas = (
        f'ALTER TABLE {tabla} '
        f'DROP COLUMN precio_oferta, '
        f'DROP COLUMN en_oferta, '
        f'DROP COLUMN actualizado_en, '
        f'DROP COLUMN creado_en'
    )
    chequeo = (
        f'ALTER TABLE {tabla} ADD CONSTRAINT {restriccion} CHECK ('
        f'(precio_oferta IS NULL OR (precio_oferta > 0 AND precio_oferta < precio)) '
        f'AND (en_oferta = false OR precio_oferta IS NOT NULL))'
    )
    base = [
        migrations.RunSQL(columnas, reverse_sql=quitar_columnas),
        migrations.RunSQL(
            chequeo,
            reverse_sql=f'ALTER TABLE {tabla} DROP CONSTRAINT {restriccion}',
        ),
    ]
    return campos, base


def _operaciones():
    estado = []
    base = []
    for model_name in _MODELOS:
        campos, sentencias = _estado(model_name)
        estado.extend(campos)
        base.extend(sentencias)
    return [
        migrations.SeparateDatabaseAndState(
            state_operations=estado,
            database_operations=base,
        ),
    ]


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_video_integrado'),
    ]

    operations = _operaciones()
