"""Vistas - módulo habitaciones (RF-07 a RF-11)."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

from hotel.cuentas.models import ROL_ENCARGADO
from hotel.cuentas.seguridad import requiere
from hotel.reglas import PRECIO_POR_PASAJERO, ReglaError

from .models import ORIENTACIONES, Habitacion
from .services import cambiar_precio, eliminar_habitacion, registrar_habitacion


@requiere(ROL_ENCARGADO)
def encargado_dashboard(request):
    # Ocupación actual por habitación: una casilla por cama, marcada si hay un huésped en ella
    ocupacion = []
    for h in Habitacion.objects.filter(activa=True).order_by("numero"):
        asig = h.asignaciones.filter(estado="ACTIVA").first()
        huespedes = asig.pasajeros.count() if asig else 0
        ocupacion.append({"hab": h, "huespedes": huespedes, "camas": [i < huespedes for i in range(h.capacidad)]})
    total = len(ocupacion)
    ocupadas = sum(1 for f in ocupacion if f["huespedes"])
    camas = sum(f["hab"].capacidad for f in ocupacion)
    camas_ocupadas = sum(f["huespedes"] for f in ocupacion)
    return render(
        request, "habitaciones/encargado_dashboard.html",
        {
            "total": total, "ocupadas": ocupadas, "vacantes": total - ocupadas, "ocupacion": ocupacion,
            # barra general: primero las ocupadas y luego las vacantes, cada grupo por número
            "hotel": sorted(ocupacion, key=lambda f: not f["huespedes"]),
            "pct_habs": round(100 * ocupadas / total) if total else 0,
            "camas": camas, "camas_ocupadas": camas_ocupadas,
            "pct_camas": round(100 * camas_ocupadas / camas) if camas else 0,
        },
    )


@requiere(ROL_ENCARGADO)
def habitaciones(request):
    if request.method == "POST":
        try:
            registrar_habitacion(
                request.POST.get("numero"), request.POST.get("capacidad"),
                request.POST.get("orientacion"), request.POST.get("precio"), request.hotel_user.username,
            )
            messages.success(request, "Habitación registrada.")
        except ReglaError as e:
            messages.error(request, str(e))
        return redirect("habitaciones:habitaciones")
    lista = Habitacion.objects.filter(activa=True).order_by("numero")
    return render(
        request, "habitaciones/habitaciones.html",
        {"habitaciones": lista, "orientaciones": ORIENTACIONES, "precio_defecto": PRECIO_POR_PASAJERO},
    )


@requiere(ROL_ENCARGADO)
def precio(request, hab_id):
    if request.method != "POST":
        return redirect("habitaciones:habitaciones")
    try:
        hab = Habitacion.objects.get(pk=hab_id, activa=True)
    except Habitacion.DoesNotExist:
        raise Http404
    try:
        cambiar_precio(hab, request.POST.get("precio"), request.hotel_user.username)
        messages.success(request, f"Precio de la habitación {hab.numero} actualizado.")
    except ReglaError as e:
        messages.error(request, str(e))
    return redirect("habitaciones:habitaciones")


@requiere(ROL_ENCARGADO)
def eliminar(request, hab_id):
    if request.method != "POST":
        return redirect("habitaciones:habitaciones")
    try:
        hab = Habitacion.objects.get(pk=hab_id, activa=True)
    except Habitacion.DoesNotExist:
        raise Http404
    try:
        eliminar_habitacion(hab, request.hotel_user.username)
        messages.success(request, f"Habitación {hab.numero} dada de baja; su historial se conserva.")
    except ReglaError as e:
        messages.error(request, str(e))
    return redirect("habitaciones:habitaciones")
