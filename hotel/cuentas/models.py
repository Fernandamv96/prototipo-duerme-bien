"""Modelo de datos - módulo cuentas (sección 8.3 del informe).

Se usa un modelo de Usuario propio (no el por defecto de Django) para controlar exactamente
los dos roles del caso (RN-01) y el bloqueo por intentos fallidos (PS-06).
"""
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

ROL_ADMIN = "ADMINISTRADOR"
ROL_ENCARGADO = "ENCARGADO_HOTEL"
ROLES = (
    (ROL_ADMIN, "Administrador"),
    (ROL_ENCARGADO, "Encargado de Hotel"),
)

MAX_INTENTOS = 5                 # bloqueo tras intentos fallidos (PS-06)
DURACION_BLOQUEO_MIN = 15


class Usuario(models.Model):
    """RN-01: cada usuario tiene exactamente un rol (CHECK vía choices + constraint)."""

    nombre = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    correo = models.EmailField(max_length=254, blank=True)           # opcional
    password_hash = models.CharField(max_length=128)
    rol = models.CharField(max_length=20, choices=ROLES)
    activo = models.BooleanField(default=True)
    intentos_fallidos = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "usuario"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rol__in=[ROL_ADMIN, ROL_ENCARGADO]),
                name="ck_usuario_rol",
            )
        ]

    def __str__(self):
        return f"{self.username} ({self.rol})"

    # ---- utilidades de autenticación (hash PBKDF2-SHA256 de Django, RNF-01) ----
    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)  # PBKDF2 por defecto en Django

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def esta_bloqueado(self):
        return self.bloqueado_hasta is not None and self.bloqueado_hasta > timezone.now()

    def registrar_fallo_login(self):
        self.intentos_fallidos += 1
        bloqueada = False
        auditar(self.username, "LOGIN_FALLIDO", f"Intento fallido {self.intentos_fallidos} para '{self.username}'")
        if self.intentos_fallidos >= MAX_INTENTOS:
            self.bloqueado_hasta = timezone.now() + timezone.timedelta(minutes=DURACION_BLOQUEO_MIN)
            self.intentos_fallidos = 0
            bloqueada = True
            auditar(self.username, "CUENTA_BLOQUEADA",
                    f"Cuenta '{self.username}' bloqueada {DURACION_BLOQUEO_MIN} min")
        self.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])
        return bloqueada

    def registrar_login_exitoso(self):
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None
        self.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])


class Auditoria(models.Model):
    """RNF-09: registro de operaciones relevantes con usuario y fecha."""

    fecha_hora = models.DateTimeField(default=timezone.now)
    usuario = models.CharField(max_length=50)
    accion = models.CharField(max_length=40)
    detalle = models.CharField(max_length=300)

    class Meta:
        db_table = "auditoria"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.fecha_hora:%d-%m-%Y %H:%M} {self.usuario} {self.accion}"


def auditar(usuario_label, accion, detalle):
    Auditoria.objects.create(usuario=usuario_label or "anónimo", accion=accion, detalle=detalle[:300])
