from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from .models import *

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com', 'class': 'form-control'})
    )

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
    
    email = forms.EmailField(required=True, label='Correo Electrónico',
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso por otra cuenta.")
        return email

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['titulo', 'texto', 'calificacion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ¡Excelente producto!'
            }),
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu reseña aquí...'
            }),
            'calificacion': forms.Select(choices=[(i, f'{i} estrellas') for i in range(1, 6)], attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'titulo': 'Título de tu reseña',
            'texto': 'Tu opinión',
            'calificacion': 'Calificación'
        }
