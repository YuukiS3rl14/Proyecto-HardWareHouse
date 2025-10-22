from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import *
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash 
from django.db import transaction 

# Create your views here.

def mostrarIndex(request):
    return render(request, 'core/index.html')

def mostrarArmado(request):
    return render(request, 'core/armado.html')

@login_required
def mostrarCarrito(request):
    return render(request, 'core/carrito.html')

@login_required
def mostrarCheckout(request):
    return render(request, 'core/checkout.html')

def mostrarContacto(request):
    return render(request, 'core/contacto.html')

def mostrarDetalle(request):
    return render(request, 'core/detalle.html')

def mostrarTienda(request):
    return render(request, 'core/tienda.html')

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
                update_session_auth_hash(request, user) 
                messages.success(request, '¡Tu contraseña ha sido cambiada con éxito! Por seguridad, te recomendamos iniciar sesión nuevamente.')
                return redirect('perfil')
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