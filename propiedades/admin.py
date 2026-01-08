from django.contrib import admin
from .models import Propiedad, ImagenPropiedad
from django.utils.html import format_html


class ImagenPropiedadInline(admin.TabularInline):
    """
    Inline para gestión de galería fotográfica directamente desde el formulario de Propiedad.
    
    Permite agregar, editar y ordenar imágenes sin salir de la interfaz de edición
    de la propiedad. Configurado en modo tabular para optimizar espacio visual.
    """
    model = ImagenPropiedad
    extra = 1  # Cantidad de formularios vacíos adicionales mostrados
    fields = ('imagen', 'titulo', 'es_principal', 'orden', 'preview_imagen')
    readonly_fields = ('preview_imagen',)  # Campo de solo lectura para vista previa
    
    def preview_imagen(self, obj):
        """
        Genera una vista previa en miniatura de la imagen cargada.
        
        Args:
            obj: Instancia de ImagenPropiedad
            
        Returns:
            str: HTML con la imagen en miniatura o mensaje si no existe
        """
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 4px;" />',
                obj.imagen.url
            )
        return "Sin imagen"
    
    preview_imagen.short_description = "Vista Previa"


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Propiedad.
    
    Proporciona interfaz completa para gestión de propiedades incluyendo:
    - Listado con filtros y búsqueda
    - Formulario organizado por secciones
    - Gestión inline de galería fotográfica
    - Vista previa de imagen principal
    """
    
    # --- CONFIGURACIÓN DE LISTADO ---
    list_display = (
        'titulo', 
        'tipo', 
        'estado', 
        'precio_formateado', 
        'superficie_total_m2',
        'comuna', 
        'mostrar_imagen_principal',
        'creado'
    )
    
    list_filter = (
        'estado', 
        'tipo', 
        'comuna', 
        'topografia',
        'factibilidad_agua',
        'creado'
    )
    
    search_fields = (
        'titulo', 
        'rol', 
        'direccion',
        'slug'
    )
    
    # Campos editables directamente desde el listado
    list_editable = ('estado',)
    
    # Ordenamiento predeterminado en el listado
    ordering = ('-creado',)
    
    # Cantidad de items por página
    list_per_page = 25
    
    # Acciones personalizadas en el menú desplegable
    actions = ['marcar_como_disponible', 'marcar_como_vendido']
    
    # --- CONFIGURACIÓN DE FORMULARIO ---
    prepopulated_fields = {'slug': ('titulo',)}
    
    inlines = [ImagenPropiedadInline]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'slug', 'estado', 'tipo'),
            'description': 'Datos básicos de identificación y clasificación de la propiedad'
        }),
        ('Valorización', {
            'fields': ('precio_uf', 'precio_pesos_referencia'),
            'description': 'Precio en UF y su equivalente referencial en pesos chilenos'
        }),
        ('Dimensiones y Características', {
            'fields': (
                'superficie_total_m2', 
                'superficie_construida_m2', 
                'dormitorios', 
                'banos', 
                'estacionamientos'
            ),
            'description': 'Metraje y características de edificación (opcional para terrenos sin construcción)'
        }),
        ('Especificaciones Técnicas', {
            'fields': ('rol', 'topografia', 'factibilidad_agua'),
            'description': 'Información legal y características del terreno'
        }),
        ('Geolocalización', {
            'fields': ('direccion', 'comuna', 'latitud', 'longitud'),
            'description': 'Ubicación física y coordenadas GPS para integración con mapas',
            'classes': ('collapse',)  # Sección colapsable para ahorrar espacio
        }),
    )
    
    # Campos de solo lectura (auditoría)
    readonly_fields = ('creado', 'actualizado', 'precio_m2_calculado')
    
    # --- MÉTODOS PERSONALIZADOS PARA LISTADO ---
    
    @admin.display(description="Portada", ordering='imagenes__orden')
    def mostrar_imagen_principal(self, obj):
        """
        Renderiza una miniatura de la imagen principal en el listado.
        
        Args:
            obj: Instancia de Propiedad
            
        Returns:
            str: HTML con imagen en miniatura o guion si no existe
        """
        if obj.imagen_principal:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);" />',
                obj.imagen_principal.imagen.url
            )
        return format_html('<span style="color: #999;">Sin imagen</span>')
    
    @admin.display(description="Precio/m²")
    def precio_m2_calculado(self, obj):
        """
        Muestra el precio por metro cuadrado calculado.
        
        Args:
            obj: Instancia de Propiedad
            
        Returns:
            str: Precio por m² formateado o guion si no está disponible
        """
        precio_m2 = obj.precio_m2_uf
        if precio_m2:
            return f"UF {precio_m2:,.2f}/m²".replace(",", ".")
        return "-"
    
    # --- ACCIONES MASIVAS ---
    
    @admin.action(description="Marcar como Disponible")
    def marcar_como_disponible(self, request, queryset):
        """
        Acción para cambiar el estado de propiedades seleccionadas a Disponible.
        
        Args:
            request: HttpRequest del admin
            queryset: QuerySet de propiedades seleccionadas
        """
        cantidad = queryset.update(estado='DISPONIBLE')
        self.message_user(
            request,
            f"{cantidad} propiedad(es) marcada(s) como Disponible."
        )
    
    @admin.action(description="Marcar como Vendido")
    def marcar_como_vendido(self, request, queryset):
        """
        Acción para cambiar el estado de propiedades seleccionadas a Vendido.
        
        Args:
            request: HttpRequest del admin
            queryset: QuerySet de propiedades seleccionadas
        """
        cantidad = queryset.update(estado='VENDIDO')
        self.message_user(
            request,
            f"{cantidad} propiedad(es) marcada(s) como Vendido."
        )


@admin.register(ImagenPropiedad)
class ImagenPropiedadAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para gestión independiente de imágenes.
    
    Útil para operaciones masivas sobre imágenes o gestión avanzada de la galería
    sin necesidad de acceder a través del modelo Propiedad.
    """
    
    list_display = (
        'preview_miniatura',
        'propiedad', 
        'titulo', 
        'es_principal', 
        'orden', 
        'subido_en'
    )
    
    list_filter = (
        'es_principal', 
        'propiedad__tipo',
        'subido_en'
    )
    
    search_fields = (
        'titulo', 
        'propiedad__titulo',
        'alt_text'
    )
    
    list_editable = ('orden', 'es_principal')
    
    ordering = ('propiedad', 'orden')
    
    readonly_fields = ('preview_completa', 'subido_en')
    
    fields = (
        'propiedad',
        'preview_completa',
        'imagen',
        'titulo',
        'alt_text',
        'es_principal',
        'orden',
        'subido_en'
    )
    
    @admin.display(description="Miniatura")
    def preview_miniatura(self, obj):
        """
        Genera miniatura para el listado de imágenes.
        
        Args:
            obj: Instancia de ImagenPropiedad
            
        Returns:
            str: HTML con imagen miniatura
        """
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.imagen.url
            )
        return "-"
    
    @admin.display(description="Vista Previa Completa")
    def preview_completa(self, obj):
        """
        Genera vista previa de tamaño completo en el formulario de edición.
        
        Args:
            obj: Instancia de ImagenPropiedad
            
        Returns:
            str: HTML con imagen en tamaño medio
        """
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.imagen.url
            )
        return "Aún no se ha cargado ninguna imagen"