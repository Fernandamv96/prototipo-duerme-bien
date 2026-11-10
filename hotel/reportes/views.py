"""Vistas - módulo reportes (RF-16, RF-19, RF-20)."""
from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, render

from hotel.cuentas.models import ROL_ENCARGADO
from hotel.cuentas.seguridad import requiere
from hotel.habitaciones.models import Habitacion
from hotel.pasajeros.models import Asignacion, HistorialOcupacion
from hotel.reglas import PRECIO_POR_PASAJERO


@requiere(ROL_ENCARGADO)
def estado(request):
    filas = []
    for h in Habitacion.objects.filter(activa=True).order_by("numero"):
        asig = Asignacion.objects.filter(habitacion=h, estado="ACTIVA").select_related("responsable", "representante").first()
        filas.append({"hab": h, "ocupada": asig is not None, "asig": asig})
    return render(request, "reportes/estado.html", {"filas": filas})


@requiere(ROL_ENCARGADO)
def hospedados(request):
    asigs = Asignacion.objects.filter(estado="ACTIVA").order_by("id").prefetch_related("pasajeros")
    return render(request, "reportes/hospedados.html", {"asigs": asigs})


@requiere(ROL_ENCARGADO)
def historial(request):
    qs = HistorialOcupacion.objects.select_related("pasajero")
    desde, hasta = request.GET.get("desde", ""), request.GET.get("hasta", "")
    hab = request.GET.get("habitacion", "").strip()
    try:
        if desde:
            qs = qs.filter(fecha_asignacion__gte=datetime.fromisoformat(desde))
        if hasta:
            qs = qs.filter(fecha_asignacion__lte=datetime.fromisoformat(hasta + "T23:59:59"))
    except ValueError:
        messages.error(request, "Formato de fecha inválido (AAAA-MM-DD).")
    if hab:
        qs = qs.filter(numero_habitacion=hab)
    registros = qs.order_by("-fecha_asignacion")
    return render(
        request, "reportes/historial.html",
        {"registros": registros, "desde": desde, "hasta": hasta, "habitacion": hab},
    )


def _clp(monto):
    """Pesos chilenos con punto de miles: 240000 -> '$240.000'."""
    return "$" + f"{monto:,}".replace(",", ".")


@requiere(ROL_ENCARGADO)
def boleta(request, asig_id):
    """Comprobante de la estadía: personas × noches × tarifa por persona y noche = total."""
    asig = get_object_or_404(
        Asignacion.objects.select_related("habitacion", "responsable", "representante", "registrado_por"), pk=asig_id,
    )
    pasajeros = asig.pasajeros.order_by("nombre")
    n = pasajeros.count()
    noches = asig.noches or 0
    # El costo se calcula como personas × noches × tarifa, así que la tarifa se recupera exacta del total guardado
    tarifa = asig.costo_total // (n * noches) if n and noches else PRECIO_POR_PASAJERO
    return render(request, "reportes/boleta.html", {
        "asig": asig, "pasajeros": pasajeros, "n": n, "noches": noches,
        "tarifa": _clp(tarifa), "total": _clp(asig.costo_total), "numero": f"{asig.id:06d}",
    })
