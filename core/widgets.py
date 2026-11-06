from decimal import Decimal

from django import forms

from core.calificaciones import PASOS


class EstrellasWidget(forms.Widget):
    template_name = 'core/widgets/estrellas.html'

    def get_context(self, name, value, attrs):
        contexto = super().get_context(name, value, attrs)
        seleccionado = ''
        if value not in (None, ''):
            seleccionado = f'{Decimal(str(value)).quantize(Decimal("0.1"))}'
        estrellas = []
        for indice in range(1, 6):
            mitad = f'{(Decimal(indice) - Decimal("0.5")).quantize(Decimal("0.1"))}'
            entera = f'{Decimal(indice).quantize(Decimal("0.1"))}'
            estrellas.append({
                'mitad': mitad,
                'entera': entera,
                'mitad_elegida': mitad == seleccionado,
                'entera_elegida': entera == seleccionado,
                'etiqueta_mitad': mitad.replace('.', ','),
                'etiqueta_entera': entera.replace('.', ','),
            })
        contexto['widget']['estrellas'] = estrellas
        contexto['widget']['pasos'] = [f'{paso}' for paso in PASOS]
        contexto['widget']['texto'] = (
            f'{seleccionado.replace(".", ",")} de 5 estrellas' if seleccionado else 'Selecciona una calificación'
        )
        return contexto
