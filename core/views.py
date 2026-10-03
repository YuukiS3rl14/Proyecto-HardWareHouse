from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash 
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from .forms import *
import json
import uuid

from django.conf import settings
from django.db import transaction 
from django.db.models import Q, Avg, Count
from .models import *
from paypal.standard.forms import PayPalPaymentsForm
from django.urls import reverse
from decimal import Decimal

# Create your views here.

def mostrarIndex(request):
    proveedores_con_logo = Proveedor.objects.filter(logo__isnull=False).exclude(logo='').order_by('nombre').distinct()
    
    context = {
        'proveedores': proveedores_con_logo
    }
    return render(request, 'core/index.html', context)

def mostrarArmado(request):    
    def get_component_data(model, fields):
        components = []
        for item in model.objects.all():
            data = {'id': item.id}
            for field in fields:
                data[field] = getattr(item, field)
            data['imagen'] = item.imagen.url if item.imagen else None
            components.append(data)
        return components

    componentes = {
        'placa_madre': get_component_data(PlacaMadre, ['nombre', 'precio', 'socket_cpu', 'tipo_ram_soportado', 'formato', 'chipset', 'ranuras_ram', 'stock']),
        'procesador': get_component_data(Procesador, ['nombre', 'precio', 'socket', 'nucleos', 'frecuencia_base', 'stock']),
        'memoria_ram': get_component_data(MemoriaRam, ['nombre', 'precio', 'tipo_ddr', 'capacidad_gb', 'velocidad_mhz', 'stock']),
        'tarjeta_grafica': get_component_data(TarjetaGrafica, ['nombre', 'precio', 'vram_gb', 'tipo_memoria', 'interfaz', 'stock']),
        'almacenamiento': get_component_data(AlmacenamientoSSD, ['nombre', 'precio', 'capacidad_gb', 'formato', 'stock']) + get_component_data(AlmacenamientoHDD, ['nombre', 'precio', 'capacidad_gb', 'stock']),
        'gabinete': get_component_data(Gabinete, ['nombre', 'precio', 'formato_soporte', 'stock']),
        'fuente_de_poder': get_component_data(FuenteDePoder, ['nombre', 'precio', 'potencia_watts', 'stock']),
        'refrigeracion_cooler': get_component_data(RefrigeracionCooler, ['nombre', 'precio', 'socket_compatibles', 'tipo', 'tamanho_radiador_mm', 'stock']),
    }

    for categoria in componentes:
        for componente in componentes[categoria]:
            componente['precio'] = str(componente['precio'])

    context = {'componentes': componentes}
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


    total_clp = carrito.get_total_precio()
    # Convertimos el total a USD para PayPal, redondeando a 2 decimales
    total_usd = (total_clp / Decimal(settings.CLP_TO_USD_RATE)).quantize(Decimal('0.01'))

    # Creamos un pedido PENDIENTE
    # Usamos transaction.atomic para asegurar que la creación del pedido y sus items sea una operación única
    with transaction.atomic():
        # Siempre creamos un nuevo pedido para cada checkout.
        # Esto evita reutilizar pedidos antiguos y asegura un invoice único.
        pedido = Pedido.objects.create(
            usuario=request.user,
            estado='PENDIENTE',
            total_monto=total_clp,
            direccion_envio="Por definir" # O la dirección que tengas del usuario
        )

        for item_carrito in items_carrito:
            producto = item_carrito.get_related_product()
            ItemPedido.objects.create(
                pedido=pedido,
                producto_nombre=producto.nombre,
                producto_tipo=producto.categoria,
                precio_unitario=item_carrito.precio_unitario,
                cantidad=item_carrito.cantidad
            )




    # Diccionario para el botón de PayPal
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": f"{total_usd:.2f}",
        "item_name": f"Pedido #{pedido.id} - HardWareHouse",
        "invoice": str(pedido.id), 
        "currency_code": "USD",
        "notify_url": settings.SITE_URL + reverse('paypal-ipn'), 
        "return_url": settings.SITE_URL + reverse('core:payment_success'),
        "cancel_return": settings.SITE_URL + reverse('core:payment_failed'),
    }

    form_paypal = PayPalPaymentsForm(initial=paypal_dict)

    context = {
        'pedido': pedido,
        'items_pedido': pedido.items_pedido.all(),
        'total_clp': total_clp,
        'total_usd': total_usd,
        'clp_to_usd_rate': settings.CLP_TO_USD_RATE,
        'form_paypal': form_paypal,
    }
    return render(request, 'core/checkout.html', context)

@login_required
def paymentSuccess(request):
    # Aquí es donde PayPal redirige al usuario después de un pago exitoso.
    # La lógica de actualización del pedido se maneja mejor con la señal de IPN de django-paypal.
    # Por ahora, solo vaciamos el carrito y mostramos un mensaje.
    carrito = Carrito.objects.filter(usuario=request.user).first()
    if carrito:
        carrito.items.all().delete()
    
    messages.success(request, "¡Tu pago ha sido procesado con éxito! Tu pedido está siendo preparado.")
    return render(request, 'core/payment_success.html')

@login_required
def paymentFailed(request):
    messages.error(request, "El pago falló o fue cancelado. Puedes intentarlo de nuevo desde 'Mis Pedidos'.")
    return render(request, 'core/payment_failed.html')

def mostrarContacto(request):
    return render(request, 'core/contacto.html')

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

def mostrarTienda(request):
    query = request.GET.get('q')
    selected_categorias = request.GET.getlist('categoria')
    selected_proveedores = request.GET.getlist('proveedor')
    selected_precio = request.GET.get('precio')

    productos_con_modelo = [] # Cambiamos el nombre para mayor claridad
    modelos = [
        Procesador, TarjetaGrafica, MemoriaRam, PlacaMadre, 
        AlmacenamientoSSD, AlmacenamientoHDD, Gabinete, FuenteDePoder, 
        RefrigeracionCooler, Ventilador
    ]

    # --- 2. Lógica de Filtrado ---
    no_filters_applied = not query and not selected_categorias and not selected_proveedores and not selected_precio
    if no_filters_applied:
        for modelo in modelos:
            model_name = modelo._meta.model_name.replace('tarjetagrafica', 'tarjeta_grafica').replace('memoriaram', 'memoria_ram').replace('placamadre', 'placa_madre').replace('almacenamientossd', 'almacenamiento_ssd').replace('almacenamientohdd', 'almacenamiento_hdd').replace('fuentedepoder', 'fuente_de_poder').replace('refrigeracioncooler', 'refrigeracion')
            if modelo == RefrigeracionCooler: 
                model_name = 'refrigeracion'
            productos_recientes = modelo.objects.order_by('-id')[:5]
            for producto in productos_recientes:
                productos_con_modelo.append((producto, model_name))
    else:
        for modelo in modelos:
            # a. Filtro por Categoría
            categoria_modelo = modelo._meta.get_field('categoria').default
            if selected_categorias and categoria_modelo not in selected_categorias:
                continue

            # b. Construcción de la consulta
            model_name = modelo._meta.model_name.replace('tarjetagrafica', 'tarjeta_grafica').replace('memoriaram', 'memoria_ram').replace('placamadre', 'placa_madre').replace('almacenamientossd', 'almacenamiento_ssd').replace('almacenamientohdd', 'almacenamiento_hdd').replace('fuentedepoder', 'fuente_de_poder').replace('refrigeracioncooler', 'refrigeracion')
            if modelo == RefrigeracionCooler: 
                model_name = 'refrigeracion'
            qs = modelo.objects.all()
            
            if query:
                search_query = (
                    Q(nombre__icontains=query) | 
                    Q(proveedor__nombre__icontains=query) |
                    Q(categoria__icontains=query)
                )
                qs = qs.filter(search_query)

            # Filtro por Proveedor
            if selected_proveedores:
                qs = qs.filter(proveedor__id__in=selected_proveedores)

            # Filtro por Precio
            if selected_precio:
                if selected_precio == 'p1': qs = qs.filter(precio__lte=100000)
                elif selected_precio == 'p2': qs = qs.filter(precio__gt=100000, precio__lte=300000)
                elif selected_precio == 'p3': qs = qs.filter(precio__gt=300000, precio__lte=600000)
                elif selected_precio == 'p4': qs = qs.filter(precio__gt=600000)

            for producto in qs:
                productos_con_modelo.append((producto, model_name))

    # --- 3. Obtener IDs de productos favoritos del usuario ---
    favoritos_ids = {}
    if request.user.is_authenticated:
        user_favoritos = Favorito.objects.filter(usuario=request.user).select_related('procesador', 'tarjeta_grafica', 'memoria_ram', 'placa_madre', 'almacenamiento_ssd', 'almacenamiento_hdd', 'gabinete', 'fuente_de_poder', 'refrigeracion', 'ventilador')
        for fav in user_favoritos:
            prod = fav.get_related_product()
            if prod:
                model_name_template = prod._meta.model_name.replace('_', '')
                favoritos_ids[f"{model_name_template}-{prod.id}"] = True

    # --- 3. Preparar contexto para la plantilla ---
    # Obtenemos todas las categorías y proveedores para mostrarlos en los filtros
    categorias_disponibles = sorted(list(set(m._meta.get_field('categoria').default for m in modelos)))
    proveedores_disponibles = Proveedor.objects.all().order_by('nombre')
        
    context = {
        'productos': productos_con_modelo,
        'favoritos_ids': favoritos_ids,
        'query': query,
        'categorias': categorias_disponibles,
        'proveedores': proveedores_disponibles,
        'selected_categorias': selected_categorias,
        'selected_proveedores': [int(p) for p in selected_proveedores], # Convertir a int para la plantilla
        'selected_precio': selected_precio,
    }
    return render(request, 'core/tienda.html', context)

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

@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_pedido')
    context = {
        'pedidos': pedidos
    }
    return render(request, 'core/mis_pedidos.html', context)

@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    form_paypal = None
    if pedido.estado == 'PENDIENTE':
        total_usd = (pedido.total_monto / Decimal(settings.CLP_TO_USD_RATE)).quantize(Decimal('0.01'))
        paypal_dict = {
            "business": settings.PAYPAL_RECEIVER_EMAIL,
            "amount": f"{total_usd:.2f}",
            "item_name": f"Pedido #{pedido.id} - HardWareHouse",
            "invoice": str(pedido.id),
            "currency_code": "USD",
            "notify_url": settings.SITE_URL + reverse('paypal-ipn'), 
            "return_url": settings.SITE_URL + reverse('core:payment_success'),
            "cancel_return": settings.SITE_URL + reverse('core:payment_failed'),
        }
        form_paypal = PayPalPaymentsForm(initial=paypal_dict)

    context = {
        'pedido': pedido,
        'form_paypal': form_paypal,
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
    
    context = {
        'pedido': pedido,
        'items_pedido': pedido.items_pedido.all(),
    }
    
    return render(request, 'core/boleta.html', context)