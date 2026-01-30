from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Propiedad # Asegúrate de importar tus modelos

class PropiedadSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'

    def items(self):
        # Retorna solo las propiedades activas/publicadas
        return Propiedad.objects.all() 

    def lastmod(self, obj):
        # Ajusta esto al campo de fecha de tu modelo (ej: fecha_publicacion, created_at, etc)
        # Si no tienes fecha, puedes borrar este método 'lastmod' entero.
        return obj.fecha_publicacion 

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"
    protocol = 'https'

    def items(self):
        # Aquí pon los 'name' de tus urls estáticas (revisa tu urls.py)
        return ['inicio', 'nosotros', 'contacto', 'servicios']

    def location(self, item):
        return reverse(item)