from django.core.management.base import BaseCommand
from propiedades.models import Propiedad
import requests
from decimal import Decimal

class Command(BaseCommand):
    help = 'Actualiza el precio en pesos de todas las propiedades según el valor UF del día'

    def handle(self, *args, **kwargs):
        self.stdout.write("Consultando valor UF actual...")

        # 1. Obtener valor UF del día (API Externa)
        valor_uf_hoy = None
        try:
            response = requests.get('https://mindicador.cl/api/uf', timeout=10)
            if response.status_code == 200:
                data = response.json()
                valor_uf_hoy = Decimal(str(data['serie'][0]['valor']))
                self.stdout.write(self.style.SUCCESS(f"Valor UF obtenido: ${valor_uf_hoy:,.2f}"))
            else:
                self.stdout.write(self.style.ERROR("Error al conectar con la API (Status no 200)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Excepción al conectar con API: {e}"))

        # Si falló la API, preguntamos si queremos usar un valor manual o cancelar
        if not valor_uf_hoy:
            self.stdout.write(self.style.WARNING("No se pudo obtener la UF de la API. No se realizarán cambios para evitar errores."))
            return

        # 2. Recorrer las propiedades y actualizar
        propiedades = Propiedad.objects.filter(precio_uf__isnull=False)
        contador = 0

        self.stdout.write(f"Procesando {propiedades.count()} propiedades...")

        for prop in propiedades:
            # Calculamos el nuevo precio
            nuevo_precio_pesos = int(prop.precio_uf * valor_uf_hoy)
            
            # Verificamos si cambió para no guardar "por las puras"
            if prop.precio_pesos_referencia != nuevo_precio_pesos:
                prop.precio_pesos_referencia = nuevo_precio_pesos
                
                # IMPORTANTE: Usamos update_fields para ser más eficientes y evitar
                # disparar toda la lógica pesada del método save() original innecesariamente
                # o loops infinitos de recálculo.
                prop.save(update_fields=['precio_pesos_referencia', 'actualizado'])
                contador += 1
                self.stdout.write(f" > {prop.titulo}: Actualizado a ${nuevo_precio_pesos:,.0f}")

        self.stdout.write(self.style.SUCCESS(f"¡Listo! Se actualizaron {contador} propiedades al valor UF de hoy."))