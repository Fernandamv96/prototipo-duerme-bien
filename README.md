# Hotel "Duerme Bien" · Gestión de pasajeros y habitaciones

[![Demo](https://img.shields.io/badge/demo-prototipo--duerme--bien.vercel.app-000?logo=vercel)](https://prototipo-duerme-bien.vercel.app)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6-092E20?logo=django&logoColor=white)
![Tests](https://img.shields.io/badge/pytest-35%20pruebas-0A9EDC?logo=pytest&logoColor=white)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

Prototipo de la Unidad 3 de **Ingeniería de Software (INACAP)**: un sistema para que un hotel registre habitaciones, asigne pasajeros, calcule el costo de la estadía y consulte reportes de ocupación.

**[▶ Ver demo](https://prototipo-duerme-bien.vercel.app)**

## Funcionalidades

Hay dos roles, con un panel propio cada uno (RN-01):

| Rol | Puede |
| --- | --- |
| **Administrador** | Gestionar usuarios, revisar la auditoría de acciones y ver el panel general |
| **Encargado de hotel** | Gestionar habitaciones, asignar uno o varios pasajeros, registrar salidas y consultar reportes |

- **Habitaciones:** número único (RN-03), orientación y baja lógica para no perder el historial (RN-05).
- **Asignaciones:** individual o múltiple, una línea por pasajero con el formato `Nombre;RUT`; el RUT se valida con su dígito verificador.
- **Costo de la estadía:** pasajeros × noches × valor fijo por pasajero (RN-07).
- **Reportes:** estado de las habitaciones, pasajeros hospedados e historial de ocupación.

Las reglas de negocio (RN-01 a RN-10) viven en [`hotel/reglas.py`](hotel/reglas.py) como funciones puras, sin depender de Django, para probarlas de forma aislada.

## Seguridad

- **Bloqueo por intentos fallidos:** 5 intentos y la cuenta queda bloqueada 15 minutos (PS-06).
- **Expiración por inactividad:** la sesión vence a los 15 minutos sin uso; se verifica en el servidor (SEG-06).
- **Control de acceso por rol** en cada vista, y auditoría de las acciones del panel.
- **Cabeceras:** CSP nativa de Django 6, `X-Frame-Options: DENY` y HSTS en producción; CSRF y autoescape de plantillas activos.
- **Sin el admin genérico de Django:** el caso define dos roles con panel propio, así que no se expone `/admin`.
- **Secretos por entorno:** `SECRET_KEY`, `DATABASE_URL` y las claves de los usuarios demo se leen de variables de entorno. En producción, sin `SECRET_KEY` la app no arranca.

## Stack

| Capa | Tecnología |
| --- | --- |
| Backend | Python 3.12 + Django 6 (WhiteNoise para estáticos) |
| Base de datos | SQLite en desarrollo y PostgreSQL en producción (`dj-database-url` + psycopg 3) |
| Tests | pytest + pytest-django (52 pruebas) |
| Despliegue | Vercel, runtime de Python ([`api/index.py`](api/index.py)) |

## Ejecutar en local

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows (en macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_demo        # crea los usuarios "admin" y "encargado"
python manage.py runserver        # http://127.0.0.1:8000
```

`seed_demo` usa las claves de `DEMO_ADMIN_PASSWORD` y `DEMO_ENCARGADO_PASSWORD`. Si no las defines, genera claves al azar y las muestra en la consola. Las variables disponibles están en [`.env.example`](.env.example).

```bash
pytest                            # pruebas unitarias y de integración
```

## Licencia

[MIT](LICENSE)
