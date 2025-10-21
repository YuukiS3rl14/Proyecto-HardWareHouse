from django.shortcuts import render

# Create your views here.

def mostrarIndex(request):
    return render(request, 'core/index.html')

def mostrarArmado(request):
    return render(request, 'core/armado.html')

def mostrarCarrito(request):
    return render(request, 'core/carrito.html')

def mostrarCheckout(request):
    return render(request, 'core/checkout.html')

def mostrarContacto(request):
    return render(request, 'core/contacto.html')

def mostrarDetalle(request):
    return render(request, 'core/detalle.html')

def mostrarTienda(request):
    return render(request, 'core/tienda.html')

def mostrarLogin(request):
    return render(request, 'core/registration/login.html')

def mostrarRegistro(request):
    return render(request, 'core/registration/registro.html')