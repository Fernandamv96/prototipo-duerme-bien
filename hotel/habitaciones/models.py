"""Modelo de datos - módulo habitaciones (RF-07 a RF-11)."""
from django.db import models

from hotel.reglas import PRECIO_POR_PASAJERO

ORIENTACIONES = (
    ("MAR", "Vista al mar"),
    ("CIUDAD", "Vista a la ciudad"),
)


class Habitacion(models.Model):
    numero = models.CharField(max_length=10, unique=True)          # RN-03
    capacidad = models.PositiveIntegerField()
    orientacion = models.CharField(max_length=10, choices=ORIENTACIONES)
    precio = models.PositiveIntegerField(default=PRECIO_POR_PASAJERO)  # por pasajero y por noche (RN-07)
    activa = models.BooleanField(default=True)                     # baja lógica (RN-05)

    class Meta:
        db_table = "habitacion"
        ordering = ["numero"]
        constraints = [
            models.CheckConstraint(condition=models.Q(capacidad__gt=0), name="ck_hab_cap"),
            models.CheckConstraint(condition=models.Q(precio__gt=0), name="ck_hab_precio"),
        ]

    def __str__(self):
        return f"Habitación {self.numero}"

    def ocupada(self):
        return self.asignaciones.filter(estado="ACTIVA").exists()
