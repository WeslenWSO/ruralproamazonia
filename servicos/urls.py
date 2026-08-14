from django.urls import path

from servicos import views

app_name = "servicos"

urlpatterns = [
    path("", views.lista_servicos, name="lista"),
    path("<slug:slug>/", views.detalhe_servico, name="detalhe"),
]
