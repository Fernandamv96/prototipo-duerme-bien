from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("estado", views.estado, name="estado"),
    path("hospedados", views.hospedados, name="hospedados"),
    path("historial", views.historial, name="historial"),
]
