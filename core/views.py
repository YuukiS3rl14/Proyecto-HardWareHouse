from django.shortcuts import render, redirect, get_object_or_404
import json
from django.http import Http404, JsonResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import *
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash 
from django.db import transaction 
from django.db.models import Q, Avg, Count
from .models import *

# Create your views here.

def mostrarIndex(request):
    # Obtenemos todos los proveedores que tienen un logo para mostrarlos en el carrusel.
    proveedores_con_logo = Proveedor.objects.filter(logo__isnull=False).exclude(logo='').order_by('nombre').distinct()
    
    context = {
        'proveedores': proveedores_con_logo
    }
    return render(request, 'core/index.html', context)

def mostrarArmado(request):    
    # Diccionario para almacenar todos los componentes que se pasarán a la plantilla
    componentes = {
        'procesador': list(Procesador.objects.values('id', 'nombre', 'precio', 'socket', 'stock')),
        'placa_madre': list(PlacaMadre.objects.values('id', 'nombre', 'precio', 'socket_cpu', 'tipo_ram_soportado', 'formato', 'stock')),
        'memoria_ram': list(MemoriaRam.objects.values('id', 'nombre', 'precio', 'tipo_ddr', 'stock')),
        # DEBUG: Imprimir las placas madre recuperadas
        # print(f"DEBUG: Placas Madre recuperadas: {list(PlacaMadre.objects.values('id', 'nombre', 'precio', 'socket_cpu', 'tipo_ram_soportado', 'formato', 'stock'))}")
        'tarjeta_grafica': list(TarjetaGrafica.objects.values('id', 'nombre', 'precio', 'stock')),
        'almacenamiento': list(AlmacenamientoSSD.objects.values('id', 'nombre', 'precio', 'stock')) + list(AlmacenamientoHDD.objects.values('id', 'nombre', 'precio', 'stock')),
        'fuente_de_poder': list(FuenteDePoder.objects.values('id', 'nombre', 'precio', 'stock')),
        'gabinete': list(Gabinete.objects.values('id', 'nombre', 'precio', 'formato_soporte', 'stock')),
        'refrigeracion_cooler': list(RefrigeracionCooler.objects.values('id', 'nombre', 'precio', 'socket_compatibles', 'stock')),
    }

    # Convertimos los precios a string para que el JSON no tenga problemas con el tipo Decimal
    for categoria in componentes:
        for componente in componentes[categoria]:
            componente['precio'] = str(componente['precio'])

    context = {
        'componentes_json': json.dumps(componentes)
    }
    return render(request, 'core/armado.html', context)

@login_required
def mostrarCarrito(request):
    # Obtenemos o creamos el carrito para el usuario actual
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    
    # Obtenemos todos los items del carrito
    items = carrito.items.all().order_by('id')
    
    # Calculamos el total
    total_carrito = carrito.get_total_precio()
    
    context = {
        'items': items,
        'total_carrito': total_carrito,
    }
    return render(request, 'core/carrito.html', context)

@login_required
def mostrarCheckout(request):
    return render(request, 'core/checkout.html')

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
    """
    Muestra los detalles de un producto específico, buscándolo en el modelo correcto.
    """
    # 1. Normalizar el nombre del modelo
    model_name_lower = model_name.lower()
    ModelClass = PRODUCT_MODEL_MAP.get(model_name_lower)
    
    if not ModelClass:
        raise Http404("Tipo de producto no encontrado.")
        
    # 2. Obtener el objeto específico
    producto = get_object_or_404(ModelClass, pk=pk)
    
    # 3. Verificar si el producto está en favoritos (si el usuario está logueado)
    is_favorito = False
    if request.user.is_authenticated:
        lookup_kwargs = {f'{model_name_lower}__id': pk, 'usuario': request.user}
        is_favorito = Favorito.objects.filter(**lookup_kwargs).exists()

    # 4. Obtener comentarios, promedio de calificación y total de comentarios
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
        'model_name': model_name_lower, # Pasamos el nombre del modelo a la plantilla
        'is_favorito': is_favorito,
        'comentarios': comentarios,
        'promedio_calificacion': promedio_calificacion,
        'total_comentarios': total_comentarios,
        'comentario_form': ComentarioForm(),
    }
    return render(request, 'core/detalle.html', context)

def mostrarTienda(request):
    # --- 1. Obtener parámetros de la URL ---
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
    # Si no hay filtros ni búsqueda, mostramos los productos más recientes.
    no_filters_applied = not query and not selected_categorias and not selected_proveedores and not selected_precio
    if no_filters_applied:
        for modelo in modelos:
            # Corregimos el model_name para que coincida con las claves del MAP y los campos del modelo
            model_name = modelo._meta.model_name.replace('tarjetagrafica', 'tarjeta_grafica').replace('memoriaram', 'memoria_ram').replace('placamadre', 'placa_madre').replace('almacenamientossd', 'almacenamiento_ssd').replace('almacenamientohdd', 'almacenamiento_hdd').replace('fuentedepoder', 'fuente_de_poder').replace('refrigeracioncooler', 'refrigeracion')
            if modelo == RefrigeracionCooler: # Caso especial para RefrigeracionCooler
                model_name = 'refrigeracion'
            productos_recientes = modelo.objects.order_by('-id')[:5]
            for producto in productos_recientes:
                productos_con_modelo.append((producto, model_name))
    else:
        # Si hay filtros o búsqueda, los aplicamos.
        for modelo in modelos:
            # a. Filtro por Categoría
            # Si se seleccionaron categorías y la del modelo actual no está en la lista, lo saltamos.
            categoria_modelo = modelo._meta.get_field('categoria').default
            if selected_categorias and categoria_modelo not in selected_categorias:
                continue

            # b. Construcción de la consulta
            # Corregimos el model_name para que coincida con las claves del MAP y los campos del modelo
            model_name = modelo._meta.model_name.replace('tarjetagrafica', 'tarjeta_grafica').replace('memoriaram', 'memoria_ram').replace('placamadre', 'placa_madre').replace('almacenamientossd', 'almacenamiento_ssd').replace('almacenamientohdd', 'almacenamiento_hdd').replace('fuentedepoder', 'fuente_de_poder').replace('refrigeracioncooler', 'refrigeracion')
            if modelo == RefrigeracionCooler: # Caso especial para RefrigeracionCooler
                model_name = 'refrigeracion'
            qs = modelo.objects.all()
            
            # Filtro por texto (query 'q')
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
                return redirect(to='login')
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
                return redirect('perfil') 
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
            return redirect(request.META.get('HTTP_REFERER', 'tienda'))

        producto = get_object_or_404(ModelClass, id=product_id)
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)

        # Construimos el filtro para buscar el item en el carrito
        # Ejemplo: {'procesador_id': product_id}
        lookup_kwargs = {f'{model_name}__id': product_id}
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, **lookup_kwargs)

        if created:
            # Si es un nuevo item, asignamos el producto y la cantidad
            setattr(item, model_name, producto)
            item.cantidad = max(1, quantity) # Asegurarse que la cantidad sea al menos 1
            item.precio_unitario = producto.precio # Guardamos el precio actual
            message = f"'{producto.nombre}' se agregó a tu carrito."
        else:
            # Si el item ya existía, solo actualizamos la cantidad
            item.cantidad += max(1, quantity)
            message = f"Se actualizó la cantidad de '{producto.nombre}' en tu carrito."
        
        item.save()

        # Si es una petición AJAX, devolvemos JSON. Si no, redirigimos.
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': message})
        
        # Si NO es AJAX, sí agregamos el mensaje a la sesión antes de redirigir.
        messages.success(request, message)

    return redirect(request.META.get('HTTP_REFERER', 'tienda'))

@login_required
def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    nombre_producto = item.get_related_product().nombre
    item.delete()
    messages.warning(request, f"'{nombre_producto}' fue eliminado de tu carrito.")
    return redirect('carrito')

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
            # Si la cantidad es 0 o menos, eliminamos el item
            return eliminar_del_carrito(request, item_id)
            
    return redirect('carrito')

# --- VISTAS DE FAVORITOS ---

@login_required
def mostrar_favoritos(request):
    favoritos = Favorito.objects.filter(usuario=request.user).order_by('-fecha_agregado')
    
    productos_favoritos = []
    for fav in favoritos:
        producto = fav.get_related_product()
        if producto:
            # Buscamos la clave correcta en el PRODUCT_MODEL_MAP que corresponde a la clase del producto
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
                # Se acaba de crear, así que se agregó a favoritos
                producto = get_object_or_404(ModelClass, id=product_id)
                setattr(favorito, model_name, producto)
                favorito.save()
                return JsonResponse({'status': 'added', 'message': '¡Agregado a favoritos!'})
            else:
                # Ya existía, así que lo eliminamos
                favorito.delete()
                return JsonResponse({'status': 'removed', 'message': 'Eliminado de favoritos.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Petición no válida.'}, status=400)

@login_required
def eliminar_favorito(request, fav_id):
    favorito = get_object_or_404(Favorito, id=fav_id, usuario=request.user)
    favorito.delete()
    messages.success(request, "Producto eliminado de tus favoritos.")
    return redirect('favoritos')

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
            setattr(comentario, model_name, producto) # Asocia el comentario con el producto correcto
            comentario.save()
            messages.success(request, "¡Gracias por tu reseña! Tu comentario ha sido publicado.")
        else:
            messages.error(request, "Hubo un error al publicar tu comentario. Por favor, revisa los campos.")

    return redirect('detalle', model_name=model_name, pk=pk)