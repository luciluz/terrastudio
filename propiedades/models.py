from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from multiselectfield import MultiSelectField
import os
import requests
from decimal import Decimal
import datetime
from django.urls import reverse

# --- OPCIONES ---

TIPO_OPERACION = [('VENTA', 'Venta'), ('ARRIENDO', 'Arriendo')]
TIPO_MONEDA = [('UF', 'UF'), ('CLP', 'Pesos Chilenos (CLP)')]
TIPO_PROPIEDAD = [
    ('PARCELA', 'Parcela de Agrado'), ('URBANO', 'Sitio Urbano'),
    ('CASA', 'Casa'), ('AGRICOLA', 'Terreno Agrícola'), ('INDUSTRIAL', 'Terreno Industrial')
]
ESTADO_PROPIEDAD = [
    ('DISPONIBLE', 'Disponible'), ('RESERVADO', 'Reservado'),
    ('VENDIDO', 'Vendido'), ('PAUSADO', 'Pausado / Suspendido')
]

# Plataformas externas (Para el Checkbox Múltiple)
PLATAFORMAS_OPCIONES = [
    ('FB_MARKET', 'Facebook Marketplace'),
    ('FB_PAGE', 'Meta Enterprise'),
    ('INSTAGRAM', 'Instagram'),
    ('PORTAL', 'PortalInmobiliario'),
    ('YAPO', 'Yapo.cl'),
    ('TOCTOC', 'TocToc'),
    ('TERRA_WEB', 'TerraStudio.cl'),
    ('OTRA', 'Otra'),
]

# Factibilidades
TIPO_AGUA = [
    ('RED_PUBLICA', 'Red Pública'), ('APR', 'APR'), ('POZO', 'Pozo Profundo'),
    ('PUNTERA', 'Puntera'), ('VERTIENTE', 'Vertiente/Estero'), ('CAMION', 'Camión Aljibe'), ('NO_TIENE', 'No tiene')
]
TIPO_LUZ = [
    ('MEDIDOR', 'Medidor Instalado'), ('FACTIBILIDAD', 'Factibilidad Técnica'),
    ('POSTACION', 'Postación Cerca'), ('SOLAR', 'Proyecto Solar'), ('NO_TIENE', 'No tiene')
]
TIPO_ALCANTARILLADO = [
    ('INSTALADO', 'Instalado'), ('ACCESO_RED', 'Acceso a Red'),
    ('FOSA', 'Fosa Séptica'), ('NO_TIENE', 'No tiene')
]
TOPOGRAFIA = [
    ('PLANO', 'Plano'), ('PENDIENTE_SUAVE', 'Pendiente Suave'),
    ('PENDIENTE_FUERTE', 'Pendiente Fuerte'), ('MIXTO', 'Mixto'), ('IRREGULAR', 'Irregular')
]

# --- MODELOS ---

class Propiedad(models.Model):
    # A. IDENTIFICACIÓN
    id_ficha = models.CharField(
        max_length=20, unique=True, blank=True,
        verbose_name="ID Ficha",
        help_text="Dejar vacío para automático (TS-0001). Si escribes, se respeta."
    )
    fecha_ingreso = models.DateField(default=timezone.now, verbose_name="Fecha Ingreso")
    titulo = models.CharField(max_length=200, verbose_name="Título Publicación")
    slug = models.SlugField(unique=True, blank=True, max_length=255, help_text="Se genera automático: ID + Título")
    
    estado = models.CharField(max_length=20, choices=ESTADO_PROPIEDAD, default='DISPONIBLE')
    tipo = models.CharField(max_length=20, choices=TIPO_PROPIEDAD, default='PARCELA')
    
    rol = models.CharField(max_length=50, blank=True, verbose_name="Rol Avalúo")
    nro_lote = models.CharField(max_length=50, blank=True, verbose_name="Nro. Lote")
    propietario = models.CharField(max_length=255, blank=True, verbose_name="Dueño (Privado)")

    # B. UBICACIÓN
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    referencia_locacion = models.CharField(max_length=255, blank=True, verbose_name="Referencia")
    comuna = models.CharField(max_length=100, default='Tomé')
    sector = models.CharField(max_length=100, blank=True, verbose_name="Sector")
    
    # Coordenadas Texto (Copia y pega de Google Earth)
    coordenadas_gps = models.CharField(
        max_length=100, blank=True, 
        verbose_name="Coordenadas GPS",
        help_text="Ej: 36°30'33.0\"S 72°50'48.0\"W (Copiar tal cual de Google Earth)"
    )
    link_google_earth = models.URLField(blank=True, verbose_name="Link Mapa")

    # C. ECONÓMICO
    operacion = models.CharField(max_length=20, choices=TIPO_OPERACION, default='VENTA')
    moneda = models.CharField(max_length=5, choices=TIPO_MONEDA, default='CLP', verbose_name="Moneda Principal")
    precio_lista = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio Lista")
    
    # Calculados
    precio_uf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_pesos_referencia = models.PositiveBigIntegerField(null=True, blank=True)

    # D. TÉCNICO
    superficie_total_m2 = models.PositiveIntegerField(verbose_name="Sup. Total m²")
    superficie_construida_m2 = models.PositiveIntegerField(null=True, blank=True, verbose_name="Sup. Construida m²")
    topografia = models.CharField(max_length=20, choices=TOPOGRAFIA, default='MIXTO')
    topografia_detalle = models.TextField(blank=True)
    
    factibilidad_agua = models.CharField(max_length=20, choices=TIPO_AGUA, default='NO_TIENE', verbose_name="Agua")
    factibilidad_luz = models.CharField(max_length=20, choices=TIPO_LUZ, default='NO_TIENE', verbose_name="Luz")
    factibilidad_alcantarillado = models.CharField(max_length=20, choices=TIPO_ALCANTARILLADO, default='NO_TIENE', verbose_name="Alcantarillado")
    factibilidad_detalle = models.TextField(blank=True)

    # E. HABITACIONAL
    dormitorios = models.PositiveSmallIntegerField(null=True, blank=True)
    banos = models.PositiveSmallIntegerField(null=True, blank=True)
    estacionamientos = models.PositiveSmallIntegerField(null=True, blank=True)

    # F. GESTIÓN Y PUBLICACIÓN
    esta_publicada = models.BooleanField(
        default=False, 
        verbose_name="¿Está publicada en algún sitio?",
        help_text="Si no marcas esto, quiere decir que aún no se publica la propiedad en ningún portal."
    )
    
    plataformas_publicadas = MultiSelectField(
        choices=PLATAFORMAS_OPCIONES,
        blank=True,
        verbose_name="Plataformas Activas",
        help_text="Marca las casillas para habilitar los campos de links correspondientes."
    )

    # Campos Específicos para Links (Se mostrarán/ocultarán con JS)
    url_facebook = models.URLField(blank=True, verbose_name="Link Facebook Marketplace")
    url_meta_ads = models.URLField(blank=True, verbose_name="Link Meta Enterprise (Ads)")
    url_instagram = models.URLField(blank=True, verbose_name="Link Instagram")
    url_portalinmobiliario = models.URLField(blank=True, verbose_name="Link PortalInmobiliario")
    url_yapo = models.URLField(blank=True, verbose_name="Link Yapo.cl")
    url_toctoc = models.URLField(blank=True, verbose_name="Link TocToc")
    url_terrastudio = models.URLField(blank=True, null=True, verbose_name="Link Publicación Terrastudio")
    url_otra = models.URLField(blank=True, verbose_name="Link Otra Plataforma")

    descripcion = models.TextField(verbose_name="Descripción Pública")
    observaciones_internas = models.TextField(blank=True, verbose_name="Notas Internas")
    
    # CAMBIO DE NOMBRE AQUÍ PARA EVITAR CONFUSIÓN
    link_drive_fotos = models.URLField(
        blank=True, 
        verbose_name="Link Carpeta Drive (FOTOS ORIGINALES)",
        help_text="Pega aquí el link a la carpeta de Google Drive donde guardas los originales de alta calidad."
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"
        ordering = ['-creado']

    def _obtener_valor_uf(self):
        try:
            response = requests.get('https://mindicador.cl/api/uf', timeout=3)
            if response.status_code == 200:
                return Decimal(str(response.json()['serie'][0]['valor']))
        except: pass
        return Decimal('38000')

    def save(self, *args, **kwargs):
        # --- 1. Lógica existente: ID Automático (TS-0001) ---
        if not self.id_ficha:
            ultimo = Propiedad.objects.all().order_by('id_ficha').last()
            nuevo_num = 1
            if ultimo and ultimo.id_ficha.startswith('TS-'):
                try:
                    partes = ultimo.id_ficha.split('-')
                    if len(partes) == 2:
                        nuevo_num = int(partes[1]) + 1
                except: pass
            self.id_ficha = f"TS-{nuevo_num:04d}"

        super().save(*args, **kwargs)

        # 2. Slug con ID y Título
        if not self.slug:
            # Limpiamos el título para el slug
            titulo_limpio = slugify(self.titulo)[:50] # Máximo 50 chars del titulo
            self.slug = slugify(f"{self.id_ficha}-{titulo_limpio}")

        # 3. Calculo Precios (Respaldo servidor)
        valor_uf = self._obtener_valor_uf()
        if self.moneda == 'UF':
            self.precio_uf = self.precio_lista
            self.precio_pesos_referencia = int(self.precio_lista * valor_uf)
        else:
            self.precio_pesos_referencia = int(self.precio_lista)
            self.precio_uf = (self.precio_lista / valor_uf).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # 'detalle_propiedad' debe coincidir con el name=... que pusiste en urls.py
        return reverse('detalle_propiedad', kwargs={'slug': self.slug})

    @property
    def precio_formateado(self):
        if self.moneda == 'CLP' and self.precio_pesos_referencia:
             return f"${self.precio_pesos_referencia:,.0f}".replace(",", ".")
        elif self.precio_uf:
            return f"UF {self.precio_uf:,.2f}".replace(",", ".")
        return "Consulte"
    
    @property
    def imagen_principal(self):
        img = self.imagenes.filter(es_principal=True).first()
        return img if img else self.imagenes.first()
    
    def __str__(self):
        return f"{self.id_ficha} | {self.titulo}"
    
    @property
    def precio_uf_visual(self):
        if self.precio_uf:
            # 1. Formateamos a 2 decimales con separador de miles gringo (1,234.56)
            valor = f"{self.precio_uf:,.2f}"
            # 2. Invertimos los signos para formato chileno (1.234,56)
            return valor.replace(",", "X").replace(".", ",").replace("X", ".")
        return "0,00"
    
    @property
    def ubicacion_visual(self):
        # Si tiene sector, retorna "Sector, Comuna"
        if self.sector:
            return f"{self.sector}, {self.comuna}"
        # Si no, solo "Comuna"
        return self.comuna


# Modelo Imágenes (Igual que antes, solo asegúrate de tenerlo)
class ImagenPropiedad(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='propiedades/%Y/%m/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])
    titulo = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    es_principal = models.BooleanField(default=False)
    orden = models.PositiveSmallIntegerField(default=0)
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-es_principal', 'orden', 'subido_en']

    def save(self, *args, **kwargs):
        if not self.alt_text: self.alt_text = self.titulo or f"Img {self.propiedad.titulo}"
        if self.es_principal:
            ImagenPropiedad.objects.filter(propiedad=self.propiedad, es_principal=True).exclude(pk=self.pk).update(es_principal=False)
        super().save(*args, **kwargs)

@receiver(post_delete, sender=ImagenPropiedad)
def eliminar_archivo(sender, instance, **kwargs):
    if instance.imagen and os.path.isfile(instance.imagen.path): os.remove(instance.imagen.path)