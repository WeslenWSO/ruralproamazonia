from django.urls import path

from contato import views

app_name = "contato"

urlpatterns = [
    path("", views.contato, name="contato"),
    path("newsletter/whatsapp/", views.inscricao_whatsapp, name="inscricao_whatsapp"),
]
