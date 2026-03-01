from django.core.management.base import BaseCommand
from propiedades.models import Propiedad
import requests
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Actualiza conversiones UF/CLP manteniendo el precio_lista original estático'

    def handle(self, *args, **kwargs):
        self.stdout.write("Consultando valor UF actual...")
        
        try:
            response = requests.get('https://mindicador.cl/api/uf', timeout=10)
            if response.status_code == 200:
                data = response.json()
                valor_uf_hoy = Decimal(str(data['serie'][0]['valor']))
                self.stdout.write(self.style.SUCCESS(f"Valor UF: ${valor_uf_hoy:,.2f}"))
            else:
                self.stdout.write(self.style.ERROR("Error HTTP en la API."))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error de conexión: {e}"))
            return

        propiedades = Propiedad.objects.all()
        contador = 0

        for prop in propiedades:
            if prop.moneda == 'CLP':
                # Mantiene el valor en pesos estático, recalcula la UF
                nuevo_pesos = int(prop.precio_lista)
                nueva_uf = (prop.precio_lista / valor_uf_hoy).quantize(Decimal('0.01'))
            elif prop.moneda == 'UF':
                # Mantiene el valor en UF estático, recalcula los pesos
                nueva_uf = prop.precio_lista
                nuevo_pesos = int(prop.precio_lista * valor_uf_hoy)
            else:
                continue

            Propiedad.objects.filter(pk=prop.pk).update(
                precio_pesos_referencia=nuevo_pesos,
                precio_uf=nueva_uf,
                actualizado=timezone.now()
            )
            contador += 1

        self.stdout.write(self.style.SUCCESS(f"Operación completada. {contador} propiedades recalculadas desde su precio_lista original."))