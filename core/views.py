from django.shortcuts import render

# Create your views here.

def mostrarIndex(request):
    return render(request, 'core/index.html')