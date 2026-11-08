from django import template

from core.formato_clp import formatear_pesos

register = template.Library()


@register.filter(name='pesos')
def pesos(valor):
    return formatear_pesos(valor)
