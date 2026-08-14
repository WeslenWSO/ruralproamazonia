from django.urls import path

from blog import views

app_name = "blog"

urlpatterns = [
    path("", views.lista_posts, name="lista"),
    path("<slug:slug>/", views.detalhe_post, name="detalhe"),
]
