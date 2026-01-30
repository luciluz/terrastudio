from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import Propiedad

def inicio(request):
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
    qs_base = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO'],
        esta_publicada=True
    ).exclude(
        plataformas_publicadas__contains='TERRA_WEB'
    )

    sectores = qs_base.exclude(sector="").values_list('sector', flat=True).distinct().order_by('sector')

    sector_seleccionado = request.GET.get('sector')
    if sector_seleccionado:
        qs_base = qs_base.filter(sector=sector_seleccionado)

    orden = request.GET.get('orden')
    
    if orden == 'menor_mayor':
        propiedades = qs_base.order_by('precio_uf') 
    elif orden == 'mayor_menor':
        propiedades = qs_base.order_by('-precio_uf')
    else:
        propiedades = qs_base.order_by('-fecha_ingreso')

    context = {
        'propiedades': propiedades,
        'is_catalog_page': True,
        'sectores': sectores,
        'filtro_sector': sector_seleccionado,
        'filtro_orden': orden,
    }

    return render(request, 'propiedades/catalogo.html', context)

def detalle_propiedad(request, slug):
    propiedad = get_object_or_404(Propiedad, slug=slug)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'propiedades/detalle_content.html', {'propiedad': propiedad})
    
    todas_las_propiedades = Propiedad.objects.filter(
        estado__in=['DISPONIBLE', 'RESERVADO'],
        esta_publicada=True
    ).exclude(
        plataformas_publicadas__contains='TERRA_WEB'
    ).order_by('-fecha_ingreso')
    
    context = {
        'propiedades': todas_las_propiedades,
        'modal_open_slug': slug,
        'is_catalog_page': True
    }
    
    return render(request, 'propiedades/catalogo.html', context)

def servicios(request):
    return render(request, 'servicios.html')

def enviar_contacto(request):
    if request.method == 'POST':
        categoria = request.POST.get('categoria', 'General')
        canal = request.POST.get('canal', 'Indefinido')
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        email_cliente = request.POST.get('email', 'No proporcionado')
        mensaje_cliente = request.POST.get('mensaje', '')

        asunto = f"Nuevo contacto desde web TerraStudio: {nombre} - {categoria}"
        
        cuerpo_mensaje = f"""
        Has recibido una nueva solicitud de contacto desde la web TerraStudio.cl

        DATOS DEL CLIENTE
        =================
        Nombre:   {nombre}
        Teléfono: {telefono}
        Email:    {email_cliente}
        
        INTERÉS
        =======
        Área:  {categoria}
        Canal: {canal}
        
        MENSAJE ADICIONAL
        =================
        {mensaje_cliente}
        """

        try:
            send_mail(
                asunto,
                cuerpo_mensaje,
                settings.EMAIL_HOST_USER,
                ['ruzbraulio@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, '¡Solicitud recibida! Te contactaremos a la brevedad.')
        except Exception as e:
            print(f"Error enviando correo: {e}")
            messages.error(request, 'Hubo un error al enviar tu solicitud. Por favor contáctanos por WhatsApp.')

        url_anterior = request.META.get('HTTP_REFERER')
        
        if url_anterior:
            if '#' in url_anterior:
                url_anterior = url_anterior.split('#')[0]
            return redirect(url_anterior + '#contacto-interactivo')
        
        return redirect('inicio') 
    
    return redirect('inicio')