"""Vistas - módulo reportes (RF-16, RF-19, RF-20)."""
from datetime import datetime

from django.contrib import messages
from django.shortcuts import render

from hotel.cuentas.models import ROL_ENCARGADO
from hotel.cuentas.seguridad import requiere
from hotel.habitaciones.models import Habitacion
from hotel.pasajeros.models import Asignacion, HistorialOcupacion


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
