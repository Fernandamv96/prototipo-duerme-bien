"""Vistas - módulo pasajeros y asignaciones (RF-12 a RF-18)."""
from datetime import timedelta

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from hotel.cuentas.models import ROL_ENCARGADO
from hotel.cuentas.seguridad import requiere
from hotel.habitaciones.services import habitaciones_libres
from hotel.reglas import PRECIO_POR_PASAJERO, ReglaError

from .models import Asignacion
from .services import crear_asignacion, crear_asignacion_multiple, registrar_salida


def _ctx_estadia():
    """Precio y fechas por defecto (hoy → mañana) para los formularios de asignación."""
    hoy = timezone.localdate()
    return {"precio": PRECIO_POR_PASAJERO, "hoy": hoy.isoformat(), "manana": (hoy + timedelta(days=1)).isoformat()}


@requiere(ROL_ENCARGADO)
def asignar(request):
    if request.method == "POST":
        try:
            hab_id = int(request.POST.get("habitacion_id", "0"))
            idx = int(request.POST.get("responsable", "0"))
            crear_asignacion(
                hab_id, request.POST.get("pasajeros"), idx,
                request.POST.get("fecha_inicio"), request.POST.get("fecha_termino"),
                request.hotel_user, request.hotel_user.username,
            )
            messages.success(request, "Asignación registrada.")
            return redirect("reportes:estado")
        except ValueError:
            messages.error(request, "Datos de asignación inválidos.")
        except ReglaError as e:
            messages.error(request, str(e))
        return redirect("pasajeros:asignar")
    return render(request, "pasajeros/asignar.html", {"libres": habitaciones_libres(), **_ctx_estadia()})


@requiere(ROL_ENCARGADO)
def asignar_multiple(request):
    libres = habitaciones_libres()
    if request.method == "POST":
        try:
            ids = [int(x) for x in request.POST.getlist("habitacion_ids")]
            responsables = {
                h.id: int(request.POST.get(f"responsable_{h.id}", "1") or 1) for h in libres if h.id in ids
            }
            asigs = crear_asignacion_multiple(
                ids, request.POST.get("pasajeros"), responsables,
                request.POST.get("fecha_inicio"), request.POST.get("fecha_termino"),
                request.hotel_user, request.hotel_user.username,
            )
            messages.success(request, f"Grupo distribuido en {len(asigs)} habitaciones.")
            return redirect("reportes:estado")
        except ValueError:
            messages.error(request, "Datos inválidos.")
        except ReglaError as e:
            messages.error(request, str(e))
        return redirect("pasajeros:asignar_multiple")
    max_disp = max((h.capacidad for h in libres), default=0)
    return render(
        request, "pasajeros/asignar_multiple.html",
        {"libres": libres, "max_disp": max_disp, **_ctx_estadia()},
    )


@requiere(ROL_ENCARGADO)
def salida(request, asig_id):
    if request.method != "POST":
        return redirect("reportes:hospedados")
    try:
        asig = Asignacion.objects.get(pk=asig_id)
    except Asignacion.DoesNotExist:
        raise Http404
    try:
        registrar_salida(asig, request.hotel_user.username)
        messages.success(request, "Salida registrada; la habitación queda vacante.")
    except ReglaError as e:
        messages.error(request, str(e))
    return redirect("reportes:hospedados")
