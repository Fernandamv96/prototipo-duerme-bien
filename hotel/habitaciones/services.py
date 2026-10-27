"""Servicios de dominio - módulo habitaciones (RF-07 a RF-11)."""
from hotel.cuentas.models import auditar
from hotel.reglas import ReglaError, parsear_precio

from .models import ORIENTACIONES, Habitacion

ORIENTACIONES_VALIDAS = {clave for clave, _ in ORIENTACIONES}


def habitaciones_libres():
    return [h for h in Habitacion.objects.filter(activa=True).order_by("numero") if not h.ocupada()]


def registrar_habitacion(numero, capacidad, orientacion, precio, usuario_label):
    numero = (numero or "").strip()
    try:
        capacidad = int(capacidad)
    except (TypeError, ValueError):
        raise ReglaError("La capacidad debe ser un número entero.")
    if not numero or capacidad <= 0 or orientacion not in ORIENTACIONES_VALIDAS:
        raise ReglaError("Número, capacidad (>0) y orientación son obligatorios (RF-09).")
    if Habitacion.objects.filter(numero=numero).exists():
        raise ReglaError(f"La habitación {numero} ya existe (RN-03).")
    precio = parsear_precio(precio)
    hab = Habitacion.objects.create(numero=numero, capacidad=capacidad, orientacion=orientacion, precio=precio)
    auditar(usuario_label, "HABITACION_CREADA", f"Habitación {numero}, cap. {capacidad}, {orientacion}, ${precio}")
    return hab


def cambiar_precio(hab, precio, usuario_label):
    """El nuevo precio rige para las próximas asignaciones; las ya registradas mantienen su costo."""
    anterior, hab.precio = hab.precio, parsear_precio(precio)
    hab.save(update_fields=["precio"])
    auditar(usuario_label, "PRECIO_CAMBIADO", f"Habitación {hab.numero}: ${anterior} → ${hab.precio}")


def eliminar_habitacion(hab, usuario_label):
    if hab.ocupada():
        raise ReglaError(f"No se puede eliminar la habitación {hab.numero}: tiene pasajeros activos (RN-04).")
    hab.activa = False                      # baja lógica; el historial se conserva (RN-05)
    hab.save(update_fields=["activa"])
    auditar(usuario_label, "HABITACION_ELIMINADA", f"Habitación {hab.numero} dada de baja (historial conservado)")
