from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from propiedades.views import inicio, detalle_propiedad, nosotros, catalogo, servicios

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', inicio, name='inicio'),
    path('nosotros/', nosotros, name='nosotros'),
    
    path('propiedad/<slug:slug>/', detalle_propiedad, name='detalle_propiedad'),
    
    path('catalogo/', catalogo, name='catalogo'),
    path('servicios/', servicios, name='servicios'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)