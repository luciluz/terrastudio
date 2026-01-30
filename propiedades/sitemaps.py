from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Propiedad

class PropiedadSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Propiedad.objects.all() 

    def lastmod(self, obj):
        return obj.fecha_ingreso

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"
    protocol = 'https'

    def items(self):
        return ['inicio', 'nosotros', 'catalogo', 'servicios']

    def location(self, item):
        return reverse(item)