import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError

from core.calificaciones import validar_media_estrella
from core.telefonos import PAISES, normalizar_telefono
from core.widgets import EstrellasWidget
from .models import *

_NOMBRE_CONTACTO = re.compile(r"^[^\W\d_]+(?:[ '\u2019-][^\W\d_]+)*$")


class LoginForm(AuthenticationForm):
    """Los límites coinciden con el usuario de Django. No agregan reglas nuevas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['maxlength'] = '150'
        self.fields['password'].widget.attrs['maxlength'] = '4096'


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        max_length=254,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'placeholder': 'ejemplo@correo.com',
            'class': 'form-control',
            'maxlength': '254',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['maxlength'] = '150'
        self.fields['first_name'].widget.attrs['maxlength'] = '150'
        self.fields['last_name'].widget.attrs['maxlength'] = '150'
        self.fields['password1'].widget.attrs['maxlength'] = '4096'
        self.fields['password2'].widget.attrs['maxlength'] = '4096'

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
    
class UserEditForm(UserChangeForm):
    password = None 
    
    email = forms.EmailField(
        required=True,
        max_length=254,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'maxlength': '254'}),
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '150'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '150'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '150'}),
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso por otra cuenta.")
        return email

class ComentarioForm(forms.ModelForm):
    calificacion = forms.DecimalField(
        max_digits=2,
        decimal_places=1,
        label='Calificación',
        validators=[validar_media_estrella],
        widget=EstrellasWidget(),
        error_messages={
            'required': 'Selecciona una calificación.',
            'invalid': 'La calificación debe ir de 0,5 a 5, en medios puntos.',
        },
    )

    class Meta:
        model = Comentario
        fields = ['titulo', 'texto', 'calificacion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ¡Excelente producto!',
                'maxlength': '100',
            }),
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': '1500',
                'placeholder': 'Escribe tu reseña aquí...',
                'data-contador': 'contador-resena',
            }),
        }
        labels = {
            'titulo': 'Título de tu reseña',
            'texto': 'Tu opinión',
        }
        error_messages = {
            'titulo': {'max_length': 'El título admite como máximo 100 caracteres.'},
            'texto': {'max_length': 'La reseña admite como máximo 1500 caracteres.'},
        }

    def clean_calificacion(self):
        return validar_media_estrella(self.cleaned_data.get('calificacion'))


class ContactoForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        label='Nombre',
        error_messages={
            'required': 'Ingresa tu nombre.',
            'max_length': 'El nombre admite como máximo 100 caracteres.',
        },
    )
    email = forms.EmailField(
        max_length=254,
        label='Correo',
        error_messages={
            'required': 'Ingresa tu correo.',
            'invalid': 'Ingresa un correo válido.',
            'max_length': 'El correo admite como máximo 254 caracteres.',
        },
    )
    telefono_pais = forms.ChoiceField(
        required=False,
        initial='CL',
        choices=[(pais['codigo'], pais['nombre']) for pais in PAISES],
        label='País',
    )
    telefono_nacional = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
    )
    asunto = forms.CharField(
        max_length=120,
        label='Asunto',
        error_messages={
            'required': 'Ingresa un asunto.',
            'max_length': 'El asunto admite como máximo 120 caracteres.',
        },
    )
    mensaje = forms.CharField(
        max_length=2000,
        label='Mensaje',
        widget=forms.Textarea,
        error_messages={
            'required': 'Ingresa un mensaje.',
            'max_length': 'El mensaje admite como máximo 2000 caracteres.',
        },
    )

    def clean_nombre(self):
        nombre = ' '.join((self.cleaned_data.get('nombre') or '').split())
        if _NOMBRE_CONTACTO.fullmatch(nombre) is None:
            raise forms.ValidationError(
                'El nombre solo puede incluir letras, espacios, guiones y apóstrofes.'
            )
        return nombre

    def clean(self):
        datos = super().clean()
        nacional = (datos.get('telefono_nacional') or '').strip()
        if not nacional:
            datos['telefono'] = ''
            return datos
        try:
            datos['telefono'] = normalizar_telefono(datos.get('telefono_pais') or 'CL', nacional)
        except ValidationError as error:
            self.add_error('telefono_nacional', error)
        return datos
