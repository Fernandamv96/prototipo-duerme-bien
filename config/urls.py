"""URLs raíz del proyecto. No se usa django.contrib.admin (ver settings): el único panel de
administración del sistema es el propio módulo 'cuentas', construido a la medida del caso
(RF-06, roles Administrador / Encargado de Hotel)."""
from django.urls import include, path

urlpatterns = [
    path("", include("hotel.cuentas.urls")),
    path("", include("hotel.habitaciones.urls")),
    path("", include("hotel.pasajeros.urls")),
    path("", include("hotel.reportes.urls")),
]

# Páginas de error sin detalles técnicos (solo entran en juego con DEBUG=False; PS-07 / SEG-07).
handler400 = "hotel.cuentas.error_views.error_400"
handler403 = "hotel.cuentas.error_views.error_403"
handler404 = "hotel.cuentas.error_views.error_404"
handler500 = "hotel.cuentas.error_views.error_500"
