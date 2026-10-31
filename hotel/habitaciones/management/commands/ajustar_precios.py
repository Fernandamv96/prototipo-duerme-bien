"""Ajusta el precio (por pasajero y por noche) de las habitaciones activas según la tarifa de referencia.

Sin --aplicar solo muestra la tabla de cambios. Las asignaciones ya registradas conservan su costo.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from hotel.cuentas.models import auditar
from hotel.habitaciones.models import Habitacion

# Tarifa por pasajero y por noche: en habitaciones más grandes cada persona paga menos; la vista al mar cuesta más.
TARIFA = {
    1: {"MAR": 48000, "CIUDAD": 42000},
    2: {"MAR": 42000, "CIUDAD": 36000},
    3: {"MAR": 38000, "CIUDAD": 32000},
    4: {"MAR": 34000, "CIUDAD": 28000},
}


def precio_sugerido(hab):
    return TARIFA[min(max(hab.capacidad, 1), 4)][hab.orientacion]


class Command(BaseCommand):
    help = "Ajusta el precio de las habitaciones activas según la tarifa de referencia (use --aplicar para guardar)."

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
                auditar("sistema", "PRECIO_CAMBIADO", f"Habitación {hab.numero}: ${anterior} → ${nuevo} (tarifa de referencia)")
                cambios += 1
        self.stdout.write(f"{cambios} precio(s) actualizados." if options["aplicar"] else "Vista previa: use --aplicar para guardar.")
