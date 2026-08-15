from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from buscarrural.forms import ConsultaCARForm
from buscarrural.models import ConsultaHistorico
from buscarrural.services.diagnostico_dados import extrair_indicadores_car
from buscarrural.services.parecer_ia import ParecerIAError
from buscarrural.tasks import iniciar_consulta_async, salvar_parecer_consulta


@login_required
def consultar_view(request):
    form = ConsultaCARForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        numero_car = form.cleaned_data["numero_car"]
        consulta = ConsultaHistorico.objects.create(
            usuario=request.user,
            tipo=ConsultaHistorico.TIPO_SELO_VERDE_ACRE,
            numero_car=numero_car,
            status=ConsultaHistorico.STATUS_PENDENTE,
            mensagem_erro="Iniciando consulta automática…",
        )
        iniciar_consulta_async(consulta)
        return redirect("buscarrural:aguardando", pk=consulta.pk)

    return render(
        request,
        "buscarrural/consultar.html",
        {
            "form": form,
        },
    )


@login_required
def aguardando_view(request, pk):
    consulta = get_object_or_404(ConsultaHistorico, pk=pk, usuario=request.user)
    if consulta.status == ConsultaHistorico.STATUS_SUCESSO:
        messages.success(request, "Consulta Selo Verde Acre concluída.")
        return redirect("buscarrural:detalhe", pk=consulta.pk)
    if consulta.status == ConsultaHistorico.STATUS_ERRO:
        messages.error(request, consulta.mensagem_erro)
        return redirect("buscarrural:consultar")
    return render(request, "buscarrural/aguardando.html", {"consulta": consulta})


@login_required
def status_consulta_view(request, pk):
    consulta = get_object_or_404(ConsultaHistorico, pk=pk, usuario=request.user)
    payload = {
        "status": consulta.status,
        "mensagem": consulta.mensagem_erro,
    }
    if consulta.status == ConsultaHistorico.STATUS_SUCESSO:
        payload["redirect"] = f"/buscarrural/historico/{consulta.pk}/"
    elif consulta.status == ConsultaHistorico.STATUS_ERRO:
        payload["redirect"] = "/buscarrural/consultar/"
    return JsonResponse(payload)


@login_required
def historico_view(request):
    consultas = ConsultaHistorico.objects.filter(usuario=request.user)
    return render(request, "buscarrural/historico.html", {"consultas": consultas})


@login_required
def detalhe_view(request, pk):
    consulta = get_object_or_404(ConsultaHistorico, pk=pk, usuario=request.user)
    campos = consulta.dados.get("campos", {}) if consulta.dados else {}
    secoes = consulta.dados.get("secoes", []) if consulta.dados else []
    indicadores = None
    secoes_diagnostico = []
    if consulta.dados:
        indicadores = extrair_indicadores_car(
            consulta.dados,
            consulta.numero_car,
            consulta.atualizado_em_site,
        )
    if consulta.parecer_diagnostico:
        secoes_diagnostico = consulta.parecer_diagnostico.get("secoes") or []

    return render(
        request,
        "buscarrural/detalhe.html",
        {
            "consulta": consulta,
            "campos": campos,
            "secoes": secoes,
            "indicadores": indicadores,
            "secoes_diagnostico": secoes_diagnostico,
            "pode_gerar_parecer": (
                consulta.status == ConsultaHistorico.STATUS_SUCESSO
                and bool(consulta.dados)
            ),
            "tem_parecer": bool(consulta.parecer_diagnostico or consulta.parecer),
        },
    )


@login_required
@require_http_methods(["POST"])
def gerar_parecer_view(request, pk):
    consulta = get_object_or_404(ConsultaHistorico, pk=pk, usuario=request.user)
    if consulta.parecer:
        messages.info(request, "Diagnóstico anterior será substituído por uma nova análise.")
    if consulta.status != ConsultaHistorico.STATUS_SUCESSO:
        messages.error(request, "Só é possível gerar diagnóstico para consultas concluídas.")
        return redirect("buscarrural:detalhe", pk=consulta.pk)

    try:
        salvar_parecer_consulta(consulta)
        messages.success(request, "Diagnóstico técnico preliminar e PDF gerados com sucesso.")
    except ParecerIAError as exc:
        messages.error(request, str(exc))

    return redirect("buscarrural:detalhe", pk=consulta.pk)


@login_required
@require_http_methods(["GET"])
def redirect_consultar(request):
    return redirect("buscarrural:consultar")
