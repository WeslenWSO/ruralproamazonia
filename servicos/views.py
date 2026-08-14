from django.shortcuts import get_object_or_404, render

from servicos.models import Servico


def lista_servicos(request):
    servicos = Servico.objects.filter(ativo=True)
    return render(request, "servicos/lista.html", {"servicos": servicos})


def detalhe_servico(request, slug):
    servico = get_object_or_404(Servico, slug=slug, ativo=True)
    relacionados = Servico.objects.filter(ativo=True).exclude(pk=servico.pk)[:3]
    return render(
        request,
        "servicos/detalhe.html",
        {"servico": servico, "relacionados": relacionados},
    )
