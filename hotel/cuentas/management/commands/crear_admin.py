"""Crea el Administrador inicial. No hay registro público (RF-05/RN-02): la única forma de
crear el primer Administrador es este comando de consola, ejecutado por quien despliega el sistema."""
import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from hotel.cuentas.models import ROL_ADMIN, Usuario


class Command(BaseCommand):
    help = "Crea el Administrador inicial del sistema."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", required=True, help="Nombre de usuario del Administrador inicial.")
        parser.add_argument("--nombre", default="Administrador", help="Nombre completo a mostrar.")

    def handle(self, *args, **options):
        username = options["usuario"]
        if Usuario.objects.filter(username=username).exists():
            raise CommandError("El usuario ya existe.")
        pwd = getpass.getpass("Contraseña (mín. 8 caracteres): ")
        if pwd != getpass.getpass("Repita la contraseña: "):
            raise CommandError("Las contraseñas no coinciden.")
        try:
            validate_password(pwd)
        except ValidationError as e:
            raise CommandError(" ".join(e.messages))
        u = Usuario(nombre=options["nombre"], username=username, rol=ROL_ADMIN)
        u.set_password(pwd)
        u.save()
        self.stdout.write(self.style.SUCCESS(f"Administrador '{username}' creado."))
