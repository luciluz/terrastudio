from django.contrib import admin
from .models import Propiedad, ImagenPropiedad
from django.utils.html import format_html

class ImagenPropiedadInline(admin.TabularInline):
    model = ImagenPropiedad
    extra = 1
    fields = ('imagen', 'titulo', 'es_principal', 'orden', 'preview')
    readonly_fields = ('preview',)
    def preview(self, obj):
        return format_html('<img src="{}" style="height:80px; border-radius:4px;" />', obj.imagen.url) if obj.imagen else "-"

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    # Inyectamos el JS para cálculo en vivo
    class Media:
        js = (
            'propiedades/js/admin_calculo.js',
            'propiedades/js/admin_links.js',
        )

    list_display = ('id_ficha', 'titulo', 'estado', 'precio_visual', 'esta_publicada', 'fecha_ingreso')
    list_filter = ('esta_publicada', 'estado', 'operacion', 'comuna', 'plataformas_publicadas')
    search_fields = ('titulo', 'id_ficha', 'rol')
    list_editable = ('estado', 'esta_publicada')
    ordering = ('-fecha_ingreso',)
    list_per_page = 30
    inlines = [ImagenPropiedadInline]
    
    # Readonly para los cálculos del servidor
    readonly_fields = ('precio_uf', 'precio_pesos_referencia', 'slug', 'creado', 'actualizado')

    fieldsets = (
        ('1. Identificación', {
            'fields': (
                ('id_ficha', 'fecha_ingreso'),
                ('titulo', 'slug'),
                ('tipo', 'estado'),
                ('rol', 'nro_lote'),
                'propietario'
            )
        }),
        ('2. Ubicación', {
            'fields': (
                ('direccion', 'comuna'),
                ('sector', 'referencia_locacion'),
                'coordenadas_gps', # Texto libre
                'link_google_earth'
            )
        }),
        ('3. Económico (Cálculo Automático)', {
            'fields': (
                'operacion',
                ('moneda', 'precio_lista'),
                ('precio_uf', 'precio_pesos_referencia'), # Aquí actúa el JS y el Readonly
            )
        }),
        ('4. Técnico y Servicios', {
            'fields': (
                ('superficie_total_m2', 'superficie_construida_m2'),
                'topografia', 'topografia_detalle',
                ('factibilidad_agua', 'factibilidad_luz', 'factibilidad_alcantarillado'),
                'factibilidad_detalle'
            )
        }),
        ('5. Gestión de Publicación', {
            'fields': (
                'esta_publicada',         
                'plataformas_publicadas', 
                
                # --- NUEVO: Los campos de Links (El JS los ocultará si no están marcados) ---
                'url_facebook', 'url_meta_ads', 'url_instagram', 
                'url_portalinmobiliario', 'url_yapo', 'url_toctoc', 'url_otra',
                
                'descripcion',
                'observaciones_internas',
                'link_drive_fotos',
            )
        }),
    )

    @admin.display(description="Precio")
    def precio_visual(self, obj):
        return obj.precio_formateado
    
@admin.register(ImagenPropiedad)
class ImagenPropiedadAdmin(admin.ModelAdmin):
    # Columnas que se ven en la lista
    list_display = ('preview_miniatura', 'propiedad', 'es_principal', 'orden', 'subido_en')
    
    # Filtros laterales
    list_filter = ('es_principal', 'propiedad__tipo', 'subido_en')
    
    # Buscador
    search_fields = ('propiedad__titulo', 'propiedad__id_ficha', 'titulo')
    
    # Cosas que puedes editar rápido sin entrar a la ficha
    list_editable = ('orden', 'es_principal')
    
    # Orden por defecto
    ordering = ('propiedad', 'orden')
    
    @admin.display(description="Foto")
    def preview_miniatura(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.imagen.url)
        return "-"