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
#
# PostgreSQL acepta varias columnas y un CHECK en un solo ALTER, y DEFAULT NOW().
# SQLite rechaza NOW() («near "("»), solo agrega o quita una columna por ALTER y
# no tiene ADD CONSTRAINT. En SQLite se usan sentencias separadas y se reconstruye
# la tabla para el CHECK. El SQL de PostgreSQL no cambia: si esta migración ya
# corrió en Railway, no vuelve a ejecutarse.

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


class _SqlPorMotor(migrations.RunSQL):
    """Ejecuta el SQL de PostgreSQL guardado en sql, u otro en SQLite."""

    def __init__(self, sql, reverse_sql=None, sqlite_sql=None, sqlite_reverse_sql=None):
        super().__init__(sql, reverse_sql)
        self.sqlite_sql = sql if sqlite_sql is None else sqlite_sql
        self.sqlite_reverse_sql = (
            reverse_sql if sqlite_reverse_sql is None else sqlite_reverse_sql
        )

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'sqlite':
            self._ejecutar(schema_editor, self.sqlite_sql)
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'sqlite':
            self._ejecutar(schema_editor, self.sqlite_reverse_sql)
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)

    def _ejecutar(self, schema_editor, sql):
        if callable(sql):
            sql(schema_editor)
            return
        self._run_sql(schema_editor, sql)


def _cita(nombre):
    return '"%s"' % nombre.replace('"', '""')


def _reconstruir_check(schema_editor, tabla, fragmento, agregar):
    """SQLite no agrega ni quita un CHECK con ALTER TABLE."""
    conexion = schema_editor.connection
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = %s",
            [tabla],
        )
        fila = cursor.fetchone()
        if fila is None:
            raise RuntimeError('No existe la tabla %s.' % tabla)
        crear = fila[0]
        cursor.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'index' AND tbl_name = %s AND sql IS NOT NULL",
            [tabla],
        )
        indices = [registro[0] for registro in cursor.fetchall()]
    marca = ', %s' % fragmento
    if agregar and marca in crear:
        return
    if agregar:
        cabeza, cierre, cola = crear.rpartition(')')
        crear_nuevo = '%s%s%s%s' % (cabeza, marca, cierre, cola)
    else:
        if marca not in crear:
            return
        crear_nuevo = crear.replace(marca, '', 1)
    citada = _cita(tabla)
    temporal = '%s__oferta_tmp' % tabla
    citada_temporal = _cita(temporal)
    if 'CREATE TABLE %s' % citada in crear_nuevo:
        crear_nuevo = crear_nuevo.replace(
            'CREATE TABLE %s' % citada,
            'CREATE TABLE %s' % citada_temporal,
            1,
        )
    else:
        crear_nuevo = crear_nuevo.replace(
            'CREATE TABLE %s' % tabla,
            'CREATE TABLE %s' % citada_temporal,
            1,
        )
    with conexion.cursor() as cursor:
        cursor.execute(crear_nuevo)
        cursor.execute('INSERT INTO %s SELECT * FROM %s' % (citada_temporal, citada))
        cursor.execute('DROP TABLE %s' % citada)
        cursor.execute('ALTER TABLE %s RENAME TO %s' % (citada_temporal, citada))
        for indice in indices:
            cursor.execute(indice)


def _check_sqlite(tabla, restriccion):
    fragmento = (
        'CONSTRAINT %s CHECK ('
        '(precio_oferta IS NULL OR (precio_oferta > 0 AND precio_oferta < precio)) '
        'AND (en_oferta = false OR precio_oferta IS NOT NULL))'
    ) % _cita(restriccion)

    def aplicar(schema_editor):
        _reconstruir_check(schema_editor, tabla, fragmento, True)

    def quitar(schema_editor):
        _reconstruir_check(schema_editor, tabla, fragmento, False)

    return aplicar, quitar


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
    citada = _cita(tabla)
    columnas_sqlite = [
        f'ALTER TABLE {citada} ADD COLUMN creado_en datetime NOT NULL DEFAULT CURRENT_TIMESTAMP',
        f'ALTER TABLE {citada} ADD COLUMN actualizado_en datetime NOT NULL DEFAULT CURRENT_TIMESTAMP',
        f'ALTER TABLE {citada} ADD COLUMN en_oferta boolean NOT NULL DEFAULT 0',
        f'ALTER TABLE {citada} ADD COLUMN precio_oferta numeric(10, 2) NULL',
    ]
    quitar_sqlite = [
        f'ALTER TABLE {citada} DROP COLUMN precio_oferta',
        f'ALTER TABLE {citada} DROP COLUMN en_oferta',
        f'ALTER TABLE {citada} DROP COLUMN actualizado_en',
        f'ALTER TABLE {citada} DROP COLUMN creado_en',
    ]
    aplicar_check, quitar_check = _check_sqlite(tabla, restriccion)
    base = [
        _SqlPorMotor(
            columnas,
            reverse_sql=quitar_columnas,
            sqlite_sql=columnas_sqlite,
            sqlite_reverse_sql=quitar_sqlite,
        ),
        _SqlPorMotor(
            chequeo,
            reverse_sql=f'ALTER TABLE {tabla} DROP CONSTRAINT {restriccion}',
            sqlite_sql=aplicar_check,
            sqlite_reverse_sql=quitar_check,
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
