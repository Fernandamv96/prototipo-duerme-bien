"""Vistas - módulo habitaciones (RF-07 a RF-11)."""
import math

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from hotel.cuentas.models import ROL_ENCARGADO
from hotel.cuentas.seguridad import requiere
from hotel.reglas import PRECIO_POR_PASAJERO, ReglaError

from .models import ORIENTACIONES, Habitacion
from .services import cambiar_precio, eliminar_habitacion, registrar_habitacion


# Paletas de las ilustraciones (fotos ficticias hasta tener fotos reales); cada habitación usa una según su número
PALETAS_FOTO = (
    {"muro1": "#17142b", "muro2": "#211d3d", "piso": "#100e20", "cielo1": "#1e1b4b", "cielo2": "#312e81", "mar": "#1e3a8a",
     "edif": "#1f1a3a", "marco": "#4c4677", "madera": "#4c3d8f", "colchon": "#ecebf5", "manta1": "#8b5cf6", "manta2": "#22d3ee"},
    {"muro1": "#1f1426", "muro2": "#2e1d38", "piso": "#140c19", "cielo1": "#0c4a6e", "cielo2": "#38bdf8", "mar": "#0369a1",
     "edif": "#1e293b", "marco": "#5b4470", "madera": "#4a3460", "colchon": "#ede9fe", "manta1": "#7c3aed", "manta2": "#a78bfa"},
    {"muro1": "#2b1610", "muro2": "#3f2218", "piso": "#1d0f0a", "cielo1": "#7c2d12", "cielo2": "#f59e0b", "mar": "#155e75",
     "edif": "#291a14", "marco": "#7a4a35", "madera": "#6b3d26", "colchon": "#fdf4ec", "manta1": "#b45309", "manta2": "#fbbf24"},
    {"muro1": "#10201f", "muro2": "#163331", "piso": "#0a1514", "cielo1": "#134e4a", "cielo2": "#5eead4", "mar": "#0f766e",
     "edif": "#0f2a28", "marco": "#3f6b66", "madera": "#2f5753", "colchon": "#ecfdf5", "manta1": "#0d9488", "manta2": "#5eead4"},
)
MAX_CAMAS_DIBUJO = 4


@requiere(ROL_ENCARGADO)
def foto(request, hab_id):
    """Ilustración SVG de la habitación (foto ficticia): ventana según la orientación y una cama por plaza."""
    hab = get_object_or_404(Habitacion, pk=hab_id)
    n = min(hab.capacidad, MAX_CAMAS_DIBUJO)
    margen, sep, ancho = 64, 10, 400 - 64 - 16
    w = (ancho - sep * (n - 1)) / n
    camas = []
    for i in range(n):
        x = margen + i * (w + sep)
        alm_w = min(w - 16, 70)
        # como texto con punto decimal: la plantilla localizaría los números a "64,5" y el SVG quedaría inválido
        camas.append({k: f"{v:.1f}" for k, v in {
            "x": x, "w": w, "cab_y": 146, "cab_h": 46,
            "alm_x": x + (w - alm_w) / 2, "alm_w": alm_w, "pata_x": x + w - 6,
        }.items()})
    paleta = PALETAS_FOTO[int(hab.numero) % len(PALETAS_FOTO)] if hab.numero.isdigit() else PALETAS_FOTO[0]
    respuesta = render(
        request, "habitaciones/foto.svg",
        {"hab": hab, "camas": camas, "p": paleta, "extra": max(hab.capacidad - MAX_CAMAS_DIBUJO, 0)},
        content_type="image/svg+xml",
    )
    respuesta["Cache-Control"] = "private, max-age=3600"
    return respuesta


DONA_RADIO = 64


def _dona(ocupadas, total):
    """Arcos del gráfico circular (stroke-dasharray de dos círculos). Valores como texto con punto decimal."""
    circ = 2 * math.pi * DONA_RADIO
    if not total:
        return None
    hueco = 3 if 0 < ocupadas < total else 0          # separación de 3px entre ambos arcos
    occ = circ * ocupadas / total
    vac = circ - occ
    return {
        "r": DONA_RADIO, "circ": f"{circ:.2f}",
        "occ": f"{max(occ - hueco, 0):.2f}", "vac": f"{max(vac - hueco, 0):.2f}",
        "occ_off": f"{-hueco / 2:.2f}", "vac_off": f"{-(occ + hueco / 2):.2f}",
    }


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
    hotel = sorted(ocupacion, key=lambda f: not f["huespedes"])   # ocupadas primero, cada grupo por número
    return render(
        request, "habitaciones/encargado_dashboard.html",
        {
            "total": total, "ocupadas": ocupadas, "vacantes": total - ocupadas, "ocupacion": ocupacion,
            "ocupadas_lista": [f["hab"].numero for f in hotel if f["huespedes"]],
            "vacantes_lista": [f["hab"].numero for f in hotel if not f["huespedes"]],
            "pct_habs": round(100 * ocupadas / total) if total else 0,
            "dona": _dona(ocupadas, total),
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
