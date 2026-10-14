"""Vistas - módulo cuentas (RF-01 a RF-06)."""
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.urls import Resolver404, resolve
from django.utils.http import url_has_allowed_host_and_scheme

from hotel.reglas import ReglaError

from .models import ROL_ADMIN, ROL_ENCARGADO, Auditoria, Usuario, auditar
from .seguridad import cerrar_sesion, iniciar_sesion, requiere
from .services import crear_usuario


def index(request):
    if request.hotel_user is None:
        return redirect("cuentas:login")
    if request.hotel_user.rol == ROL_ADMIN:
        return redirect("cuentas:admin_dashboard")
    return redirect("habitaciones:encargado_dashboard")


SECCIONES = {   # accesos directos de la pantalla de ingreso: ruta -> (nombre, rol requerido)
    "/habitaciones": ("Habitaciones", "Encargado"),
    "/asignar/multiple": ("Asignación de grupos", "Encargado"),
    "/historial": ("Historial", "Encargado"),
    "/admin-hotel/auditoria": ("Auditoría", "Administrador"),
}


def _destino_seguro(request, usuario):
    """Devuelve 'next' solo si es una ruta interna a la que el rol del usuario tiene acceso
    (evita redirecciones abiertas y llegar a una página de acceso denegado)."""
    destino = request.POST.get("next", "")
    if not destino or not url_has_allowed_host_and_scheme(destino, {request.get_host()}, request.is_secure()):
        return None
    try:
        vista = resolve(destino.split("?", 1)[0]).func
    except Resolver404:
        return None
    roles = getattr(vista, "roles_permitidos", None)
    if roles is None or (roles and usuario.rol not in roles):
        return None
    return destino


def login(request):
    destino = request.POST.get("next") or request.GET.get("next", "")
    seccion = SECCIONES.get(destino.split("?", 1)[0])
    ctx = {"next": destino, "seccion": seccion[0] if seccion else None, "secciones": SECCIONES}
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            messages.error(request, "Usuario y contraseña son obligatorios.")
            return render(request, "cuentas/login.html", ctx, status=400)

        u = Usuario.objects.filter(username=username).first()
        if u is not None and u.esta_bloqueado():
            auditar(username, "LOGIN_BLOQUEADO", f"Intento con cuenta bloqueada '{username}'")
            messages.error(request, "Cuenta bloqueada temporalmente por intentos fallidos. Intente más tarde.")
            return render(request, "cuentas/login.html", ctx, status=423)

        # Se verifica contraseña incluso si el usuario no existe (hash señuelo), para no revelar
        # por tiempo de respuesta si una cuenta existe o no.
        ok = u.check_password(password) if u is not None else check_password(password, make_password(None))
        if u is None or not ok or not u.activo:
            if u is not None:
                u.registrar_fallo_login()
            else:
                auditar(username, "LOGIN_FALLIDO", f"Intento fallido para usuario inexistente '{username}'")
            messages.error(request, "Credenciales inválidas.")           # mensaje genérico (SEG-01)
            return render(request, "cuentas/login.html", ctx, status=401)

        u.registrar_login_exitoso()
        iniciar_sesion(request, u)                                       # regenera la sesión (fijación)
        auditar(u.username, "LOGIN", "Inicio de sesión")
        ir_a = _destino_seguro(request, u)
        if ir_a is None and seccion:
            messages.info(request, f"{seccion[0]} está disponible solo para el rol {seccion[1]}.")
        return redirect(ir_a or "cuentas:index")
    return render(request, "cuentas/login.html", ctx)


def logout(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.hotel_user:
        auditar(request.hotel_user.username, "LOGOUT", "Cierre de sesión")
    cerrar_sesion(request)
    return redirect("cuentas:login")


@requiere(ROL_ADMIN)
def admin_dashboard(request):
    encargados = Usuario.objects.filter(rol=ROL_ENCARGADO).count()
    return render(request, "cuentas/admin_dashboard.html", {"encargados": encargados})


@requiere(ROL_ADMIN)
def admin_usuarios(request):
    if request.method == "POST":
        try:
            # un campo 'rol' enviado en el formulario se ignora (PF-03 / RN-01)
            crear_usuario(
                request.POST.get("nombre"), request.POST.get("username"),
                request.POST.get("password"), request.hotel_user.username,
            )
            messages.success(request, "Encargado registrado.")
        except ReglaError as e:
            messages.error(request, str(e))
        return redirect("cuentas:admin_usuarios")
    encargados = Usuario.objects.filter(rol=ROL_ENCARGADO).order_by("username")
    return render(request, "cuentas/admin_usuarios.html", {"encargados": encargados})


@requiere(ROL_ADMIN)
def admin_auditoria(request):
    registros = Auditoria.objects.all()[:200]
    return render(request, "cuentas/admin_auditoria.html", {"registros": registros})
