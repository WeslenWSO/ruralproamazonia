from django.conf import settings
from django.shortcuts import render

from core.clima import obter_data_clima
from core.clima_card import obter_ou_gerar_card_regional
from core.models import SlideHero
from servicos.models import Servico


def home(request):
    slides = SlideHero.objects.filter(ativo=True)
    servicos = Servico.objects.filter(ativo=True, destaque=True)[:6]
    if not servicos.exists():
        servicos = Servico.objects.filter(ativo=True)[:6]
    clima_data = obter_data_clima()
    card_path = obter_ou_gerar_card_regional()
    card_version = int(card_path.stat().st_mtime) if card_path.exists() else 0
    card_url = (
        f"{settings.MEDIA_URL}clima/card_regional_{clima_data['iso']}.jpg"
        f"?v={card_version}"
    )
    return render(
        request,
        "core/home.html",
        {
            "slides": slides,
            "servicos_destaque": servicos,
            "clima_data": clima_data,
            "clima_card_url": card_url,
        },
    )
