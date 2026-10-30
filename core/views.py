from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash 
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .excel_armado import (
    aclaracion_de_pieza,
    especificaciones_de,
    libro_en_bytes,
    pesos_enteros,
    texto_de_estado,
)
from .compatibilidad import (
    ACLARACION_RAM,
    ESTADO_NO_EVALUADA,
    MENSAJE_ALMACENAMIENTO,
    EvaluacionCandidato,
    LineaRam,
    evaluar_candidato,
    evaluaciones_de_seleccion,
    texto_del_armado,
    validar_armado,
)
from .forms import *
import json
import logging
import uuid

from django.db import transaction 
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from core.catalogo.registry import CATALOGO_MODELOS, model_name_for
from core.tienda_filtros import (
    BANDAS_PRECIO,
    ORDENES,
    ORDENES_VALIDAS,
    filtro_precio,
    ids_validos,
    opciones_catalogo,
    ordenar_catalogo,
)

from .models import *
from .imagenes import url_imagen_producto, urls_imagen_armado
from .payments import SESION_VERIFICANDO, contexto_conversion, formulario_paypal, preparar_pedido_checkout

paypal_logger = logging.getLogger('paypal.ipn')
from django.utils import timezone

# Create your views here.

def mostrarIndex(request):
    proveedores_con_logo = Proveedor.objects.filter(logo__isnull=False).exclude(logo='').order_by('nombre').distinct()
    
    context = {
        'proveedores': proveedores_con_logo
    }
    return render(request, 'core/index.html', context)

def mostrarArmado(request):    
    def get_component_data(model, fields, model_name):
        components = []
        for item in model.objects.all():
            data = {'id': item.id, 'model_name': model_name}
            for field in fields:
                data[field] = getattr(item, field)
            data['imagen'] = url_imagen_producto(item)
            components.append(data)
        return components

    componentes = {
        'placa_madre': get_component_data(PlacaMadre, ['nombre', 'precio', 'socket_cpu', 'tipo_ram_soportado', 'formato', 'chipset', 'ranuras_ram', 'formato_ram_soportado', 'capacidad_maxima_ram_gb', 'stock'], 'placa_madre'),
        'procesador': get_component_data(Procesador, ['nombre', 'precio', 'socket', 'nucleos', 'frecuencia_base', 'potencia_referencia_watts', 'stock'], 'procesador'),
        'memoria_ram': get_component_data(MemoriaRam, ['nombre', 'precio', 'tipo_ddr', 'capacidad_gb', 'modulos_por_producto', 'capacidad_modulo_gb', 'formato_ram', 'velocidad_mhz', 'stock'], 'memoria_ram'),
        'tarjeta_grafica': get_component_data(TarjetaGrafica, ['nombre', 'precio', 'vram_gb', 'tipo_memoria', 'interfaz', 'consumo_referencia_watts', 'potencia_minima_fuente_watts', 'largo_mm', 'stock'], 'tarjeta_grafica'),
        'almacenamiento': (
            get_component_data(AlmacenamientoSSD, ['nombre', 'precio', 'capacidad_gb', 'formato', 'stock'], 'almacenamiento_ssd')
            + get_component_data(AlmacenamientoHDD, ['nombre', 'precio', 'capacidad_gb', 'stock'], 'almacenamiento_hdd')
        ),
        'gabinete': get_component_data(Gabinete, ['nombre', 'precio', 'formato_soporte', 'largo_max_gpu_mm', 'stock'], 'gabinete'),
        'fuente_de_poder': get_component_data(FuenteDePoder, ['nombre', 'precio', 'potencia_watts', 'stock'], 'fuente_de_poder'),
        'refrigeracion_cooler': get_component_data(RefrigeracionCooler, ['nombre', 'precio', 'socket_compatibles', 'tipo', 'tamanho_radiador_mm', 'stock'], 'refrigeracion'),
    }

    for categoria in componentes:
        for componente in componentes[categoria]:
            componente['precio'] = str(componente['precio'])

    context = {
        'componentes': componentes,
        'imagenes_categoria': urls_imagen_armado(),
    }
    return render(request, 'core/armado.html', context)

@login_required
def mostrarCarrito(request):
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    
    items = carrito.items.all().order_by('id')
    
    total_carrito = carrito.get_total_precio()
    
    context = {
        'items': items,
        'total_carrito': total_carrito,
    }
    return render(request, 'core/carrito.html', context)

@login_required
def mostrarCheckout(request):
    carrito = get_object_or_404(Carrito, usuario=request.user)
    items_carrito = carrito.items.all()

    if not items_carrito.exists():
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de proceder al pago.")
        return redirect('core:carrito')

    # Verificación de stock antes de proceder
    for item_carrito in items_carrito:
        producto = item_carrito.get_related_product()
        if producto.stock < item_carrito.cantidad:
            messages.error(request, f"No hay suficiente stock para '{producto.nombre}'. Solo quedan {producto.stock} unidades. Por favor, ajusta tu carrito.")
            return redirect('core:carrito')


    pedidos_antes = set(
        Pedido.objects.filter(usuario=request.user, estado='PENDIENTE').values_list('id', flat=True)
    )
    pedido = preparar_pedido_checkout(request.user, items_carrito)
    form_paypal, _total_usd = formulario_paypal(pedido)

    context = {
        'pedido': pedido,
        'pedido_reutilizado': pedido.id in pedidos_antes,
        'items_pedido': pedido.items_pedido.all(),
        'form_paypal': form_paypal,
        'estado_pago': 'esperando',
        **contexto_conversion(pedido),
    }
    return render(request, 'core/checkout.html', context)

def _pedido_del_retorno(request):
    bruto = (request.GET.get('pedido') or '').strip()
    if not bruto.isdigit():
        return None
    return Pedido.objects.filter(pk=int(bruto), usuario=request.user).first()


def _olvidar_verificacion(request, pedido):
    if pedido is not None and request.session.get(SESION_VERIFICANDO) == pedido.id:
        request.session.pop(SESION_VERIFICANDO, None)


@login_required
def paymentSuccess(request):
    pedido = _pedido_del_retorno(request)
    if pedido is not None and pedido.estado == 'PAGADO':
        _olvidar_verificacion(request, pedido)
        paypal_logger.info(
            'Regreso del navegador a payment_success. Pedido #%s del usuario %s ya estaba pagado.',
            pedido.id,
            request.user.pk,
        )
        messages.info(request, "PayPal ya confirmó este pedido. El regreso del navegador no vuelve a marcarlo.")
        return render(request, 'core/payment_success.html', {
            'pedido': pedido,
            'estado_pago': 'pagado',
            **contexto_conversion(pedido),
        })

    if pedido is not None and pedido.estado == 'CANCELADO':
        _olvidar_verificacion(request, pedido)
        paypal_logger.info(
            'Regreso del navegador a payment_success. Pedido #%s del usuario %s está cancelado.',
            pedido.id,
            request.user.pk,
        )
        return render(request, 'core/payment_success.html', {
            'pedido': pedido,
            'estado_pago': 'cancelado',
        })

    if pedido is not None and pedido.estado == 'PENDIENTE' and not (pedido.paypal_transaccion_id or '').strip():
        request.session[SESION_VERIFICANDO] = pedido.id
    paypal_logger.info(
        'Regreso del navegador a payment_success. Pedido %s del usuario %s sigue sin confirmarse por IPN.',
        pedido.id if pedido is not None else 'desconocido',
        request.user.pk,
    )
    messages.info(request, "PayPal registró tu regreso. El pedido sigue pendiente hasta que se confirme el pago.")
    context = {
        'pedido': pedido,
        'estado_pago': 'verificando',
    }
    if pedido is not None:
        context.update(contexto_conversion(pedido))
    return render(request, 'core/payment_success.html', context)

@login_required
def paymentFailed(request):
    pedido = _pedido_del_retorno(request)
    _olvidar_verificacion(request, pedido)
    paypal_logger.info(
        'Regreso del navegador a payment_failed. Pedido %s del usuario %s no se marca como pagado.',
        pedido.id if pedido is not None else 'desconocido',
        request.user.pk,
    )
    messages.warning(request, "El pago fue cancelado en PayPal. El pedido sigue pendiente y puedes reintentarlo.")
    reintento = pedido is not None and pedido.estado == 'PENDIENTE' and not (pedido.paypal_transaccion_id or '').strip()
    context = {
        'pedido': pedido,
        'estado_pago': 'cancelado',
        'reintento_disponible': reintento,
    }
    if reintento:
        context.update(contexto_conversion(pedido))
    return render(request, 'core/payment_failed.html', context)

def mostrarContacto(request):
    return render(request, 'core/contacto.html')


def mostrarSobreNosotros(request):
    from core.faq_tienda import faq_items_acordeon
    from core.knowledge.service import perfil_publico

    return render(
        request,
        'core/about_us.html',
        {
            'faq_items': faq_items_acordeon(),
            'empresa': perfil_publico(),
        },
    )

PRODUCT_MODEL_MAP = {
    'procesador': Procesador,
    'tarjeta_grafica': TarjetaGrafica,
    'memoria_ram': MemoriaRam,
    'placa_madre': PlacaMadre,
    'almacenamiento_ssd': AlmacenamientoSSD,
    'almacenamiento_hdd': AlmacenamientoHDD,
    'gabinete': Gabinete,
    'fuente_de_poder': FuenteDePoder,
    'refrigeracion': RefrigeracionCooler,
    'ventilador': Ventilador,
}

def mostrarDetalle(request, model_name, pk):
    model_name_lower = model_name.lower()
    ModelClass = PRODUCT_MODEL_MAP.get(model_name_lower)
    
    if not ModelClass:
        raise Http404("Tipo de producto no encontrado.")
        
    producto = get_object_or_404(ModelClass, pk=pk)
    
    is_favorito = False
    if request.user.is_authenticated:
        lookup_kwargs = {f'{model_name_lower}__id': pk, 'usuario': request.user}
        is_favorito = Favorito.objects.filter(**lookup_kwargs).exists()

    comment_lookup = {f'{model_name_lower}_id': pk}
    comentarios = Comentario.objects.filter(**comment_lookup).order_by('-fecha_creacion')
    
    stats_comentarios = comentarios.aggregate(
        promedio=Avg('calificacion'),
        total=Count('id')
    )
    promedio_calificacion = stats_comentarios['promedio'] or 0
    total_comentarios = stats_comentarios['total']

    context = {
        'producto': producto,
        'model_name': model_name_lower, 
        'is_favorito': is_favorito,
        'comentarios': comentarios,
        'promedio_calificacion': promedio_calificacion,
        'total_comentarios': total_comentarios,
        'comentario_form': ComentarioForm(),
    }
    return render(request, 'core/detalle.html', context)

TIENDA_PAGE_SIZE = 50

TIENDA_MODELOS = [modelo for modelo, _ in CATALOGO_MODELOS]


def _model_name_tienda(modelo):
    return model_name_for(modelo)


def mostrarTienda(request):
    query = request.GET.get('q')
    selected_categorias = [categoria for categoria in request.GET.getlist('categoria') if categoria]
    selected_proveedores = ids_validos(request.GET.getlist('proveedor'))
    selected_precio = request.GET.get('precio') or ''
    selected_orden = request.GET.get('orden') or 'relevancia'
    if selected_orden not in ORDENES_VALIDAS:
        selected_orden = 'relevancia'
    if filtro_precio(selected_precio) is None:
        selected_precio = ''

    productos_con_modelo = []

    for modelo in TIENDA_MODELOS:
        categoria_modelo = modelo._meta.get_field('categoria').default
        if selected_categorias and categoria_modelo not in selected_categorias:
            continue

        model_name = _model_name_tienda(modelo)
        qs = modelo.objects.select_related('proveedor').all()

        if query:
            qs = qs.filter(
                Q(nombre__icontains=query)
                | Q(proveedor__nombre__icontains=query)
                | Q(categoria__icontains=query)
            )

        if selected_proveedores:
            qs = qs.filter(proveedor__id__in=selected_proveedores)

        banda = filtro_precio(selected_precio)
        if banda is not None:
            qs = qs.filter(banda)

        for producto in qs:
            productos_con_modelo.append((producto, model_name))

    ordenar_catalogo(productos_con_modelo, selected_orden, query)

    paginator = Paginator(productos_con_modelo, TIENDA_PAGE_SIZE)
    productos_page = paginator.get_page(request.GET.get('page'))

    # --- 3. Obtener IDs de productos favoritos del usuario ---
    favoritos_ids = {}
    if request.user.is_authenticated:
        user_favoritos = Favorito.objects.filter(usuario=request.user).select_related('procesador', 'tarjeta_grafica', 'memoria_ram', 'placa_madre', 'almacenamiento_ssd', 'almacenamiento_hdd', 'gabinete', 'fuente_de_poder', 'refrigeracion', 'ventilador')
        for fav in user_favoritos:
            prod = fav.get_related_product()
            if prod:
                model_name_template = prod._meta.model_name.replace('_', '')
                favoritos_ids[f"{model_name_template}-{prod.id}"] = True

    categorias_disponibles, proveedores_disponibles = opciones_catalogo(TIENDA_MODELOS)

    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)
    if selected_orden == 'relevancia':
        pagination_params.pop('orden', None)
    if not selected_precio:
        pagination_params.pop('precio', None)
    pagination_query = pagination_params.urlencode()

    context = {
        'productos': productos_page.object_list,
        'productos_page': productos_page,
        'pagination_query': pagination_query,
        'total_productos': paginator.count,
        'favoritos_ids': favoritos_ids,
        'query': query,
        'categorias': categorias_disponibles,
        'proveedores': proveedores_disponibles,
        'bandas_precio': BANDAS_PRECIO,
        'ordenes': ORDENES,
        'selected_categorias': selected_categorias,
        'selected_proveedores': selected_proveedores,
        'selected_precio': selected_precio,
        'selected_orden': selected_orden,
    }
    return render(request, 'core/tienda.html', context)


def descargar_productos_csv(request):
    """Catálogo de componentes en CSV (p. ej. base de conocimiento de un asistente)."""
    from .productos_csv import generar_csv_bytes

    response = HttpResponse(generar_csv_bytes(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="productos_componentes.csv"'
    return response


def mostrarRegistro(request):
    data = {
        'form': RegistroForm()
    }
    
    if request.method == 'POST':
        form = RegistroForm(data=request.POST) 
        
        if form.is_valid():
            user = form.save()
            
            user_authenticated = authenticate(
                request,
                username=form.cleaned_data["username"], 
                password=form.cleaned_data["password2"] 
            )
            
            if user_authenticated is not None:
                login(request, user_authenticated)
                messages.success(request, '¡Registro exitoso!, Puedes iniciar sesión.')
                return redirect('login')
            else:
                messages.warning(request, 'Registro exitoso, pero fallo al iniciar sesión automáticamente. Inténtalo manualmente.')
                return redirect('login')
        
        data["form"] = form

    return render(request, 'registration/registro.html', data)

@login_required
@transaction.atomic
def verPerfil(request):
    edit_mode = False

    if request.method == 'POST':
        if 'update_info' in request.POST:
            user_form = UserEditForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, '¡Información de perfil actualizada con éxito!')
                return redirect('core:perfil') 
            else:
                messages.error(request, 'Error al actualizar la información. Revisa los campos.')
                edit_mode = True 

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                messages.success(request, '¡Tu contraseña ha sido cambiada con éxito! Por seguridad, te recomendamos iniciar sesión nuevamente.')
                return redirect('login')
            else:
                messages.error(request, 'Error al cambiar la contraseña. Revisa la contraseña actual y la nueva.')
                edit_mode = True 
    
    else:
        if request.GET.get('edit') == 'true':
            edit_mode = True

    user_form = UserEditForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
        
    context = {
        'user_form': user_form,
        'password_form': password_form,
        'edit_mode': edit_mode,
        'default_profile_pic': 'core/img/default_perfil.webp' 
    }
    return render(request, 'core/perfil.html', context)

# --- VISTAS DEL CARRITO DE COMPRAS ---

@login_required
def agregar_al_carrito(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        model_name = request.POST.get('model_name')
        quantity = int(request.POST.get('quantity', 1))

        ModelClass = PRODUCT_MODEL_MAP.get(model_name)
        if not ModelClass or not product_id:
            messages.error(request, "Error al intentar agregar el producto.")
            return redirect(request.META.get('HTTP_REFERER', 'core:tienda'))

        producto = get_object_or_404(ModelClass, id=product_id)

        # --- VALIDACIÓN DE STOCK ---
        if producto.stock <= 0:
            messages.error(request, f"Lo sentimos, '{producto.nombre}' está agotado y no se puede agregar al carrito.")
            return redirect(request.META.get('HTTP_REFERER', 'core:tienda'))

        carrito, created = Carrito.objects.get_or_create(usuario=request.user)

        lookup_kwargs = {f'{model_name}__id': product_id}
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, **lookup_kwargs)

        if created:
            setattr(item, model_name, producto)
            item.cantidad = max(1, quantity) 
            item.precio_unitario = producto.precio 
            message = f"'{producto.nombre}' se agregó a tu carrito."
        else:
            item.cantidad += max(1, quantity)
            message = f"Se actualizó la cantidad de '{producto.nombre}' en tu carrito."
        
        item.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': message, 'cart_count': carrito.items.count()})
        
        messages.success(request, message)

    return redirect(request.META.get('HTTP_REFERER', 'core:tienda'))

_CLAVES_DE_VALIDACION = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'memoria_ram': 'memoria_ram',
    'gabinete': 'gabinete',
    'refrigeracion': 'refrigeracion',
    'tarjeta_grafica': 'tarjeta_grafica',
    'fuente_de_poder': 'fuente_de_poder',
}

def _error_armado(message, estado='error', motivos=None, status=400):
    return JsonResponse({
        'status': 'error',
        'estado': estado,
        'message': message,
        'motivos': motivos if motivos is not None else [message],
    }, status=status)


from core.armado_recomendacion import (
    RECOMENDACIONES_POR_CATEGORIA as _RECOMENDACIONES,
    candidatos_para_categoria,
    serializar_candidatos_api,
)

_CLAVE_QUE_REEMPLAZA = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'memoria_ram': 'memoria_ram',
    'gabinete': 'gabinete',
    'refrigeracion_cooler': 'refrigeracion',
    'tarjeta_grafica': 'tarjeta_grafica',
    'fuente_de_poder': 'fuente_de_poder',
}

_TIPOS_ALMACENAMIENTO = frozenset({'almacenamiento_ssd', 'almacenamiento_hdd'})
_TIPOS_CON_CANTIDAD = _TIPOS_ALMACENAMIENTO | {'memoria_ram'}


def _cantidad_pedida(item):
    """Entero positivo. Si no viene cantidad, la pieza cuenta como una."""
    if 'cantidad' not in item or item.get('cantidad') in (None, ''):
        return 1
    valor = item.get('cantidad')
    if isinstance(valor, bool) or isinstance(valor, float):
        return None
    if isinstance(valor, str):
        if not valor.isdigit():
            return None
        valor = int(valor)
    if not isinstance(valor, int) or valor < 1:
        return None
    return valor


_UI_POR_TIPO = {
    'procesador': 'procesador',
    'placa_madre': 'placa_madre',
    'memoria_ram': 'memoria_ram',
    'gabinete': 'gabinete',
    'refrigeracion': 'refrigeracion_cooler',
    'tarjeta_grafica': 'tarjeta_grafica',
    'fuente_de_poder': 'fuente_de_poder',
    'almacenamiento_ssd': 'almacenamiento',
    'almacenamiento_hdd': 'almacenamiento',
}


def _error_seleccion(message):
    return JsonResponse({'status': 'error', 'message': message}, status=400)


def _cargar_seleccion(componentes, excluir_clave=None):
    """Carga las piezas enviadas. No escribe carrito, productos ni usuarios."""
    if not isinstance(componentes, list):
        return None, _error_seleccion('La selección no es válida.')

    seleccion = {}
    almacenamientos = []
    memorias = []
    grupos_disco = {}
    grupos_ram = {}
    vistos = set()
    for item in componentes:
        if not isinstance(item, dict):
            return None, _error_seleccion('La selección no es válida.')
        tipo = item.get('tipo') or item.get('model_name')
        clave_ui = _UI_POR_TIPO.get(tipo)
        if clave_ui is None:
            continue
        clave = _CLAVES_DE_VALIDACION.get(tipo)
        if excluir_clave is not None and clave == excluir_clave:
            continue
        cantidad = _cantidad_pedida(item)
        if cantidad is None:
            return None, _error_seleccion('La cantidad debe ser un entero positivo.')
        if tipo not in _TIPOS_CON_CANTIDAD and cantidad != 1:
            return None, _error_seleccion(
                'Solo el almacenamiento y la memoria RAM admiten varias unidades.'
            )
        ModelClass = PRODUCT_MODEL_MAP.get(tipo)
        try:
            product_id = int(item.get('id'))
        except (TypeError, ValueError):
            return None, _error_seleccion('Hay una pieza sin identificador válido.')
        producto = ModelClass.objects.filter(pk=product_id).first() if ModelClass else None
        if producto is None:
            return None, _error_seleccion('Una pieza de la selección ya no está disponible.')
        if tipo == 'memoria_ram':
            if product_id in grupos_ram:
                indice = grupos_ram[product_id]
                previa = memorias[indice]
                memorias[indice] = LineaRam(previa.producto, previa.cantidad + cantidad)
            else:
                grupos_ram[product_id] = len(memorias)
                memorias.append(LineaRam(producto, cantidad))
            continue
        if clave:
            if clave_ui in vistos:
                return None, _error_seleccion('Hay una pieza repetida en la selección.')
            vistos.add(clave_ui)
            seleccion[clave] = producto
            continue
        grupo = (tipo, product_id)
        if grupo in grupos_disco:
            almacenamientos[grupos_disco[grupo]]['cantidad'] += cantidad
        else:
            grupos_disco[grupo] = len(almacenamientos)
            almacenamientos.append({'tipo': tipo, 'producto': producto, 'cantidad': cantidad})
    return (seleccion, almacenamientos, memorias), None


def _serializar_evaluacion(evaluacion):
    return {
        'estado': evaluacion.estado,
        'etiqueta': evaluacion.etiqueta,
        'coincidencias': list(evaluacion.coincidencias),
        'motivos': list(evaluacion.motivos),
        'pendientes': list(evaluacion.pendientes),
        'advertencias': list(evaluacion.advertencias),
    }


@require_POST
def evaluar_armado(request):
    """Devuelve el estado actual de la selección usando validar_armado()."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error_seleccion('La solicitud no es válida.')

    cargado, error = _cargar_seleccion(payload.get('componentes') or [])
    if error:
        return error
    seleccion, almacenamientos, memorias = cargado
    resultado, por_categoria = evaluaciones_de_seleccion(
        seleccion,
        memorias_ram=memorias or None,
    )
    if almacenamientos:
        por_categoria['almacenamiento'] = EvaluacionCandidato(
            ESTADO_NO_EVALUADA,
            motivos=(MENSAJE_ALMACENAMIENTO,),
        )

    return JsonResponse({
        'status': 'success',
        'estado': resultado.estado,
        'texto': texto_del_armado(resultado, bool(almacenamientos), bool(seleccion) or bool(memorias)),
        'motivos': resultado.motivos_de_rechazo,
        'advertencias': resultado.advertencias,
        'piezas': {
            clave: _serializar_evaluacion(evaluacion)
            for clave, evaluacion in por_categoria.items()
        },
    })


_ORDEN_EXPORTACION = (
    ('procesador', 'procesador', 'Procesador (CPU)'),
    ('placa_madre', 'placa_madre', 'Placa Madre'),
    ('memoria_ram', 'memoria_ram', 'Memoria RAM'),
    ('refrigeracion', 'refrigeracion_cooler', 'Refrigeración CPU'),
    ('tarjeta_grafica', 'tarjeta_grafica', 'Tarjeta Gráfica (GPU)'),
    ('almacenamiento', 'almacenamiento', 'Almacenamiento'),
    ('gabinete', 'gabinete', 'Gabinete'),
    ('fuente_de_poder', 'fuente_de_poder', 'Fuente de Poder'),
)


def _filas_de_exportacion(seleccion, almacenamientos, memorias, por_categoria):
    filas = []
    aclaraciones = []
    for clave_modelo, clave_ui, componente in _ORDEN_EXPORTACION:
        if clave_ui == 'memoria_ram':
            if not memorias:
                continue
            evaluacion = por_categoria['memoria_ram']
            for indice, linea in enumerate(memorias):
                producto = linea.producto
                especificaciones = list(especificaciones_de(producto))
                if indice == 0:
                    especificaciones.extend(_notas_del_conjunto_ram(memorias, evaluacion))
                filas.append({
                    'componente': componente,
                    'producto': producto.nombre,
                    'cantidad': linea.cantidad,
                    'precio': pesos_enteros(producto.precio),
                    'estado': evaluacion.estado,
                    'texto_estado': texto_de_estado(evaluacion),
                    'especificaciones': especificaciones,
                })
            continue
        if clave_ui == 'almacenamiento':
            if not almacenamientos:
                continue
            evaluacion = por_categoria['almacenamiento']
            aclaracion = aclaracion_de_pieza(componente, evaluacion)
            if aclaracion:
                aclaraciones.append(aclaracion)
            for disco in almacenamientos:
                producto = disco['producto']
                filas.append({
                    'componente': componente,
                    'producto': producto.nombre,
                    'cantidad': disco['cantidad'],
                    'precio': pesos_enteros(producto.precio),
                    'estado': evaluacion.estado,
                    'texto_estado': texto_de_estado(evaluacion),
                    'especificaciones': especificaciones_de(producto),
                })
            continue
        producto = seleccion.get(clave_modelo)
        if producto is None:
            continue
        evaluacion = por_categoria[clave_ui]
        filas.append({
            'componente': componente,
            'producto': producto.nombre,
            'cantidad': 1,
            'precio': pesos_enteros(producto.precio),
            'estado': evaluacion.estado,
            'texto_estado': texto_de_estado(evaluacion),
            'especificaciones': especificaciones_de(producto),
        })
    return filas, aclaraciones


def _notas_del_conjunto_ram(memorias, evaluacion):
    notas = [('Aclaración', ACLARACION_RAM)]
    for aviso in evaluacion.advertencias:
        notas.append(('Advertencia', aviso))
    return notas


@require_POST
def exportar_armado(request):
    """Genera el Excel con una evaluación nueva. No reutiliza un resultado anterior."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error_seleccion('La solicitud no es válida.')

    cargado, error = _cargar_seleccion(payload.get('componentes') or [])
    if error:
        return error
    seleccion, almacenamientos, memorias = cargado
    if not seleccion and not almacenamientos and not memorias:
        return _error_seleccion('Selecciona al menos un componente.')

    resultado, por_categoria = evaluaciones_de_seleccion(
        seleccion,
        memorias_ram=memorias or None,
    )
    if almacenamientos:
        por_categoria['almacenamiento'] = EvaluacionCandidato(
            ESTADO_NO_EVALUADA,
            motivos=(MENSAJE_ALMACENAMIENTO,),
        )
    try:
        filas, aclaraciones = _filas_de_exportacion(
            seleccion, almacenamientos, memorias, por_categoria,
        )
    except ValueError as exc:
        return _error_seleccion(str(exc))
    for evaluacion in por_categoria.values():
        for pendiente in evaluacion.pendientes:
            if pendiente not in aclaraciones:
                aclaraciones.append(pendiente)
    if memorias and ACLARACION_RAM not in aclaraciones:
        aclaraciones.append(ACLARACION_RAM)
    for aviso in resultado.advertencias:
        if aviso not in aclaraciones:
            aclaraciones.append(aviso)

    contenido = libro_en_bytes(
        filas,
        {
            'estado': resultado.estado,
            'texto': texto_del_armado(resultado, bool(almacenamientos), bool(seleccion) or bool(memorias)),
            'motivos': resultado.motivos_de_rechazo,
            'aclaraciones': aclaraciones,
        },
        timezone.localtime(),
    )
    respuesta = HttpResponse(
        contenido,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    respuesta['Content-Disposition'] = 'attachment; filename="Presupuesto_armado_PC.xlsx"'
    return respuesta

_ORDEN_RECOMENDACION = {
    'compatible': 0,
    'incompleto': 1,
    'no_evaluada': 2,
    'datos_insuficientes': 3,
    'incompatible': 4,
}

def _orden_recomendado(candidato):
    return (
        0 if candidato['stock'] > 0 else 1,
        _ORDEN_RECOMENDACION[candidato['estado']],
        candidato['precio'],
        candidato['nombre'],
    )

@require_POST
def recomendar_armado(request):
    """Clasifica los candidatos de una categoría con las piezas ya elegidas."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'status': 'error', 'message': 'La solicitud no es válida.'}, status=400)

    categoria = payload.get('categoria')
    fuentes = _RECOMENDACIONES.get(categoria)
    if fuentes is None:
        return JsonResponse({'status': 'error', 'message': 'La categoría no es válida.'}, status=400)

    modo = payload.get('modo') or ''
    conserva_ram = categoria == 'memoria_ram' and modo in ('agregar', 'reemplazar')
    cargado, error = _cargar_seleccion(
        payload.get('componentes') or [],
        excluir_clave=None if conserva_ram else _CLAVE_QUE_REEMPLAZA.get(categoria),
    )
    if error:
        return error
    seleccion, _sin_regla, memorias = cargado

    if conserva_ram:
        candidatos = []
        for modelo, categoria_regla, model_name in fuentes:
            for producto in modelo.objects.all():
                lineas = _lineas_para_candidato(
                    memorias,
                    producto,
                    modo,
                    payload.get('reemplaza_id'),
                )
                if lineas is None:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'La línea de RAM que quieres reemplazar no está en la selección.',
                    }, status=400)
                evaluacion = evaluar_candidato(
                    categoria_regla,
                    producto,
                    memorias_ram=lineas,
                    **seleccion,
                )
                candidatos.append({
                    'id': producto.id,
                    'model_name': model_name,
                    'nombre': producto.nombre,
                    'precio': producto.precio,
                    'stock': producto.stock,
                    'estado': evaluacion.estado,
                    'etiqueta': evaluacion.etiqueta,
                    'coincidencias': list(evaluacion.coincidencias),
                    'motivos': list(evaluacion.motivos),
                    'pendientes': list(evaluacion.pendientes),
                    'advertencias': list(evaluacion.advertencias),
                    'seleccionable': producto.stock > 0,
                })
        candidatos.sort(key=_orden_recomendado)
        for candidato in candidatos:
            candidato['precio'] = str(candidato['precio'])
        return JsonResponse({'status': 'success', 'candidatos': candidatos})

    candidatos = candidatos_para_categoria(categoria, seleccion, memorias or None)
    return JsonResponse({'status': 'success', 'candidatos': serializar_candidatos_api(candidatos)})


def _sumar_linea_ram(lineas, producto, cantidad):
    nuevas = []
    sumada = False
    for linea in lineas:
        if linea.producto.pk == producto.pk:
            nuevas.append(LineaRam(linea.producto, linea.cantidad + cantidad))
            sumada = True
        else:
            nuevas.append(linea)
    if not sumada:
        nuevas.append(LineaRam(producto, cantidad))
    return nuevas


def _lineas_para_candidato(memorias, producto, modo, reemplaza_id):
    """Agregar suma el candidato al conjunto. Reemplazar sustituye una línea."""
    if modo == 'agregar':
        return _sumar_linea_ram(memorias, producto, 1)
    if modo != 'reemplazar':
        return [LineaRam(producto, 1)]
    if reemplaza_id in (None, ''):
        return [LineaRam(producto, 1)]
    try:
        buscado = int(reemplaza_id)
    except (TypeError, ValueError):
        return None
    cantidad = None
    restantes = []
    for linea in memorias:
        if linea.producto.id == buscado:
            cantidad = linea.cantidad
            continue
        restantes.append(linea)
    if cantidad is None:
        return None
    return _sumar_linea_ram(restantes, producto, cantidad)

@login_required
@require_POST
def agregar_armado_al_carrito(request):
    """Valida el armado completo y, solo si no hay conflicto, agrega todas las piezas."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error_armado('El armado enviado no es válido.')

    componentes = payload.get('componentes')
    if not isinstance(componentes, list) or not componentes:
        return _error_armado('Selecciona al menos un componente.', estado='incompleto')

    grupos = {}
    orden = []
    seleccion = {}

    for item in componentes:
        if not isinstance(item, dict):
            return _error_armado('El armado enviado no es válido.')

        model_name = item.get('tipo') or item.get('model_name')
        ModelClass = PRODUCT_MODEL_MAP.get(model_name)
        if not ModelClass:
            return _error_armado('Hay un componente con un tipo no válido.')

        cantidad = _cantidad_pedida(item)
        if cantidad is None:
            return _error_armado(
                'La cantidad debe ser un entero positivo.',
                estado='error',
                motivos=['La cantidad debe ser un entero positivo.'],
            )
        if model_name not in _TIPOS_CON_CANTIDAD and cantidad != 1:
            return _error_armado(
                'Solo el almacenamiento y la memoria RAM admiten varias unidades.',
                estado='error',
                motivos=['Solo el almacenamiento y la memoria RAM admiten varias unidades.'],
            )

        try:
            product_id = int(item.get('id'))
        except (TypeError, ValueError):
            return _error_armado('Hay un componente sin identificador válido.')

        producto = ModelClass.objects.filter(pk=product_id).first()
        if producto is None:
            return _error_armado('Uno de los componentes ya no está disponible.')

        if model_name not in _TIPOS_CON_CANTIDAD and any(nombre == model_name for nombre, _pid in orden):
            return _error_armado('Hay una pieza repetida en la selección.')

        clave_grupo = (model_name, product_id)
        if clave_grupo in grupos:
            grupos[clave_grupo]['cantidad'] += cantidad
        else:
            grupos[clave_grupo] = {'producto': producto, 'cantidad': cantidad}
            orden.append(clave_grupo)
        clave = _CLAVES_DE_VALIDACION.get(model_name)
        if clave and model_name != 'memoria_ram':
            seleccion[clave] = producto

    carrito_previo = Carrito.objects.filter(usuario=request.user).first()
    motivos_stock = []
    for model_name, product_id in orden:
        grupo = grupos[(model_name, product_id)]
        producto = grupo['producto']
        ya_en_carrito = 0
        if carrito_previo is not None:
            existente = ItemCarrito.objects.filter(
                carrito=carrito_previo,
                **{f'{model_name}__id': producto.id},
            ).first()
            ya_en_carrito = existente.cantidad if existente else 0
        if ya_en_carrito + grupo['cantidad'] > producto.stock:
            motivos_stock.append(
                f"'{producto.nombre}' no tiene stock suficiente: "
                f"se piden {grupo['cantidad']} y hay {producto.stock} "
                f"({ya_en_carrito} ya en el carrito)."
            )
    if motivos_stock:
        return _error_armado(
            'No se agregó el armado al carrito.',
            estado='error',
            motivos=motivos_stock,
        )

    memorias = [
        LineaRam(grupos[clave]['producto'], grupos[clave]['cantidad'])
        for clave in orden
        if clave[0] == 'memoria_ram'
    ]
    resultado = validar_armado(**seleccion, memorias_ram=memorias or None)
    if resultado.bloquea_agregar:
        return _error_armado(
            'No se agregó el armado al carrito.',
            estado=resultado.estado,
            motivos=resultado.motivos_de_rechazo,
        )

    with transaction.atomic():
        carrito, _created = Carrito.objects.get_or_create(usuario=request.user)
        for model_name, product_id in orden:
            grupo = grupos[(model_name, product_id)]
            producto = grupo['producto']
            lookup_kwargs = {f'{model_name}__id': producto.id}
            item, created = ItemCarrito.objects.get_or_create(carrito=carrito, **lookup_kwargs)
            if created:
                setattr(item, model_name, producto)
                item.cantidad = grupo['cantidad']
                item.precio_unitario = producto.precio
            else:
                item.cantidad += grupo['cantidad']
            item.save()

    return JsonResponse({
        'status': 'success',
        'estado': resultado.estado,
        'message': 'Se agregaron los componentes del armado al carrito.',
        'motivos': [],
    })

@login_required
def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    nombre_producto = item.get_related_product().nombre
    item.delete()
    messages.warning(request, f"'{nombre_producto}' fue eliminado de tu carrito.")
    return redirect('core:carrito')

@login_required
def actualizar_carrito(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
        new_quantity = int(request.POST.get('quantity', 1))

        if new_quantity > 0:
            item.cantidad = new_quantity
            item.save()
            messages.success(request, "Cantidad actualizada.")
        else:
            return eliminar_del_carrito(request, item_id)
            
    return redirect('core:carrito')

# --- VISTAS DE FAVORITOS ---

@login_required
def mostrar_favoritos(request):
    favoritos = Favorito.objects.filter(usuario=request.user).order_by('-fecha_agregado')
    
    productos_favoritos = []
    for fav in favoritos:
        producto = fav.get_related_product()
        if producto:
            model_name = None
            for key, model_class in PRODUCT_MODEL_MAP.items():
                if isinstance(producto, model_class):
                    model_name = key
                    break
            productos_favoritos.append({'producto': producto, 'model_name': model_name, 'fav_id': fav.id})

    context = {
        'productos_favoritos': productos_favoritos
    }
    return render(request, 'core/favoritos.html', context)

@login_required
def toggle_favorito(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_id = request.POST.get('product_id')
        model_name = request.POST.get('model_name')

        ModelClass = PRODUCT_MODEL_MAP.get(model_name)
        if not ModelClass or not product_id:
            return JsonResponse({'status': 'error', 'message': 'Datos inválidos.'}, status=400)

        lookup_kwargs = {f'{model_name}__id': product_id, 'usuario': request.user}
        
        try:
            favorito, created = Favorito.objects.get_or_create(**lookup_kwargs)
            if created:
                producto = get_object_or_404(ModelClass, id=product_id)
                setattr(favorito, model_name, producto)
                favorito.save()
                status, message = 'added', '¡Agregado a favoritos!'
            else:
                favorito.delete()
                status, message = 'removed', 'Eliminado de favoritos.'
            favorite_count = Favorito.objects.filter(usuario=request.user).count()
            return JsonResponse({'status': status, 'message': message, 'favorite_count': favorite_count})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Petición no válida.'}, status=400)

@login_required
def eliminar_favorito(request, fav_id):
    favorito = get_object_or_404(Favorito, id=fav_id, usuario=request.user)
    favorito.delete()
    messages.success(request, "Producto eliminado de tus favoritos.")
    return redirect('core:favoritos')

# --- VISTA DE COMENTARIOS ---

@login_required
def agregar_comentario(request, model_name, pk):
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        ModelClass = PRODUCT_MODEL_MAP.get(model_name)
        
        if not ModelClass:
            raise Http404("Tipo de producto no encontrado.")
        
        producto = get_object_or_404(ModelClass, pk=pk)

        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.usuario = request.user
            setattr(comentario, model_name, producto)
            comentario.save()
            messages.success(request, "¡Gracias por tu reseña! Tu comentario ha sido publicado.")
        else:
            messages.error(request, "Hubo un error al publicar tu comentario. Por favor, revisa los campos.")

    return redirect('core:detalle', model_name=model_name, pk=pk)

# --- VISTAS DE PEDIDOS ---

def _estado_visible(pedido, verificando_id):
    if pedido.estado == 'PAGADO':
        return 'pagado'
    if pedido.estado == 'CANCELADO':
        return 'cancelado'
    if pedido.estado == 'PENDIENTE' and verificando_id == pedido.id and not (pedido.paypal_transaccion_id or '').strip():
        return 'verificando'
    if pedido.estado == 'PENDIENTE':
        return 'esperando'
    return 'otro'


def _puede_reintentar(pedido):
    return (
        pedido.estado == 'PENDIENTE'
        and not (pedido.paypal_transaccion_id or '').strip()
        and not PagoBoleta.objects.filter(pedido_id=pedido.id).exists()
    )


@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_pedido')
    verificando_id = request.session.get(SESION_VERIFICANDO)
    context = {
        'pedidos': pedidos,
        'verificando_id': verificando_id,
    }
    return render(request, 'core/mis_pedidos.html', context)

@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    if request.session.get(SESION_VERIFICANDO) == pedido.id and pedido.estado != 'PENDIENTE':
        request.session.pop(SESION_VERIFICANDO, None)

    reintento = _puede_reintentar(pedido)
    form_paypal = None
    if reintento:
        form_paypal, _total_usd = formulario_paypal(pedido)

    context = {
        'pedido': pedido,
        'form_paypal': form_paypal,
        'estado_pago': _estado_visible(pedido, request.session.get(SESION_VERIFICANDO)),
        'reintento_disponible': reintento,
        **contexto_conversion(pedido),
    }
    return render(request, 'core/detalle_pedido.html', context)

@login_required
@transaction.atomic 
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    if pedido.estado != 'PENDIENTE':
        messages.error(request, "Solo se pueden cancelar pedidos pendientes de pago.")
        return redirect('core:detalle_pedido', pedido_id=pedido.id)

    pedido.estado = 'CANCELADO'
    pedido.save()

    messages.success(request, f"El Pedido #{pedido.id} ha sido cancelado correctamente.")
    return redirect('core:mis_pedidos')

@login_required
def ver_boleta(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user, estado='PAGADO')
    
    boleta = PagoBoleta.objects.filter(pedido_id=pedido.id).first()
    context = {
        'pedido': pedido,
        'items_pedido': pedido.items_pedido.all(),
        'fecha_pago': None if boleta is None else boleta.fecha_pago,
        **contexto_conversion(pedido),
    }
    
    return render(request, 'core/boleta.html', context)