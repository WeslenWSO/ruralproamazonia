from django.urls import path

from clientes import views

app_name = "clientes"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("cadastro/", views.cadastro_view, name="cadastro"),
    path("painel/", views.painel_view, name="painel"),
    path("sair/", views.logout_view, name="logout"),
]
