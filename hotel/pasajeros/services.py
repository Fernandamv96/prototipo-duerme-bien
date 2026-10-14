"""Servicios de dominio - módulo pasajeros y asignaciones (RF-12 a RF-18)."""
from django.db import transaction
from django.utils import timezone

from hotel.cuentas.models import auditar
from hotel.habitaciones.models import Habitacion
from hotel.habitaciones.services import habitaciones_libres
from hotel.reglas import PRECIO_POR_PASAJERO, ReglaError, parsear_pasajeros

from .models import Asignacion, HistorialOcupacion, Pasajero


def _pasajero_por_rut(nombre, rut):
    p, _creado = Pasajero.objects.get_or_create(rut=rut, defaults={"nombre": nombre})
    return p


def _crear_asignacion(hab, datos, idx_responsable, ahora, usuario, usuario_label):
    pasajeros = [_pasajero_por_rut(n, r) for n, r in datos]
    costo = len(pasajeros) * PRECIO_POR_PASAJERO                       # RN-07
    asig = Asignacion.objects.create(
        habitacion=hab,
        responsable=pasajeros[idx_responsable - 1],                    # RN-10
        costo_total=costo,
        fecha_hora_inicio=ahora,                                       # RN-08
        estado="ACTIVA",
        registrado_por=usuario,
    )
    asig.pasajeros.set(pasajeros)
    for p in pasajeros:
        HistorialOcupacion.objects.create(
            asignacion_id=asig.id, pasajero=p, numero_habitacion=hab.numero, fecha_asignacion=ahora
        )
    auditar(usuario_label, "ASIGNACION", f"Hab. {hab.numero}: {len(pasajeros)} pasajero(s), costo ${costo}")
    return asig


@transaction.atomic
def crear_asignacion(hab_id, texto_pasajeros, idx_responsable, usuario, usuario_label):
    try:
        hab = Habitacion.objects.get(pk=hab_id, activa=True)
    except Habitacion.DoesNotExist:
        raise ReglaError("La habitación seleccionada no está disponible.")
    if hab.ocupada():
        raise ReglaError(f"La habitación {hab.numero} ya está ocupada.")
    datos = parsear_pasajeros(texto_pasajeros)
    if len(datos) != hab.capacidad:                                    # RN-06 / RF-14
        raise ReglaError(
            f"Debe asignar exactamente {hab.capacidad} pasajero(s) a la "
            f"habitación {hab.numero}; ingresó {len(datos)}."
        )
    if not (1 <= idx_responsable <= len(datos)):                       # RN-10
        raise ReglaError("Debe seleccionar un pasajero responsable válido.")
    return _crear_asignacion(hab, datos, idx_responsable, timezone.now(), usuario, usuario_label)


@transaction.atomic
def crear_asignacion_multiple(hab_ids, texto_pasajeros, responsables, usuario, usuario_label):
    """RF-17 / RN-09: grupo que supera la capacidad de la habitación más grande disponible."""
    datos = parsear_pasajeros(texto_pasajeros)
    n = len(datos)
    libres = {h.id: h for h in habitaciones_libres()}
    if len(set(hab_ids)) != len(hab_ids) or len(hab_ids) < 2:
        raise ReglaError("Seleccione al menos dos habitaciones distintas.")
    seleccion = []
    for hid in hab_ids:
        if hid not in libres:
            raise ReglaError("Una de las habitaciones seleccionadas no está disponible.")
        seleccion.append(libres[hid])
    max_disp = max((h.capacidad for h in libres.values()), default=0)
    if n <= max_disp:
        raise ReglaError("El grupo cabe en una habitación; use la asignación simple (RN-09).")
    if sum(h.capacidad for h in seleccion) != n:
        raise ReglaError(
            f"La suma de capacidades ({sum(h.capacidad for h in seleccion)}) "
            f"no coincide con el total de pasajeros ({n})."
        )
    seleccion.sort(key=lambda h: (-h.capacidad, h.numero))
    ahora, inicio, asignaciones = timezone.now(), 0, []
    for hab in seleccion:
        chunk = datos[inicio:inicio + hab.capacidad]
        inicio += hab.capacidad
        idx = responsables.get(hab.id, 1)
        if not (1 <= idx <= len(chunk)):
            raise ReglaError(f"Responsable inválido para la habitación {hab.numero}.")
        asignaciones.append(_crear_asignacion(hab, chunk, idx, ahora, usuario, usuario_label))
    return asignaciones


@transaction.atomic
def registrar_salida(asig, usuario_label):
    if asig.estado != "ACTIVA":
        raise ReglaError("La asignación ya fue finalizada.")
    ahora = timezone.now()
    asig.estado = "FINALIZADA"
    asig.fecha_hora_termino = ahora
    asig.save(update_fields=["estado", "fecha_hora_termino"])
    HistorialOcupacion.objects.filter(asignacion_id=asig.id, fecha_termino=None).update(fecha_termino=ahora)
    auditar(usuario_label, "SALIDA", f"Asignación {asig.id} finalizada (hab. {asig.habitacion.numero})")
