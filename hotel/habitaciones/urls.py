from django.urls import path

from . import views

app_name = "habitaciones"

urlpatterns = [
    path("encargado", views.encargado_dashboard, name="encargado_dashboard"),
    path("habitaciones", views.habitaciones, name="habitaciones"),
    path("habitaciones/<int:hab_id>/eliminar", views.eliminar, name="eliminar"),
]
