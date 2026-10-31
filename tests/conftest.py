import re
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from hotel.cuentas.models import ROL_ADMIN, ROL_ENCARGADO, Usuario


def make_rut(cuerpo: str) -> str:
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - suma % 11
    return f"{cuerpo}-{ {11: '0', 10: 'K'}.get(resto, str(resto)) }".replace(" ", "")


R1, R2, R3, R4, R5 = (make_rut(c) for c in ["12345678", "23456789", "34567890", "45678901", "56789012"])


@pytest.fixture
def admin_user(db):
    u = Usuario(nombre="Admin", username="admin", rol=ROL_ADMIN)
    u.set_password("Admin#2026test")
    u.save()
    return u


@pytest.fixture
def encargado_user(db):
    u = Usuario(nombre="Enc", username="encargado", rol=ROL_ENCARGADO)
    u.set_password("Encargado#2026")
    u.save()
    return u


@pytest.fixture
def client():
    # enforce_csrf_checks=True: todas las pruebas pasan por la misma validación de token
    # CSRF que un navegador real (PS-05 / SEG-04).
    return Client(enforce_csrf_checks=True)


def get_csrf(client, url="/login"):
    r = client.get(url)
    token_match = re.search(r'csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)', r.content.decode())
    assert token_match, f"No se encontró csrfmiddlewaretoken en {url}"
    return token_match.group(1)


def login(client, user, pwd):
    token = get_csrf(client)
    return client.post("/login", {"username": user, "password": pwd, "csrfmiddlewaretoken": token})


def login_enc(client):
    r = login(client, "encargado", "Encargado#2026")
    assert r.status_code == 302, r.content


def login_admin(client):
    r = login(client, "admin", "Admin#2026test")
    assert r.status_code == 302, r.content


TELEFONO_PRUEBA = "+56912345678"


def form(client, url, **data):
    # Atajo de las pruebas: pasajeros="Nombre;RUT[;teléfono[;correo]]" (uno por línea) se convierte en las
    # columnas del formulario real (una fila por pasajero) y la cantidad declarada coincide con la lista.
    if "pasajeros" in data:
        filas = [linea.split(";") + ["", "", ""] for linea in data.pop("pasajeros").splitlines() if linea.strip()]
        data["pasajero_nombre"] = [f[0] for f in filas]
        data["pasajero_rut"] = [f[1] for f in filas]
        data["pasajero_telefono"] = [f[2] or TELEFONO_PRUEBA for f in filas]
        data["pasajero_correo"] = [f[3] for f in filas]
        data.setdefault("cantidad", str(len(filas)))
    if url.endswith("/multiple"):
        data.setdefault("representante", "1")
    data["csrfmiddlewaretoken"] = get_csrf(client, url)
    return data


def crear_hab(client, numero, cap, ori="MAR", precio=40000):
    return client.post("/habitaciones", form(
        client, "/habitaciones", numero=numero, capacidad=cap, orientacion=ori, precio=precio,
    ))


def hab_id(numero):
    from hotel.habitaciones.models import Habitacion
    return Habitacion.objects.get(numero=numero).id


def asig_id():
    from hotel.pasajeros.models import Asignacion
    return Asignacion.objects.order_by("-id").first().id


def fechas(noches=1, desde=0):
    """Fechas de estadía válidas: desde hoy (+desde días) por 'noches' noches."""
    ini = timezone.localdate() + timedelta(days=desde)
    return {"fecha_inicio": ini.isoformat(), "fecha_termino": (ini + timedelta(days=noches)).isoformat()}
