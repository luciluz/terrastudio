from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
import os
import requests
from decimal import Decimal
import datetime

# --- CONSTANTES Y OPCIONES (CHOICES) ---

TIPO_OPERACION = [
    ('VENTA', 'Venta'),
    ('ARRIENDO', 'Arriendo'),
]

TIPO_MONEDA = [
    ('UF', 'UF'),
    ('CLP', 'Pesos Chilenos (CLP)'),
]

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
    ('PAUSADO', 'Pausado / Suspendido'),
]

# Factibilidades Detalladas
TIPO_AGUA = [
    ('RED_PUBLICA', 'Red Pública (Essbio/Smapa)'),
    ('APR', 'APR (Agua Potable Rural)'),
    ('POZO', 'Pozo Profundo'),
    ('PUNTERA', 'Puntera'),
    ('VERTIENTE', 'Vertiente / Estero'),
    ('CAMION', 'Camión Aljibe'),
    ('NO_TIENE', 'No tiene / Sin factibilidad'),
]

TIPO_LUZ = [
    ('MEDIDOR', 'Medidor Instalado'),
    ('FACTIBILIDAD', 'Factibilidad Técnica'),
    ('POSTACION', 'Postación Cerca'),
    ('SOLAR', 'Proyecto Solar Recomendado'),
    ('NO_TIENE', 'No tiene'),
]

TIPO_ALCANTARILLADO = [
    ('INSTALADO', 'Instalado'),
    ('ACCESO_RED', 'Acceso a Red'),
    ('FOSA', 'Fosa Séptica'),
    ('NO_TIENE', 'No tiene'),
]

TOPOGRAFIA = [
    ('PLANO', 'Plano'),
    ('PENDIENTE_SUAVE', 'Pendiente Suave'),
    ('PENDIENTE_FUERTE', 'Pendiente Fuerte'),
    ('MIXTO', 'Mixto / Variado'),
    ('IRREGULAR', 'Irregular'),
]

# --- MODELOS DE DATOS ---

class Propiedad(models.Model):
    # --- A. IDENTIFICACIÓN ---
    id_ficha = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="ID Individual (Ficha)",
        help_text="Dejar en blanco para generar automático (ej: TS-2026-001). Si escribes uno manual, se respetará."
    )
    rol = models.CharField(
        max_length=50, blank=True, verbose_name="Rol de Avalúo",
        help_text="Ej: 1234-56"
    )
    nro_lote = models.CharField(
        max_length=50, blank=True, verbose_name="Nro. Lote",
        help_text="Ej: Lote A-4"
    )
    propietario = models.CharField(
        max_length=255, blank=True, verbose_name="Nombre Dueño (Privado)",
        help_text="Dato interno. No se muestra en la web."
    )
    fecha_ingreso = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Ingreso",
        help_text="Fecha en que la propiedad ingresa al sistema. Editable."
    )
    estado = models.CharField(max_length=20, choices=ESTADO_PROPIEDAD, default='DISPONIBLE')
    tipo = models.CharField(max_length=20, choices=TIPO_PROPIEDAD, default='PARCELA')
    
    titulo = models.CharField(max_length=200, verbose_name="Título Publicación")
    slug = models.SlugField(
        unique=True, blank=True,
        help_text="URL amigable. Se genera sola desde el título."
    )

    # --- B. UBICACIÓN ---
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    referencia_locacion = models.CharField(max_length=255, blank=True, verbose_name="Referencia Pública")
    comuna = models.CharField(max_length=100, default='Tomé')
    sector = models.CharField(max_length=100, blank=True, verbose_name="Sector", help_text="Ej: Mirador, Rinco 2")
    link_google_earth = models.URLField(blank=True, verbose_name="Link Google Earth/Maps")
    
    # Coordenadas para mapas futuros
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # --- C. ÁMBITO ECONÓMICO ---
    operacion = models.CharField(max_length=20, choices=TIPO_OPERACION, default='VENTA')
    moneda = models.CharField(
        max_length=5, choices=TIPO_MONEDA, default='CLP', 
        verbose_name="Moneda Principal",
        help_text="Define si el precio fijo es en Pesos o UF."
    )
    precio_lista = models.DecimalField(
        max_digits=12, decimal_places=2, 
        verbose_name="Precio de Lista",
        help_text="Ingresa el valor en la moneda seleccionada arriba. Este es el precio real."
    )
    
    # Campos calculados (Solo lectura en Admin)
    precio_uf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor UF (Calc)")
    precio_pesos_referencia = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="Valor Pesos (Calc)")

    # --- D. DIMENSIONES Y TERRENO ---
    superficie_total_m2 = models.PositiveIntegerField(verbose_name="Superficie Total (m²)")
    superficie_construida_m2 = models.PositiveIntegerField(null=True, blank=True, verbose_name="Sup. Construida (m²)")
    
    topografia = models.CharField(max_length=20, choices=TOPOGRAFIA, default='MIXTO')
    topografia_detalle = models.TextField(blank=True, verbose_name="Detalle Topografía")

    # --- E. FACTIBILIDADES ---
    factibilidad_agua = models.CharField(max_length=20, choices=TIPO_AGUA, default='NO_TIENE', verbose_name="Agua")
    factibilidad_luz = models.CharField(max_length=20, choices=TIPO_LUZ, default='NO_TIENE', verbose_name="Luz")
    factibilidad_alcantarillado = models.CharField(max_length=20, choices=TIPO_ALCANTARILLADO, default='NO_TIENE', verbose_name="Alcantarillado")
    factibilidad_detalle = models.TextField(blank=True, verbose_name="Detalle Servicios")

    # --- F. CARACT. HABITACIONALES ---
    dormitorios = models.PositiveSmallIntegerField(null=True, blank=True)
    banos = models.PositiveSmallIntegerField(null=True, blank=True)
    estacionamientos = models.PositiveSmallIntegerField(null=True, blank=True)

    # --- G. GESTIÓN Y MULTIMEDIA ---
    publicada = models.BooleanField(
        default=False, 
        verbose_name="¿Publicada en Web?",
        help_text="Marcar para que aparezca en el sitio."
    )
    link_drive_fotos = models.URLField(blank=True, verbose_name="Link Drive (Privado)")
    links_publicados = models.TextField(blank=True, verbose_name="Links Portales", help_text="Links de Yapo, PortalInmobiliario, etc.")
    observaciones_internas = models.TextField(blank=True, verbose_name="Notas Internas (Privado)")
    descripcion = models.TextField(verbose_name="Descripción Pública")

    # Metadatos automáticos
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"
        ordering = ['-creado']

    def _obtener_valor_uf(self):
        """Consulta API mindicador.cl"""
        try:
            response = requests.get('https://mindicador.cl/api/uf', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return Decimal(str(data['serie'][0]['valor']))
        except:
            pass
        return Decimal('38000') # Respaldo seguro

    def save(self, *args, **kwargs):
        # 1. Generación Automática de ID Ficha
        if not self.id_ficha:
            year = datetime.date.today().year
            # Contamos cuántas propiedades hay creadas este año para sacar el correlativo
            count = Propiedad.objects.filter(creado__year=year).count() + 1
            self.id_ficha = f"TS-{year}-{count:03d}" # Ej: TS-2026-001

        # 2. Generación de Slug
        if not self.slug:
            self.slug = slugify(self.titulo)
            # Evitar duplicados básicos
            orig_slug = self.slug
            counter = 1
            while Propiedad.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{orig_slug}-{counter}"
                counter += 1

        # 3. Cálculo de Precios (La lógica Económica)
        valor_uf_dia = self._obtener_valor_uf()

        if self.moneda == 'UF':
            # La verdad es la UF
            self.precio_uf = self.precio_lista
            self.precio_pesos_referencia = int(self.precio_lista * valor_uf_dia)
        else:
            # La verdad es el Peso (CLP)
            self.precio_pesos_referencia = int(self.precio_lista)
            self.precio_uf = (self.precio_lista / valor_uf_dia).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    @property
    def precio_formateado(self):
        # Muestra el precio según la moneda principal
        if self.moneda == 'CLP' and self.precio_pesos_referencia:
             return f"${self.precio_pesos_referencia:,.0f}".replace(",", ".")
        elif self.precio_uf:
            return f"UF {self.precio_uf:,.2f}".replace(",", ".")
        return "Consulte Precio"
    
    @property
    def imagen_principal(self):
        img = self.imagenes.filter(es_principal=True).first()
        return img if img else self.imagenes.first()

    def __str__(self):
        return f"{self.id_ficha} | {self.titulo}"


class ImagenPropiedad(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='propiedades/%Y/%m/', validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])])
    titulo = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    es_principal = models.BooleanField(default=False)
    orden = models.PositiveSmallIntegerField(default=0)
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imagen de Propiedad"
        verbose_name_plural = "Imágenes de Propiedades"
        ordering = ['-es_principal', 'orden', 'subido_en'] # Orden arreglado
        indexes = [models.Index(fields=['propiedad', 'es_principal']), models.Index(fields=['propiedad', 'orden'])]

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.titulo if self.titulo else f"Imagen de {self.propiedad.titulo}"
        if self.es_principal:
            ImagenPropiedad.objects.filter(propiedad=self.propiedad, es_principal=True).exclude(pk=self.pk).update(es_principal=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Img {self.orden} - {self.propiedad.titulo}"

# Signals
@receiver(post_delete, sender=ImagenPropiedad)
def eliminar_archivo_imagen(sender, instance, **kwargs):
    if instance.imagen and os.path.isfile(instance.imagen.path):
        os.remove(instance.imagen.path)

@receiver(pre_save, sender=ImagenPropiedad)
def eliminar_imagen_anterior(sender, instance, **kwargs):
    if not instance.pk: return
    try:
        old = ImagenPropiedad.objects.get(pk=instance.pk)
        if old.imagen and old.imagen != instance.imagen and os.path.isfile(old.imagen.path):
            os.remove(old.imagen.path)
    except: pass