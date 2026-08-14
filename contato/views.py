from urllib.parse import quote

from django.contrib import messages
from django.shortcuts import redirect, render

from contato.forms import ContatoForm, WhatsAppInscricaoForm
from contato.models import InscricaoWhatsApp
from core.models import ConfiguracaoSite


def contato(request):
    if request.method == "POST":
        form = ContatoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mensagem enviada com sucesso! Em breve entraremos em contato.")
            return redirect("contato:contato")
    else:
        form = ContatoForm()
    return render(request, "contato/contato.html", {"form": form})


def inscricao_whatsapp(request):
    if request.method != "POST":
        return redirect("core:home")

    form = WhatsAppInscricaoForm(request.POST)
    destino = request.META.get("HTTP_REFERER") or "/"

    if not form.is_valid():
        messages.error(request, form.errors.get("telefone", ["WhatsApp inválido."])[0])
        return redirect(destino)

    telefone = form.cleaned_data["telefone"]
    inscricao, _ = InscricaoWhatsApp.objects.get_or_create(telefone=telefone, defaults={"ativo": True})

    config = ConfiguracaoSite.load()
    numero_empresa = config.whatsapp_numero
    telefone_fmt = inscricao.telefone_formatado

    if numero_empresa:
        texto = (
            "Olá! Quero receber novidades da Rural Pro Amazônia no WhatsApp. "
            f"Meu número: {telefone_fmt}"
        )
        return redirect(f"https://wa.me/{numero_empresa}?text={quote(texto)}")

    messages.success(request, "Inscrição registrada! Entraremos em contato pelo WhatsApp.")
    return redirect(destino)
