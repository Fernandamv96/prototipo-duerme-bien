"""Deja el precio (por pasajero y por noche) de las habitaciones activas en la tarifa estándar, PRECIO_POR_PASAJERO.

Sin --aplicar solo muestra la tabla de cambios. Las asignaciones ya registradas conservan su costo.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from hotel.cuentas.models import auditar
from hotel.habitaciones.models import Habitacion
from hotel.reglas import PRECIO_POR_PASAJERO


def precio_sugerido(hab):
    return PRECIO_POR_PASAJERO


class Command(BaseCommand):
    help = "Deja las habitaciones activas en la tarifa estándar de $40.000 (use --aplicar para guardar)."

    def add_arguments(self, parser):
        parser.add_argument("--aplicar", action="store_true", help="Guarda los precios nuevos (si no, solo los muestra).")

    @transaction.atomic
    def handle(self, *args, **options):
        cambios = 0
        self.stdout.write(f"{'Hab.':<6}{'Cap.':<6}{'Vista':<9}{'Actual':>10}{'Nuevo':>10}")
        for hab in Habitacion.objects.filter(activa=True).order_by("numero"):
            nuevo = precio_sugerido(hab)
            self.stdout.write(f"{hab.numero:<6}{hab.capacidad:<6}{hab.orientacion:<9}{hab.precio:>10}{nuevo:>10}")
            if options["aplicar"] and hab.precio != nuevo:
                anterior, hab.precio = hab.precio, nuevo
                hab.save(update_fields=["precio"])
                auditar("sistema", "PRECIO_CAMBIADO", f"Habitación {hab.numero}: ${anterior} → ${nuevo} (tarifa estándar)")
                cambios += 1
        self.stdout.write(f"{cambios} precio(s) actualizados." if options["aplicar"] else "Vista previa: use --aplicar para guardar.")
