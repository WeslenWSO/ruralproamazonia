from django.conf import settings
from django.shortcuts import render

from blog.models import Post
from core.clima import obter_data_clima
from core.clima_card import obter_ou_gerar_card_regional
from core.models import HistoriaEmpresa, SlideHero
from servicos.models import Servico


def home(request):
    slides = SlideHero.objects.filter(ativo=True)
    servicos = Servico.objects.filter(ativo=True, destaque=True)[:6]
    if not servicos.exists():
        servicos = Servico.objects.filter(ativo=True)[:6]
    posts = Post.objects.filter(publicado=True, destaque=True)[:3]
    if not posts.exists():
        posts = Post.objects.filter(publicado=True)[:3]
    historia = HistoriaEmpresa.load()
    clima_data = obter_data_clima()
    obter_ou_gerar_card_regional()
    card_url = f"{settings.MEDIA_URL}clima/card_regional_{clima_data['iso']}.jpg"
    return render(
        request,
        "core/home.html",
        {
            "slides": slides,
            "servicos_destaque": servicos,
            "posts_destaque": posts,
            "historia": historia,
            "clima_data": clima_data,
            "clima_card_url": card_url,
        },
    )
