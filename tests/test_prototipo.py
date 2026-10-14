"""Pruebas del prototipo Django. Los identificadores (PF-xx, PS-xx) corresponden a las
tablas de pruebas funcionales y de seguridad del informe (Unidad 3), y son los mismos
nombres de prueba que tenía la versión Flask original, para conservar la trazabilidad."""
from datetime import timedelta

from django.utils import timezone

from hotel.cuentas.models import MAX_INTENTOS, ROL_ADMIN, ROL_ENCARGADO, Auditoria, Usuario
from hotel.habitaciones.models import Habitacion
from hotel.pasajeros.models import Asignacion, HistorialOcupacion

from .conftest import R1, R2, R3, asig_id, crear_hab, form, get_csrf, hab_id, login, login_admin, login_enc


# ------------------------------------------------------------ PF: pruebas funcionales
def test_pf01_login_valido_encargado(client, encargado_user):
    r = login(client, "encargado", "Encargado#2026")
    assert r.status_code == 302
    assert client.get("/").headers["Location"] == "/encargado"


def test_pf02_contrasena_incorrecta_mensaje_generico(client, encargado_user):
    r = login(client, "encargado", "mala-clave")
    assert r.status_code == 401
    html = r.content.decode()
    assert "Credenciales inválidas" in html
    assert "incorrecta" not in html.lower() and "no existe" not in html.lower()  # no indica qué dato falló
    assert client.get("/encargado").status_code == 302


def test_pf03_un_solo_rol_por_usuario(client, admin_user):
    # RF-04 / RN-01: aunque se intente forzar otro rol, el alta siempre fija ENCARGADO_HOTEL.
    login_admin(client)
    client.post("/admin-hotel/usuarios", form(
        client, "/admin-hotel/usuarios", nombre="Doble", username="doble",
        password="Clave#segura1", rol=ROL_ADMIN,
    ))
    assert Usuario.objects.get(username="doble").rol == ROL_ENCARGADO


def test_pf04_admin_registra_encargado(client, admin_user):
    login_admin(client)
    r = client.post("/admin-hotel/usuarios", form(
        client, "/admin-hotel/usuarios", nombre="Nuevo", username="nuevo", password="Clave#segura1",
    ))
    assert r.status_code == 302
    u = Usuario.objects.get(username="nuevo")
    assert u.rol == ROL_ENCARGADO and u.password_hash != "Clave#segura1"


def test_pf05_encargado_no_abre_gestion_de_usuarios(client, encargado_user):
    login_enc(client)
    assert client.get("/admin-hotel/usuarios").status_code == 403


def test_pf06_registrar_habitacion(client, encargado_user):
    login_enc(client)
    assert crear_hab(client, "101", 3, "MAR").status_code == 302
    assert hab_id("101")


def test_pf07_numero_duplicado_rechazado(client, encargado_user):
    login_enc(client)
    crear_hab(client, "101", 3)
    r = client.post("/habitaciones", form(client, "/habitaciones", numero="101", capacidad=2, orientacion="CIUDAD"), follow=True)
    assert "ya existe" in r.content.decode()
    assert Habitacion.objects.filter(numero="101").count() == 1


def test_pf08_no_eliminar_habitacion_ocupada(client, encargado_user):
    login_enc(client)
    crear_hab(client, "102", 1)
    hid = hab_id("102")
    client.post("/asignar", form(client, "/asignar", habitacion_id=hid, pasajeros=f"Ana;{R1}", responsable="1"))
    r = client.post(f"/habitaciones/{hid}/eliminar", form(client, "/habitaciones"), follow=True)
    assert "pasajeros activos" in r.content.decode()
    assert Habitacion.objects.get(numero="102").activa is True


def test_pf09_baja_logica_conserva_historial(client, encargado_user):
    login_enc(client)
    crear_hab(client, "103", 1)
    hid = hab_id("103")
    client.post("/asignar", form(client, "/asignar", habitacion_id=hid, pasajeros=f"Luis;{R2}", responsable="1"))
    client.post(f"/asignaciones/{asig_id()}/salida", form(client, "/hospedados"))
    client.post(f"/habitaciones/{hid}/eliminar", form(client, "/habitaciones"))
    assert Habitacion.objects.get(numero="103").activa is False
    assert HistorialOcupacion.objects.filter(numero_habitacion="103").count() == 1
    html = client.get("/historial?habitacion=103").content.decode()
    assert "Luis" in html


def test_pf10_rut_invalido_rechazado(client, encargado_user):
    from hotel.reglas import normalizar_rut
    login_enc(client)
    crear_hab(client, "104", 1)
    bad = R1[:-1] + ("0" if R1[-1] != "0" else "1")
    r = client.post("/asignar", form(client, "/asignar", habitacion_id=hab_id("104"), pasajeros=f"X;{bad}", responsable="1"), follow=True)
    assert "RUT inválido" in r.content.decode()
    assert normalizar_rut(bad) is None


def test_pf11_capacidad_no_exacta_rechazada(client, encargado_user):
    login_enc(client)
    crear_hab(client, "201", 3)
    r = client.post("/asignar", form(client, "/asignar", habitacion_id=hab_id("201"), pasajeros=f"A;{R1}\nB;{R2}", responsable="1"), follow=True)
    assert "exactamente 3" in r.content.decode()
    assert Asignacion.objects.count() == 0


def test_pf12_tres_pasajeros_en_habitacion_de_tres_cuesta_120000(client, encargado_user):
    login_enc(client)
    crear_hab(client, "202", 3)
    client.post("/asignar", form(client, "/asignar", habitacion_id=hab_id("202"), pasajeros=f"A;{R1}\nB;{R2}\nC;{R3}", responsable="1"))
    assert Asignacion.objects.get().costo_total == 120000


def test_pf13_fecha_hora_generada_por_servidor(client, encargado_user):
    login_enc(client)
    crear_hab(client, "203", 1)
    antes = timezone.now() - timedelta(seconds=5)
    client.post("/asignar", form(
        client, "/asignar", habitacion_id=hab_id("203"), pasajeros=f"A;{R1}", responsable="1",
        fecha_hora_inicio="2001-01-01T00:00",   # el cliente no puede fijar la fecha; se ignora
    ))
    inicio = Asignacion.objects.get().fecha_hora_inicio
    assert inicio >= antes and inicio.year > 2001


def test_pf14_grupo_mayor_que_la_habitacion_mas_grande_se_divide(client, encargado_user):
    login_enc(client)
    crear_hab(client, "301", 2)
    crear_hab(client, "302", 1)
    ids = [str(hab_id("301")), str(hab_id("302"))]
    pax = f"A;{R1}\nB;{R2}\nC;{R3}"
    data = form(client, "/asignar/multiple", pasajeros=pax)
    data["habitacion_ids"] = ids                 # Django envía varios valores para la misma clave
    data[f"responsable_{ids[0]}"] = "1"
    data[f"responsable_{ids[1]}"] = "1"
    r = client.post("/asignar/multiple", data)
    assert r.status_code == 302, r.content
    assert sorted(a.costo_total for a in Asignacion.objects.all()) == [40000, 80000]


def test_pf15_sin_responsable_rechazado(client, encargado_user):
    login_enc(client)
    crear_hab(client, "401", 2)
    r = client.post("/asignar", form(client, "/asignar", habitacion_id=hab_id("401"), pasajeros=f"A;{R1}\nB;{R2}", responsable="0"), follow=True)
    assert "responsable válido" in r.content.decode()
    assert Asignacion.objects.count() == 0


def test_pf16_estado_y_hospedados_tras_asignacion(client, encargado_user):
    login_enc(client)
    crear_hab(client, "501", 1)
    crear_hab(client, "502", 1)
    client.post("/asignar", form(client, "/asignar", habitacion_id=hab_id("501"), pasajeros=f"Marta Soto;{R1}", responsable="1"))
    estado = client.get("/estado").content.decode()
    assert "table-danger" in estado and "table-success" in estado
    hosp = client.get("/hospedados").content.decode()
    assert "Marta Soto" in hosp and R1 in hosp


# ------------------------------------------------------------ PS: pruebas de seguridad
def test_ps01_encargado_por_url_a_pantallas_de_admin(client, encargado_user):
    login_enc(client)
    for ruta in ["/admin-hotel", "/admin-hotel/usuarios", "/admin-hotel/auditoria"]:
        assert client.get(ruta).status_code == 403


def test_ps02_contrasenas_con_hash(client, admin_user, encargado_user):
    for u in Usuario.objects.all():
        assert u.password_hash.startswith("pbkdf2_") and "Admin#2026test" not in u.password_hash


def test_ps03_inyeccion_sql_en_login(client, encargado_user):
    assert login(client, "' OR 1=1 --", "' OR 1=1 --").status_code == 401


def test_ps04_xss_escapado(client, encargado_user):
    login_enc(client)
    crear_hab(client, "601", 1)
    client.post("/asignar", form(client, "/asignar", habitacion_id=hab_id("601"), pasajeros=f"<script>alert(1)</script>;{R1}", responsable="1"))
    html = client.get("/hospedados").content.decode()
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


def test_ps05_csrf_en_formulario_de_registro(client, encargado_user):
    login_enc(client)
    r = client.post("/habitaciones", {"numero": "700", "capacidad": "1", "orientacion": "MAR"})  # sin token
    assert r.status_code == 403  # Django responde 403 Forbidden ante un token CSRF ausente/ inválido


def test_ps06_bloqueo_tras_intentos_fallidos(client, encargado_user):
    for _ in range(MAX_INTENTOS):
        login(client, "encargado", "malo")
    r = login(client, "encargado", "Encargado#2026")       # clave correcta, cuenta ya bloqueada
    assert r.status_code == 423
    assert Auditoria.objects.filter(accion="CUENTA_BLOQUEADA").count() == 1


def test_ps06_sesion_expira_por_inactividad(client, encargado_user):
    login_enc(client)
    session = client.session
    session["ultima"] = (timezone.now() - timedelta(minutes=16)).timestamp()
    session.save()
    r = client.get("/encargado")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_ps07_error_interno_sin_detalles():
    # PS-07 / SEG-07: la página de error 500 que ve la persona usuaria no debe exponer el
    # detalle técnico real (ese detalle queda solo en el log del servidor; ver LOGGING en
    # settings.py). Se invoca directamente el handler, igual que lo haría Django con
    # DEBUG=False ante cualquier excepción no controlada.
    from django.test import RequestFactory
    from hotel.cuentas.error_views import error_500
    r = error_500(RequestFactory().get("/"))
    body = r.content.decode()
    assert r.status_code == 500
    assert "Traceback" not in body and "Ocurrió un error inesperado" in body


def test_ps07_sin_secretos_en_el_repositorio():
    import re
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    patron = re.compile(r"(Admin#2026|Encargado#2026|SECRET_KEY\s*=\s*['\"][^'\"]+['\"])")
    for archivo in raiz.rglob("*"):
        if archivo.is_file() and archivo.suffix in {".py", ".md", ".txt"} and "tests" not in archivo.parts \
                and ".venv" not in archivo.parts and "migrations" not in archivo.parts:
            texto = archivo.read_text(encoding="utf-8")
            # la clave de desarrollo local está marcada explícitamente como insegura/no productiva
            if "django-insecure-solo-para-desarrollo-local" in texto:
                texto = texto.replace("django-insecure-solo-para-desarrollo-local-cambiar-en-produccion", "")
            assert not patron.search(texto), archivo


def test_ps08_auditoria_de_login_asignacion_y_eliminacion(client, encargado_user):
    login_enc(client)
    crear_hab(client, "801", 1)
    hid = hab_id("801")
    client.post("/asignar", form(client, "/asignar", habitacion_id=hid, pasajeros=f"A;{R1}", responsable="1"))
    client.post(f"/asignaciones/{asig_id()}/salida", form(client, "/hospedados"))
    client.post(f"/habitaciones/{hid}/eliminar", form(client, "/habitaciones"))
    acciones = set(Auditoria.objects.values_list("accion", flat=True))
    assert {"LOGIN", "HABITACION_CREADA", "ASIGNACION", "SALIDA", "HABITACION_ELIMINADA"} <= acciones


def test_ps09_cabeceras_de_seguridad(client):
    r = client.get("/login")
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Content-Type-Options"] == "nosniff"


# ------------------------------------------------------------ accesos directos de la pantalla de ingreso
def login_con_next(client, user, pwd, destino):
    token = get_csrf(client, f"/login?next={destino}")
    return client.post("/login", {"username": user, "password": pwd, "next": destino, "csrfmiddlewaretoken": token})


def test_accesos_directos_redirigen_al_login_y_vuelven_a_la_seccion(client, encargado_user):
    r = client.get("/historial")
    assert r.status_code == 302 and r.headers["Location"] == "/login?next=%2Fhistorial"
    assert "continuar a <strong>Historial" in client.get("/login?next=/historial").content.decode()
    r = login_con_next(client, "encargado", "Encargado#2026", "/historial")
    assert r.status_code == 302 and r.headers["Location"] == "/historial"


def test_next_externo_no_genera_redireccion_abierta(client, encargado_user):
    r = login_con_next(client, "encargado", "Encargado#2026", "https://sitio-malicioso.example/")
    assert r.headers["Location"] == "/"


def test_next_de_otro_rol_lleva_al_panel_propio(client, encargado_user):
    r = login_con_next(client, "encargado", "Encargado#2026", "/admin-hotel/auditoria")
    assert r.headers["Location"] == "/"
    assert "solo para el rol Administrador" in client.get("/encargado").content.decode()
