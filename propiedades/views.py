from django.shortcuts import render, get_object_or_404
from .models import Propiedad

# --- VISTAS ---

def inicio(request):
    # Filtramos:
    # 1. Estado: Disponible o Reservado
    # 2. Checkbox: Que esté marcada como 'esta_publicada'
    # 3. Excluir: Que NO sea un pack interno (TERRA_WEB)
    propiedades_destacadas = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO'],
        esta_publicada=True
    ).exclude(
        plataformas_publicadas__contains='TERRA_WEB'
    ).order_by('-fecha_ingreso')[:3]
    
    context = {
        'propiedades': propiedades_destacadas
    }
    return render(request, 'inicio.html', context)

def nosotros(request):
    propiedades_destacadas = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO'],
        esta_publicada=True
    ).exclude(
        plataformas_publicadas__contains='TERRA_WEB'
    ).order_by('-fecha_ingreso')[:3]
    
    return render(request, 'nosotros.html', {'propiedades': propiedades_destacadas})

def catalogo(request):
    # Catálogo completo visible
    todas_las_propiedades = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO'],
        esta_publicada=True
    ).exclude(
        plataformas_publicadas__contains='TERRA_WEB'
    ).order_by('-fecha_ingreso')
    
    context = {
        'propiedades': todas_las_propiedades,
        'is_catalog_page': True 
    }

    return render(request, 'propiedades/catalogo.html', context)

# En views.py

def detalle_propiedad(request, slug):
    propiedad = get_object_or_404(Propiedad, slug=slug)
    
    # Si es petición AJAX (click desde el modal)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'propiedades/detalle_content.html', {'propiedad': propiedad})
    
    # Si es link directo (deep link desde WhatsApp, etc.)
    # Renderizamos el catálogo con instrucción de abrir el modal automáticamente
    todas_las_propiedades = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO'],
        esta_publicada=True
    ).exclude(
        plataformas_publicadas__contains='TERRA_WEB'
    ).order_by('-fecha_ingreso')
    
    context = {
        'propiedades': todas_las_propiedades,
        'modal_open_slug': slug,  # Esta es la señal para JS
        'is_catalog_page': True
    }
    
    return render(request, 'propiedades/catalogo.html', context)

def servicios(request):
    return render(request, 'servicios.html')