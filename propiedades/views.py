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
    return render(request, 'propiedades/inicio.html', context)

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

def detalle_propiedad(request, slug):
    # NOTA: Aquí usamos get_object_or_404 directamente sobre Propiedad.
    # Esto permite que si tú compartes el link directo de una propiedad 'oculta' (pack),
    # el link funcione (porque existe), aunque no aparezca en el catálogo general.
    # Si quisieras que el link dé error 404, tendrías que filtrar aquí también.
    propiedad = get_object_or_404(Propiedad, slug=slug)
    
    # 1. Si es AJAX (Clic desde la misma web): Devuelve solo el HTML del modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'propiedades/detalle_content.html', {'propiedad': propiedad})
    
    # 2. Si es Link Directo (Compartido por WhatsApp):
    # Cargamos el catálogo de fondo, PERO filtrado igual que arriba
    todas_las_propiedades = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO'],
        esta_publicada=True
    ).exclude(
        plataformas_publicadas__contains='TERRA_WEB'
    ).order_by('-fecha_ingreso')
    
    return render(request, 'propiedades/catalogo.html', {
        'propiedades': todas_las_propiedades,
        'propiedad_activa_slug': slug, 
        'is_catalog_page': True
    })

def servicios(request):
    return render(request, 'servicios.html')