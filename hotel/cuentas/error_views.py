"""Páginas de error genéricas (PS-07 / SEG-07: sin detalles técnicos en pantalla).

Django ya registra el traceback completo en el log del servidor (ver LOGGING en settings.py)
cuando DEBUG=False; aquí solo se controla lo que ve la persona usuaria.
"""
from django.shortcuts import render


def error_404(request, exception=None):
    return render(request, "error.html", {"titulo": "No encontrado", "mensaje": "La página solicitada no existe."}, status=404)


def error_403(request, exception=None):
    return render(request, "error.html", {"titulo": "Acceso denegado", "mensaje": "Su rol no permite acceder a esta función."}, status=403)


def error_400(request, exception=None):
    return render(request, "error.html", {"titulo": "Solicitud rechazada", "mensaje": "La solicitud no pudo procesarse."}, status=400)


def error_500(request):
    return render(request, "error.html", {"titulo": "Error interno", "mensaje": "Ocurrió un error inesperado. Intente nuevamente."}, status=500)
