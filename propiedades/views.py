from django.shortcuts import render, get_object_or_404
from .models import Propiedad

# --- VISTAS ---

def inicio(request):
    # Filtramos solo lo que se puede vender/mostrar. 
    # Ocultamos PAUSADO y VENDIDO.
    propiedades_destacadas = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO']
    ).order_by('-fecha_ingreso')[:3]
    
    context = {
        'propiedades': propiedades_destacadas
    }
    return render(request, 'propiedades/inicio.html', context)

def nosotros(request):
    # Necesario para el footer o secciones comunes en base.html
    propiedades_destacadas = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO']
    ).order_by('-fecha_ingreso')[:3]
    return render(request, 'nosotros.html', {'propiedades': propiedades_destacadas})

def catalogo(request):
    # Catálogo completo visible
    todas_las_propiedades = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO']
    ).order_by('-fecha_ingreso')
    
    context = {
        'propiedades': todas_las_propiedades,
        'is_catalog_page': True 
    }

    return render(request, 'propiedades/catalogo.html', context)

def detalle_propiedad(request, slug):
    propiedad = get_object_or_404(Propiedad, slug=slug)
    
    # 1. Si es AJAX (Clic desde la misma web): Devuelve solo el HTML del modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'propiedades/detalle_content.html', {'propiedad': propiedad})
    
    # 2. Si es Link Directo (Compartido por WhatsApp):
    # Cargamos el catálogo entero pero le decimos qué modal abrir automáticamente.
    todas_las_propiedades = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO']
    ).order_by('-fecha_ingreso')
    
    return render(request, 'propiedades/catalogo.html', {
        'propiedades': todas_las_propiedades,
        'propiedad_activa_slug': slug, # <--- Esto activa el JS para abrir el modal solo
        'is_catalog_page': True
    })

def servicios(request):
    return render(request, 'servicios.html')