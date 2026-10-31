"""Servicios de dominio - módulo cuentas (RF-01 a RF-06)."""
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from hotel.reglas import ReglaError, correo_valido

from .models import ROL_ENCARGADO, Usuario, auditar


@transaction.atomic
def crear_usuario(nombre, username, password, usuario_label, correo=""):
    """RF-06: el Administrador crea Encargados. El rol siempre es ENCARGADO_HOTEL,
    sin importar qué rol venga en el formulario (RF-04 / RN-01). El correo es opcional."""
    nombre, username, correo = (nombre or "").strip(), (username or "").strip(), (correo or "").strip().lower()
    if not nombre or not username or not password:
        raise ReglaError("Nombre, usuario y contraseña son obligatorios.")
    if correo and not correo_valido(correo):
        raise ReglaError(f"El correo {correo} no es válido.")
    try:
        validate_password(password)        # longitud mínima, contraseñas comunes y solo numéricas
    except ValidationError as e:
        raise ReglaError(" ".join(e.messages))
    if Usuario.objects.filter(username=username).exists():
        raise ReglaError("El nombre de usuario ya existe; elija otro.")
    u = Usuario(nombre=nombre, username=username, correo=correo, rol=ROL_ENCARGADO)
    u.set_password(password)
    u.save()
    auditar(usuario_label, "USUARIO_CREADO", f"Encargado '{username}' creado")
    return u


@transaction.atomic
def eliminar_usuario(u, usuario_label):
    """El Administrador elimina Encargados. Si ya registró asignaciones se hace baja lógica
    (activo=False) para conservar el historial; si no, se borra la cuenta."""
    if u.rol != ROL_ENCARGADO:
        raise ReglaError("Solo se pueden eliminar cuentas de Encargado de Hotel.")
    if u.asignacion_set.exists():
        u.activo = False
        u.save(update_fields=["activo"])
        auditar(usuario_label, "USUARIO_ELIMINADO", f"Encargado '{u.username}' dado de baja (historial conservado)")
        return False
    u.delete()
    auditar(usuario_label, "USUARIO_ELIMINADO", f"Encargado '{u.username}' eliminado")
    return True
