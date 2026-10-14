from django.urls import path

from . import views

app_name = "pasajeros"

urlpatterns = [
    path("asignar", views.asignar, name="asignar"),
    path("asignar/multiple", views.asignar_multiple, name="asignar_multiple"),
    path("asignaciones/<int:asig_id>/salida", views.salida, name="salida"),
]
