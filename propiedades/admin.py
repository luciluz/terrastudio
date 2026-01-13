from django.contrib import admin
from .models import Propiedad, ImagenPropiedad
from django.utils.html import format_html

class ImagenPropiedadInline(admin.TabularInline):
    model = ImagenPropiedad
    extra = 1
    fields = ('imagen', 'titulo', 'es_principal', 'orden', 'preview_imagen')
    readonly_fields = ('preview_imagen',)
    
    def preview_imagen(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-width: 80px; border-radius: 4px;" />', obj.imagen.url)
        return "-"

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ('id_ficha', 'titulo', 'estado', 'operacion', 'precio_visual', 'publicada', 'fecha_ingreso')
    list_filter = ('estado', 'tipo', 'operacion', 'comuna', 'publicada')
    search_fields = ('titulo', 'id_ficha', 'propietario', 'rol')
    list_editable = ('estado', 'publicada')
    ordering = ('-fecha_ingreso',)
    list_per_page = 30
    
    inlines = [ImagenPropiedadInline]
    prepopulated_fields = {'slug': ('titulo',)}

    # Campos que se muestran pero NO se editan (Calculados)
    readonly_fields = ('precio_uf', 'precio_pesos_referencia', 'creado', 'actualizado')

    fieldsets = (
        ('1. Identificación', {
            'fields': (
                ('id_ficha', 'fecha_ingreso'),
                ('titulo', 'slug'),
                ('tipo', 'estado'),
                ('rol', 'nro_lote'),
                'propietario', # Privado
            ),
            'description': 'Datos de identificación interna y legal.'
        }),
        ('2. Ubicación', {
            'fields': (
                ('direccion', 'comuna'),
                ('sector', 'referencia_locacion'),
                'link_google_earth',
                ('latitud', 'longitud'),
            )
        }),
        ('3. Ámbito Económico', {
            'fields': (
                'operacion',
                ('moneda', 'precio_lista'), # Lo que editas
                ('precio_uf', 'precio_pesos_referencia'), # Lo calculado (ReadOnly)
            ),
            'description': 'Define la moneda principal y el precio de lista. Los otros valores se calculan solos al guardar.'
        }),
        ('4. Dimensiones y Terreno', {
            'fields': (
                ('superficie_total_m2', 'superficie_construida_m2'),
                'topografia', 'topografia_detalle'
            )
        }),
        ('5. Factibilidades (Servicios)', {
            'fields': (
                ('factibilidad_agua', 'factibilidad_luz', 'factibilidad_alcantarillado'),
                'factibilidad_detalle'
            )
        }),
        ('6. Habitacional (Opcional)', {
            'fields': ('dormitorios', 'banos', 'estacionamientos'),
            'classes': ('collapse',)
        }),
        ('7. Gestión y Multimedia', {
            'fields': (
                'publicada',
                'descripcion',
                'observaciones_internas',
                'link_drive_fotos',
                'links_publicados'
            )
        }),
    )

    @admin.display(description="Precio")
    def precio_visual(self, obj):
        return obj.precio_formateado

@admin.register(ImagenPropiedad)
class ImagenPropiedadAdmin(admin.ModelAdmin):
    list_display = ('preview_miniatura', 'propiedad', 'es_principal', 'orden')
    list_filter = ('es_principal', 'propiedad__tipo')
    
    @admin.display(description="Foto")
    def preview_miniatura(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.imagen.url)
        return "-"