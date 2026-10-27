from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("admin-hotel", views.admin_dashboard, name="admin_dashboard"),
    path("admin-hotel/usuarios", views.admin_usuarios, name="admin_usuarios"),
    path("admin-hotel/usuarios/<int:user_id>/eliminar", views.admin_eliminar_usuario, name="admin_eliminar_usuario"),
    path("admin-hotel/auditoria", views.admin_auditoria, name="admin_auditoria"),
]
