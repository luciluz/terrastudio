from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
import os
import requests
from decimal import Decimal

# --- CONSTANTES Y OPCIONES DE SELECCIÓN (CHOICES) ---
# Definición de listas de opciones como constantes para mantener la integridad 
# de los datos y facilitar cambios futuros en las reglas de negocio.

TIPO_PROPIEDAD = [
    ('PARCELA', 'Parcela de Agrado'),
    ('URBANO', 'Sitio Urbano'),
    ('CASA', 'Casa'),
    ('AGRICOLA', 'Terreno Agrícola'),
    ('INDUSTRIAL', 'Terreno Industrial'),
]

ESTADO_PROPIEDAD = [
    ('DISPONIBLE', 'Disponible'),
    ('RESERVADO', 'Reservado'),
    ('VENDIDO', 'Vendido'),
]

TIPO_AGUA = [
    ('POTABLE', 'Agua Potable (Red Pública)'),
    ('APR', 'APR (Agua Potable Rural)'),
    ('PUNTERA', 'Puntera / Pozo'),
    ('CAMION', 'Camión Aljibe'),
    ('NO_TIENE', 'Sin factibilidad actual'),
]

TOPOGRAFIA = [
    ('PLANO', '100% Plano'),
    ('LOMA_SUAVE', 'Lomaje Suave'),
    ('PENDIENTE', 'Pendiente Fuerte'),
    ('MIXTO', 'Mixto (Plano y Ladera)'),
]

# --- MODELOS DE DATOS ---

class Propiedad(models.Model):
    """
    Modelo principal que representa un activo inmobiliario (terreno o construcción).
    
    Diseñado para manejar tanto datos comerciales (precios, estado de venta) como 
    especificaciones técnicas, legales y topográficas necesarias para la evaluación 
    de viabilidad de proyectos y tasaciones.
    
    Attributes:
        titulo: Título descriptivo del aviso de la propiedad
        slug: Identificador único para URLs amigables con SEO
        precio_uf: Valor de la propiedad en UF (Unidad de Fomento)
        precio_pesos_referencia: Valor aproximado en pesos chilenos
        estado: Estado actual en el proceso de venta
        tipo: Clasificación del tipo de propiedad
        superficie_total_m2: Área total del terreno en metros cuadrados
        latitud: Coordenada geográfica decimal para geolocalización
        longitud: Coordenada geográfica decimal para geolocalización
    """

    # 1. IDENTIFICACIÓN Y SEO
    titulo = models.CharField(
        max_length=200, 
        verbose_name="Título del aviso"
    )
    slug = models.SlugField(
        unique=True, 
        blank=True,
        help_text="Identificador único para URL amigables. Se genera automáticamente desde el título si se deja en blanco."
    )
    
    # 2. VALORIZACIÓN ECONÓMICA
    # El precio en UF se utiliza como valor base debido a la inflación en Chile.
    # El precio en pesos es referencial y requiere actualización periódica.
    precio_uf = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio en UF",
        help_text="Precio en UF. Si se deja en blanco y se ingresa precio en pesos, se calculará automáticamente."
    )
    precio_pesos_referencia = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Precio en Pesos (Ref)", 
        help_text="Precio en pesos chilenos. Si se deja en blanco y se ingresa precio en UF, se calculará automáticamente."
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_PROPIEDAD, 
        default='DISPONIBLE',
        help_text="Estado actual de la propiedad en el proceso de venta"
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_PROPIEDAD, 
        default='PARCELA',
        help_text="Clasificación del tipo de propiedad"
    )
    
    # 3. CARACTERÍSTICAS DE EDIFICACIÓN
    # Campos opcionales aplicables únicamente a propiedades con construcciones existentes.
    dormitorios = models.PositiveSmallIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Dormitorios",
        help_text="Cantidad de dormitorios (aplicable solo a propiedades construidas)"
    )
    banos = models.PositiveSmallIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Baños",
        help_text="Cantidad de baños completos (aplicable solo a propiedades construidas)"
    )
    estacionamientos = models.PositiveSmallIntegerField(
        null=True, 
        blank=True,
        help_text="Cantidad de estacionamientos disponibles"
    )
    
    # 4. DIMENSIONES Y METRAJE
    superficie_total_m2 = models.PositiveIntegerField(
        verbose_name="Superficie Terreno",
        help_text="Área total del polígono del terreno en metros cuadrados"
    )
    superficie_construida_m2 = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Sup. Construida",
        help_text="Metros cuadrados de construcción edificada (aplicable solo a propiedades con edificación)"
    )

    # 5. ESPECIFICACIONES TÉCNICAS Y LEGALES
    # Información crítica para evaluación de viabilidad de proyectos y tasaciones oficiales.
    rol = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Rol de Avalúo",
        help_text="Identificador fiscal del Servicio de Impuestos Internos (SII). Omitir en casos de cesión de derechos."
    )
    topografia = models.CharField(
        max_length=20, 
        choices=TOPOGRAFIA, 
        default='MIXTO',
        help_text="Característica predominante del relieve del terreno"
    )
    factibilidad_agua = models.CharField(
        max_length=20, 
        choices=TIPO_AGUA, 
        default='NO_TIENE',
        help_text="Tipo de abastecimiento de agua disponible o factible para la propiedad"
    )
    
    # 6. GEOLOCALIZACIÓN
    # Coordenadas en formato decimal para integración con servicios de mapas (Leaflet, Google Maps, OpenStreetMap).
    direccion = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Dirección física o referencia de ubicación"
    )
    comuna = models.CharField(
        max_length=100, 
        default='Tomé',
        help_text="Comuna donde se ubica la propiedad"
    )
    latitud = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Coordenada de latitud en formato decimal. Ejemplo: -36.615517. Rango válido: -90 a 90"
    )
    longitud = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Coordenada de longitud en formato decimal. Ejemplo: -72.952919. Rango válido: -180 a 180"
    )

    # 7. METADATOS DE AUDITORÍA
    # Registro automático de timestamps para trazabilidad de cambios.
    creado = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    actualizado = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"
        ordering = ['-creado']
        indexes = [
            models.Index(fields=['estado', 'tipo']),
            models.Index(fields=['precio_pesos_referencia']),
            models.Index(fields=['comuna']),
        ]

    def clean(self):
        """
        Validación personalizada a nivel de modelo.
        
        Verifica que:
        - Las coordenadas geográficas estén dentro de rangos válidos
        - La superficie construida no exceda la superficie total del terreno
        - Al menos uno de los precios (UF o Pesos) esté definido
        
        Raises:
            ValidationError: Si alguna validación falla
        """
        if self.latitud is not None and not (-90 <= self.latitud <= 90):
            raise ValidationError({
                'latitud': 'La latitud debe estar entre -90 y 90 grados.'
            })
        
        if self.longitud is not None and not (-180 <= self.longitud <= 180):
            raise ValidationError({
                'longitud': 'La longitud debe estar entre -180 y 180 grados.'
            })
        
        if self.superficie_construida_m2 and self.superficie_total_m2:
            if self.superficie_construida_m2 > self.superficie_total_m2:
                raise ValidationError({
                    'superficie_construida_m2': 'La superficie construida no puede ser mayor que la superficie total del terreno.'
                })
        
        if not self.precio_uf and not self.precio_pesos_referencia:
            raise ValidationError(
                'Debe ingresar al menos el precio en UF o el precio en Pesos.'
            )

    def _obtener_valor_uf(self):
        """
        Consulta el valor actual de la UF desde la API de mindicador.cl.
        
        Returns:
            Decimal: Valor de la UF del día actual
            None: Si la consulta falla
        """
        try:
            response = requests.get('https://mindicador.cl/api/uf', timeout=5)
            response.raise_for_status()
            data = response.json()
            valor_uf = Decimal(str(data['serie'][0]['valor']))
            return valor_uf
        except Exception as e:
            # Log del error para debugging en producción
            print(f"Error al obtener valor UF: {e}")
            return None

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para:
        1. Generar automáticamente el slug desde el título
        2. Calcular automáticamente el precio faltante (UF o Pesos) según el ingresado
        
        La conversión se realiza únicamente si falta uno de los dos valores,
        evitando sobrescrituras accidentales en ediciones posteriores.
        """
        # 1. Generación automática de slug
        if not self.slug:
            base_slug = slugify(self.titulo)
            slug = base_slug
            counter = 1
            
            while Propiedad.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # 2. Conversión automática de precios
        # Solo se ejecuta si falta exactamente uno de los dos precios
        if self.precio_uf and not self.precio_pesos_referencia:
            # Caso: Tiene UF, necesita calcular Pesos
            valor_uf = self._obtener_valor_uf()
            if valor_uf:
                self.precio_pesos_referencia = int(self.precio_uf * valor_uf)
            else:
                # Valor de respaldo si falla la API (promedio histórico reciente)
                valor_uf_respaldo = Decimal('38000')
                self.precio_pesos_referencia = int(self.precio_uf * valor_uf_respaldo)
        
        elif self.precio_pesos_referencia and not self.precio_uf:
            # Caso: Tiene Pesos, necesita calcular UF
            valor_uf = self._obtener_valor_uf()
            if valor_uf:
                self.precio_uf = Decimal(str(self.precio_pesos_referencia)) / valor_uf
                self.precio_uf = self.precio_uf.quantize(Decimal('0.01'))
            else:
                # Valor de respaldo si falla la API
                valor_uf_respaldo = Decimal('38000')
                self.precio_uf = Decimal(str(self.precio_pesos_referencia)) / valor_uf_respaldo
                self.precio_uf = self.precio_uf.quantize(Decimal('0.01'))
        
        super().save(*args, **kwargs)

    @property
    def precio_formateado(self):
        """
        Formatea el precio en UF para visualización en frontend.
        
        Returns:
            str: Precio formateado con separadores de miles (ej: "UF 5.000")
                 o "Consulte Precio" si no está definido
        """
        if self.precio_uf:
            return f"UF {self.precio_uf:,.0f}".replace(",", ".")
        return "Consulte Precio"

    @property
    def precio_m2_uf(self):
        """
        Calcula el precio unitario por metro cuadrado en UF.
        
        Métrica útil para comparación entre propiedades de diferentes dimensiones.
        
        Returns:
            float: Precio por m² redondeado a 2 decimales
            None: Si los datos necesarios no están disponibles
        """
        if self.precio_uf and self.superficie_total_m2:
            return round(self.precio_uf / self.superficie_total_m2, 2)
        return None

    @property
    def imagen_principal(self):
        """
        Obtiene la imagen destacada de la propiedad para visualización en listados.
        
        Prioriza la imagen marcada explícitamente como principal. Si no existe,
        retorna la primera imagen disponible ordenada por criterio predeterminado.
        
        Returns:
            ImagenPropiedad: Instancia de la imagen principal o primera disponible
            None: Si no existen imágenes asociadas
        """
        imagen = self.imagenes.filter(es_principal=True).first()
        
        if not imagen:
            imagen = self.imagenes.first()
        
        return imagen

    def __str__(self):
        """Representación en string del modelo para el admin de Django."""
        return f"{self.titulo} | {self.get_estado_display()}"


class ImagenPropiedad(models.Model):
    """
    Modelo para gestión de galería fotográfica asociada a propiedades.
    
    Permite almacenar múltiples imágenes por propiedad con sistema de ordenamiento
    manual y designación de imagen principal para portadas y listados.
    
    Attributes:
        propiedad: Relación ForeignKey con la propiedad asociada
        imagen: Campo ImageField con validación de formatos permitidos
        titulo: Descripción breve de la fotografía
        alt_text: Texto alternativo para accesibilidad y SEO
        es_principal: Flag booleano para identificar imagen destacada
        orden: Valor numérico para ordenamiento manual en galerías
    """
    
    propiedad = models.ForeignKey(
        Propiedad,
        on_delete=models.CASCADE,
        related_name='imagenes',
        verbose_name="Propiedad",
        help_text="Propiedad a la que pertenece esta imagen"
    )
    
    imagen = models.ImageField(
        upload_to='propiedades/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
                message='Solo se permiten archivos en formato JPG, JPEG, PNG y WebP'
            )
        ],
        verbose_name="Imagen"
    )
    
    titulo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Título de la imagen",
        help_text="Descripción breve de la fotografía. Ejemplo: 'Vista frontal', 'Cocina equipada', 'Vista panorámica'"
    )
    
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Texto alternativo (SEO)",
        help_text="Descripción para accesibilidad web y optimización SEO. Se genera automáticamente si se omite."
    )
    
    es_principal = models.BooleanField(
        default=False,
        verbose_name="¿Es imagen principal?",
        help_text="Designa esta imagen como la destacada. Solo puede existir una imagen principal por propiedad. Se utiliza en listados y portadas."
    )
    
    orden = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Orden de visualización",
        help_text="Valor numérico para ordenamiento en galerías. Menor número aparece primero."
    )
    
    subido_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de subida"
    )

    class Meta:
        verbose_name = "Imagen de Propiedad"
        verbose_name_plural = "Imágenes de Propiedades"
        ordering = ['orden', '-subido_en']
        indexes = [
            models.Index(fields=['propiedad', 'es_principal']),
            models.Index(fields=['propiedad', 'orden']),
        ]

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para gestionar automáticamente el alt_text y la unicidad de imagen principal.
        
        Procesos ejecutados:
        1. Generación automática de texto alternativo (alt_text) si no está definido,
           priorizando el título de la imagen o usando el título de la propiedad como fallback.
        2. Implementación de patrón "Highlander" para imagen principal: si esta imagen
           se marca como principal, automáticamente desmarca cualquier otra imagen principal
           existente de la misma propiedad, garantizando unicidad sin lanzar errores de validación.
        """
        # 1. Generación automática de texto alternativo para accesibilidad y SEO
        if not self.alt_text:
            if self.titulo:
                self.alt_text = f"{self.titulo} - {self.propiedad.titulo}"
            else:
                self.alt_text = f"Imagen de {self.propiedad.titulo}"
        
        # 2. Patrón "Highlander": Solo puede haber una imagen principal
        if self.es_principal:
            ImagenPropiedad.objects.filter(
                propiedad=self.propiedad,
                es_principal=True
            ).exclude(pk=self.pk).update(es_principal=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        """Representación en string del modelo para el admin de Django."""
        principal = " [PRINCIPAL]" if self.es_principal else ""
        return f"{self.propiedad.titulo} - Imagen {self.orden}{principal}"


# --- SIGNALS ---
# Gestión automática del ciclo de vida de archivos de imagen en el sistema de archivos.

@receiver(post_delete, sender=ImagenPropiedad)
def eliminar_archivo_imagen(sender, instance, **kwargs):
    """
    Elimina el archivo físico de imagen del sistema de archivos al borrar el registro.
    
    Django elimina únicamente el registro de la base de datos por defecto. Este signal
    garantiza la eliminación del archivo físico para prevenir acumulación de archivos
    huérfanos y optimizar el uso de almacenamiento.
    
    Args:
        sender: Clase del modelo que envió la señal
        instance: Instancia del objeto que fue eliminado
        **kwargs: Argumentos adicionales de la señal
    """
    if instance.imagen and os.path.isfile(instance.imagen.path):
        os.remove(instance.imagen.path)


@receiver(pre_save, sender=ImagenPropiedad)
def eliminar_imagen_anterior(sender, instance, **kwargs):
    """
    Elimina el archivo de imagen previo al actualizar con un nuevo archivo.
    
    Previene la acumulación de archivos obsoletos cuando se reemplaza una imagen
    existente. Solo se ejecuta en operaciones de actualización (UPDATE), no en
    operaciones de creación (INSERT).
    
    Args:
        sender: Clase del modelo que envió la señal
        instance: Instancia del objeto que está siendo guardado
        **kwargs: Argumentos adicionales de la señal
    """
    if not instance.pk:
        return
    
    try:
        imagen_anterior = ImagenPropiedad.objects.get(pk=instance.pk)
    except ImagenPropiedad.DoesNotExist:
        return
    
    if imagen_anterior.imagen and imagen_anterior.imagen != instance.imagen:
        if os.path.isfile(imagen_anterior.imagen.path):
            os.remove(imagen_anterior.imagen.path)