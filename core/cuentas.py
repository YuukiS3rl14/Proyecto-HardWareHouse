"""Grupo organizativo Cliente. No otorga permisos ni cambia el acceso a la tienda."""
import logging

from django.contrib.auth.models import Group

GRUPO_CLIENTE = 'Cliente'
GRUPOS_PERSONAL = ('Administrador', 'Trabajador')

logger = logging.getLogger(__name__)


def obtener_grupo_cliente():
    """Devuelve el grupo Cliente. Si no existe, lo crea sin permisos."""
    grupo, _creado = Group.objects.get_or_create(name=GRUPO_CLIENTE)
    permisos = list(
        grupo.permissions.values_list('content_type__app_label', 'codename').order_by(
            'content_type__app_label', 'codename',
        )
    )
    if permisos:
        detalle = ', '.join(f'{app}.{codigo}' for app, codigo in permisos)
        logger.warning(
            'El grupo Cliente ya tiene %s permisos (%s). No se eliminan. '
            'La membresía sigue siendo solo organizativa.',
            len(permisos),
            detalle,
        )
    return grupo


def asignar_grupo_cliente(usuario):
    """Asocia una cuenta ya guardada. No quita otros grupos ni cambia sus datos."""
    if not usuario.pk:
        raise ValueError('El usuario debe estar guardado antes de asignar el grupo Cliente.')
    usuario.groups.add(obtener_grupo_cliente())
    return usuario


def cuentas_normales_sin_cliente():
    from django.contrib.auth.models import User

    return (
        User.objects.filter(is_staff=False, is_superuser=False, user_permissions__isnull=True)
        .exclude(groups__name__in=GRUPOS_PERSONAL)
        .exclude(groups__name=GRUPO_CLIENTE)
        .distinct()
        .order_by('username')
    )
