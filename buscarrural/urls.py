from django.urls import path

from buscarrural import views

app_name = "buscarrural"

urlpatterns = [
    path("", views.redirect_consultar, name="index"),
    path("consultar/", views.consultar_view, name="consultar"),
    path("consultar/<int:pk>/aguardando/", views.aguardando_view, name="aguardando"),
    path("consultar/<int:pk>/status/", views.status_consulta_view, name="status"),
    path("historico/", views.historico_view, name="historico"),
    path("historico/<int:pk>/", views.detalhe_view, name="detalhe"),
    path("historico/<int:pk>/gerar-parecer/", views.gerar_parecer_view, name="gerar_parecer"),
]
