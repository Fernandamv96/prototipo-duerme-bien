# Prototipo: Sistema de Gestión de Pasajeros y Habitaciones — Hotel "Duerme Bien"

Prototipo de la Unidad 3 de Ingeniería de Software (INACAP). **Demo:** <https://prototipo-duerme-bien.vercel.app> Stack libre: **Python 3, Django 6,
pytest-django**. Base de datos: SQLite en desarrollo y PostgreSQL en producción.

> Esta es la versión **Django** del prototipo (decisión del equipo tomada en la Unidad 3).
> Existe una versión previa en Flask con el mismo diseño y los mismos 27 casos de prueba
> (`PF-01…PF-16`, `PS-01…PS-09`); esta versión la reemplaza para mantener un único stack
> coherente entre el informe y el código entregado.

## Estructura (módulos del informe, sección 4.1 / 8.1)

```
config/                 proyecto Django: settings.py, urls.py
hotel/
  reglas.py             reglas puras: RUT, parseo de pasajeros, PRECIO_POR_PASAJERO (RN-07)
  cuentas/               módulo 1: autenticación, roles, usuarios, auditoría (RF-01 a RF-06)
    models.py            Usuario (RN-01), Auditoria (RNF-09)
    seguridad.py          sesión propia, expiración por inactividad, decorador @requiere
    services.py            alta de Encargados
    management/commands/  crear_admin, seed_demo
  habitaciones/          módulo 2: alta, consulta y baja lógica (RF-07 a RF-11)
  pasajeros/              módulo 3: pasajeros, asignación, costo, grupos, responsable (RF-12 a RF-18)
  reportes/               módulo 4: estado, hospedados, historial (RF-16, RF-19, RF-20)
  cuentas/static/hotel/   ui.css + ui.js: interfaz con efectos estilo React Bits, sin dependencias
tests/                   pruebas PF-01..PF-16 y PS-01..PS-09 del informe (pytest-django)
api/index.py             punto de entrada WSGI para Vercel
```

CSRF, cabeceras de seguridad (X-Content-Type-Options, X-Frame-Options, CSP, HSTS en producción),
protección contra inyección SQL (ORM) y contra XSS (autoescape de templates) usan los mecanismos
**nativos** de Django — no hay código propio para esto, a diferencia de la versión Flask.

## Instalación y ejecución

```bash
pip install -r requirements-dev.txt   # requirements.txt = solo producción
python manage.py migrate
```

Crear el Administrador inicial (no hay registro público; la contraseña se pide por consola):

```bash
python manage.py crear_admin --usuario admin
```

Datos de demostración (opcional). Las contraseñas se generan al azar y se muestran una vez, o se
toman de las variables `DEMO_ADMIN_PASSWORD` y `DEMO_ENCARGADO_PASSWORD`:

```bash
python manage.py seed_demo
```

Ejecutar el servidor local:

```bash
COOKIE_SECURE=0 DJANGO_DEBUG=1 python manage.py runserver
```

Abrir <http://127.0.0.1:8000>. `COOKIE_SECURE=0` solo es necesario en local (sin HTTPS); en
producción la cookie de sesión exige HTTPS por defecto.

Variables de entorno relevantes (ver `.env.example`):

| Variable | Uso |
|---|---|
| `SECRET_KEY` | Clave de firma de Django. Obligatoria en producción. |
| `DJANGO_DEBUG` | `0` en producción (PS-07: oculta el detalle técnico de los errores). |
| `ALLOWED_HOSTS` | Dominios autorizados, separados por coma. |
| `DATABASE_URL` | Ej.: `postgresql://usuario:clave@host:5432/hotel`. Por defecto SQLite local. |
| `COOKIE_SECURE` | `1` (por defecto) exige HTTPS para la cookie de sesión. |

## Despliegue en Vercel

El proyecto se despliega en Vercel con el runtime de Python (`api/index.py` + `vercel.json`).
Los estáticos los sirve WhiteNoise y la base de datos es PostgreSQL (Neon, desde el Marketplace
de Vercel), que entrega `DATABASE_URL`. Variables necesarias en el proyecto de Vercel:

| Variable | Valor |
|---|---|
| `SECRET_KEY` | clave aleatoria larga |
| `DATABASE_URL` | la crea la integración de Neon |

Con `VERCEL=1` (lo define Vercel) la app asume producción: `DEBUG` apagado, `ALLOWED_HOSTS=.vercel.app`
y confianza en la cabecera `X-Forwarded-Proto` del proxy para HTTPS. Las migraciones y los
usuarios iniciales se ejecutan desde local apuntando a la base de Neon:

```bash
DATABASE_URL=... python manage.py migrate
DATABASE_URL=... python manage.py seed_demo
```

## Pruebas

```bash
python -m pytest -q
python -m pytest -q --cov=hotel --cov-report=term-missing
```

Los nombres de las pruebas coinciden con los identificadores de las tablas de pruebas del informe
(`test_pf01_…` = PF-01, `test_ps06_…` = PS-06, etc.). **Resultado verificado: 30/30 pruebas
pasan** (las 27 del informe más 3 de los accesos directos de la pantalla de ingreso), igual cantidad y mismos IDs que la versión anterior del prototipo (Flask), de modo que
la trazabilidad con el informe no cambia.

## Diferencias deliberadas frente a la versión Flask

- **Hash de contraseñas:** PBKDF2 (hasher por defecto de Django), no bcrypt. Mismo objetivo de
  seguridad (OWASP / RNF-01); cambia la familia de algoritmo, no el nivel de protección.
- **CSRF y cabeceras de seguridad:** se usan los middlewares nativos de Django en vez de
  implementación propia (menos código propio que auditar, más maduro y probado).
- **ORM:** Django ORM en vez de SQLAlchemy; mismas restricciones de integridad (`UNIQUE`,
  `CHECK`) declaradas en los modelos.
- No se usa `django.contrib.admin` ni `django.contrib.auth`: el caso define exactamente dos
  roles con un panel propio, por lo que se evita duplicar conceptos o abrir un acceso adicional
  no contemplado en el caso.

## Limitaciones conocidas

- El bloqueo de cuenta se aplica por usuario: 5 intentos fallidos bloquean la cuenta 15 minutos.
  No hay bloqueo por dirección IP.
- Se agregó "Registrar salida" para liberar habitaciones; el caso no lo describe explícitamente.
- Una habitación no puede tener dos asignaciones activas al mismo tiempo.
- En grupos, cada habitación toma pasajeros en orden según su capacidad (de mayor a menor).
- Las pruebas usan SQLite; no se han ejecutado contra PostgreSQL.
- No se ha ejecutado OWASP ZAP ni pruebas de carga (RNF-02, RNF-06) — pendiente antes de la
  entrega final.
- Desplegado en Vercel (<https://prototipo-duerme-bien.vercel.app>) con PostgreSQL de Neon como
  base temporal; está planificado migrar la persistencia a DynamoDB.
- El respaldo automático (RNF-08) debe configurarse en la plataforma de despliegue.
