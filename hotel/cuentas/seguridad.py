"""Controles transversales - sesión, control de acceso por rol y bloqueo (OWASP / ISO/IEC 27002).

CSRF, cabeceras de seguridad (X-Content-Type-Options, X-Frame-Options, CSP, HSTS) y protección
contra inyección SQL/XSS se resuelven con los mecanismos nativos de Django (ver config/settings.py
y el uso de autoescape en los templates); aquí solo se implementa lo específico del dominio:
sesión propia sobre el modelo Usuario y expiración por inactividad (SEG-06).
"""
from functools import wraps

from urllib.parse import urlencode

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import Usuario

INACTIVIDAD_MAX_SEGUNDOS = 15 * 60  # se verifica en el servidor (SEG-06)


class SesionUsuarioMiddleware:
    """Carga request.hotel_user desde la sesión y aplica expiración por inactividad."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.hotel_user = None
        uid = request.session.get("uid")
        if uid is not None:
            ultima = request.session.get("ultima")
            ahora = timezone.now().timestamp()
            if ultima is not None and (ahora - ultima) > INACTIVIDAD_MAX_SEGUNDOS:
                request.session.flush()
                return redirect("cuentas:login")
            request.session["ultima"] = ahora
            try:
                u = Usuario.objects.get(pk=uid)
            except Usuario.DoesNotExist:
                u = None
            if u is None or not u.activo:
                request.session.flush()
                return redirect("cuentas:login")
            request.hotel_user = u
        return self.get_response(request)


def iniciar_sesion(request, usuario):
    """Regenera el identificador de sesión al autenticar (mitiga fijación de sesión)."""
    request.session.flush()
    request.session["uid"] = usuario.id
    request.session["rol"] = usuario.rol
    request.session["username"] = usuario.username
    request.session["ultima"] = timezone.now().timestamp()


def cerrar_sesion(request):
    request.session.flush()


def requiere(*roles):
    """Exige sesión y, si se indica, un rol concreto. Cumple RN-02 y la separación de funciones."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if request.hotel_user is None:
                # se recuerda la página pedida para volver a ella después de ingresar
                return redirect(f"{reverse('cuentas:login')}?{urlencode({'next': request.get_full_path()})}")
            if roles and request.hotel_user.rol not in roles:
                return render(
                    request, "error.html",
                    {"titulo": "Acceso denegado", "mensaje": "Su rol no permite acceder a esta función."},
                    status=403,
                )
            return vista(request, *args, **kwargs)
        envoltura.roles_permitidos = roles   # lo usa el login para validar el destino 'next'
        return envoltura
    return decorador
