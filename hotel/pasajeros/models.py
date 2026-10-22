"""Modelo de datos - módulo pasajeros (RF-12 a RF-18)."""
from django.conf import settings
from django.db import models

from hotel.cuentas.models import Usuario
from hotel.habitaciones.models import Habitacion


class Pasajero(models.Model):
    nombre = models.CharField(max_length=150)
    rut = models.CharField(max_length=12, unique=True)

    class Meta:
        db_table = "pasajero"

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


class Asignacion(models.Model):
    ESTADOS = (("ACTIVA", "Activa"), ("FINALIZADA", "Finalizada"))

    habitacion = models.ForeignKey(Habitacion, on_delete=models.PROTECT, related_name="asignaciones")
    pasajeros = models.ManyToManyField(Pasajero, related_name="asignaciones")
    responsable = models.ForeignKey(                                  # RN-10
        Pasajero, on_delete=models.PROTECT, related_name="asignaciones_responsable"
    )
    costo_total = models.PositiveIntegerField()                       # RN-07
    fecha_inicio = models.DateField(null=True, blank=True)            # estadía: fecha de inicio
    fecha_termino = models.DateField(null=True, blank=True)           # estadía: fecha de término prevista
    fecha_hora_inicio = models.DateTimeField()                        # RN-08 (registro, generada por el servidor)
    fecha_hora_termino = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default="ACTIVA")
    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT)

    class Meta:
        db_table = "asignacion"

    def __str__(self):
        return f"Asignación {self.id} - hab. {self.habitacion.numero}"

    @property
    def noches(self):
        if self.fecha_inicio and self.fecha_termino:
            return (self.fecha_termino - self.fecha_inicio).days
        return None


class HistorialOcupacion(models.Model):
    """RN-05: se conserva aunque la habitación o la asignación original dejen de estar activas."""

    asignacion_id = models.PositiveIntegerField()
    pasajero = models.ForeignKey(Pasajero, on_delete=models.PROTECT)
    numero_habitacion = models.CharField(max_length=10)   # copia: sobrevive a la baja de la habitación
    fecha_asignacion = models.DateTimeField()
    fecha_termino = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "historial_ocupacion"
        ordering = ["-fecha_asignacion"]
