"""Datos de demostración. Las contraseñas se toman de variables de entorno o se generan al azar
y se muestran una única vez (no quedan en el repositorio, PS-07 / SEG-07)."""
import os
import secrets

from django.core.management.base import BaseCommand

from hotel.cuentas.models import ROL_ADMIN, ROL_ENCARGADO, Usuario


class Command(BaseCommand):
    help = "Crea un Administrador y un Encargado de demostración si la base de datos está vacía."

    def handle(self, *args, **options):
        if Usuario.objects.exists():
            self.stdout.write("La base de datos ya tiene usuarios; no se hizo nada.")
            return
        for nombre, user, rol, env in [
            ("Administrador Demo", "admin", ROL_ADMIN, "DEMO_ADMIN_PASSWORD"),
            ("Encargado Demo", "encargado", ROL_ENCARGADO, "DEMO_ENCARGADO_PASSWORD"),
        ]:
            pwd = os.environ.get(env) or secrets.token_urlsafe(10)
            u = Usuario(nombre=nombre, username=user, rol=rol)
            u.set_password(pwd)
            u.save()
            if os.environ.get(env):
                # La contraseña viene de una variable de entorno: no se escribe en los registros (logs).
                self.stdout.write(f"{user}: creado con la contraseña definida en {env}")
            else:
                self.stdout.write(f"{user} / {pwd}")
