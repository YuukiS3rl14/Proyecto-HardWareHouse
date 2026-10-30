import logging
import uuid

from django.db import migrations, models


def rellenar_invoices_existentes(apps, schema_editor):
    """Asigna un UUID distinto a cada pedido ya guardado, sin usar el id como invoice nuevo."""
    Pedido = apps.get_model('core', 'Pedido')
    logger = logging.getLogger('paypal.ipn')
    ids = list(Pedido.objects.order_by('id').values_list('id', flat=True))
    usados = set()
    for pedido_id in ids:
        pedido = Pedido.objects.get(pk=pedido_id)
        candidato = uuid.uuid4()
        while candidato in usados:
            candidato = uuid.uuid4()
        usados.add(candidato)
        pedido.paypal_invoice = candidato
        pedido.paypal_invoice_legado = str(pedido.id)
        pedido.save(update_fields=['paypal_invoice', 'paypal_invoice_legado'])

    pendientes = list(
        Pedido.objects.filter(estado='PENDIENTE').order_by('id').values_list('id', 'paypal_invoice_legado')
    )
    for pedido_id, legado in pendientes:
        logger.warning(
            'Pedido #%s pendiente conserva el invoice legado %s. '
            'Un IPN con ese número solo se acepta si sigue guardado en este pedido. '
            'Si ese cobro se hizo en otra base o después de un reinicio, requiere conciliación manual.',
            pedido_id,
            legado,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_itemcarrito_options_alter_pagoboleta_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='paypal_invoice',
            field=models.UUIDField(editable=False, null=True, verbose_name='Invoice PayPal'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='paypal_invoice_legado',
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=32,
                null=True,
                verbose_name='Invoice PayPal legado',
            ),
        ),
        migrations.RunPython(rellenar_invoices_existentes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='pedido',
            name='paypal_invoice',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name='Invoice PayPal',
            ),
        ),
        migrations.AlterField(
            model_name='pedido',
            name='paypal_invoice_legado',
            field=models.CharField(
                blank=True,
                editable=False,
                help_text='Invoice numérico ya enviado a PayPal antes del UUID. Los pedidos nuevos lo dejan vacío.',
                max_length=32,
                null=True,
                unique=True,
                verbose_name='Invoice PayPal legado',
            ),
        ),
    ]
