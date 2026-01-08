from django.shortcuts import render, get_object_or_404
from .models import Propiedad

# --- VISTAS ---

def inicio(request):
    # En el inicio mostramos TODO o una selección, como prefieras.
    # Por ahora dejemos solo las últimas 3 para que no compita con el catálogo completo
    propiedades_destacadas = Propiedad.objects.exclude(estado='VENDIDO').order_by('-creado')[:3]
    
    context = {
        'propiedades': propiedades_destacadas
    }
    return render(request, 'propiedades/inicio.html', context)

def nosotros(request):
    # ¡TRUCO! Para que base.html muestre propiedades, necesitamos enviarlas aquí también
    propiedades_destacadas = Propiedad.objects.exclude(estado='VENDIDO').order_by('-creado')[:3]
    return render(request, 'nosotros.html', {'propiedades': propiedades_destacadas})

def catalogo(request):
    todas_las_propiedades = Propiedad.objects.exclude(estado='VENDIDO').order_by('-creado')
    
    context = {
        'propiedades': todas_las_propiedades,
        'is_catalog_page': True 
    }

    return render(request, 'propiedades/catalogo.html', context)

def detalle_propiedad(request, slug):
    propiedad = get_object_or_404(Propiedad, slug=slug)
    
    # Lógica del Modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'propiedades/detalle_content.html', {'propiedad': propiedad})
    
    # Si entran directo, también necesitamos las destacadas para el footer
    propiedades_destacadas = Propiedad.objects.exclude(estado='VENDIDO').order_by('-creado')[:3]
    
    return render(request, 'propiedades/detalle.html', {
        'propiedad': propiedad,
        'propiedades': propiedades_destacadas # Enviamos esto para que base.html no falle
    })

def servicios(request):
    # Renderiza la plantilla que te di en la respuesta anterior
    return render(request, 'servicios.html')