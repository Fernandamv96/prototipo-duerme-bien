"""Servicios de dominio - módulo cuentas (RF-01 a RF-06)."""
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from hotel.reglas import ReglaError

from .models import ROL_ENCARGADO, Usuario, auditar


@transaction.atomic
def crear_usuario(nombre, username, password, usuario_label):
    """RF-06: el Administrador crea Encargados. El rol siempre es ENCARGADO_HOTEL,
    sin importar qué rol venga en el formulario (RF-04 / RN-01)."""
    nombre, username = (nombre or "").strip(), (username or "").strip()
    if not nombre or not username or not password:
        raise ReglaError("Todos los campos son obligatorios.")
    try:
        validate_password(password)        # longitud mínima, contraseñas comunes y solo numéricas
    except ValidationError as e:
        raise ReglaError(" ".join(e.messages))
    if Usuario.objects.filter(username=username).exists():
        raise ReglaError("El nombre de usuario ya existe; elija otro.")
    u = Usuario(nombre=nombre, username=username, rol=ROL_ENCARGADO)
    u.set_password(password)
    u.save()
    auditar(usuario_label, "USUARIO_CREADO", f"Encargado '{username}' creado")
    return u
