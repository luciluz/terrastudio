from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from propiedades.views import inicio, detalle_propiedad, nosotros, catalogo, servicios, enviar_contacto
from django.contrib.sitemaps.views import sitemap
from propiedades.sitemaps import PropiedadSitemap, StaticViewSitemap

from django.http import HttpResponse

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Allow: /",
        "",
        "Sitemap: https://terrastudio.cl/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

sitemaps = {
    'propiedades': PropiedadSitemap,
    'estaticas': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', inicio, name='inicio'),
    path('nosotros/', nosotros, name='nosotros'),
    
    path('propiedad/<slug:slug>/', detalle_propiedad, name='detalle_propiedad'),

    path('enviar-contacto/', enviar_contacto, name='enviar_contacto'),
    
    path('catalogo/', catalogo, name='catalogo'),
    path('servicios/', servicios, name='servicios'),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)