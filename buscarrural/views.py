from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from buscarrural.forms import ConsultaCARForm
from buscarrural.models import ConsultaHistorico
from buscarrural.services.parecer_gemini import ParecerGeminiError
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
    return render(
        request,
        "buscarrural/detalhe.html",
        {
            "consulta": consulta,
            "campos": campos,
            "secoes": secoes,
            "pode_gerar_parecer": (
                consulta.status == ConsultaHistorico.STATUS_SUCESSO
                and bool(consulta.dados)
            ),
            "tem_parecer": bool(consulta.parecer),
        },
    )


@login_required
@require_http_methods(["POST"])
def gerar_parecer_view(request, pk):
    consulta = get_object_or_404(ConsultaHistorico, pk=pk, usuario=request.user)
    if consulta.parecer:
        messages.info(request, "Parecer anterior será substituído por uma nova análise.")
    if consulta.status != ConsultaHistorico.STATUS_SUCESSO:
        messages.error(request, "Só é possível gerar parecer para consultas concluídas.")
        return redirect("buscarrural:detalhe", pk=consulta.pk)

    try:
        salvar_parecer_consulta(consulta)
        messages.success(request, "Mini parecer e alertas críticos gerados com sucesso.")
    except ParecerGeminiError as exc:
        messages.error(request, str(exc))

    return redirect("buscarrural:detalhe", pk=consulta.pk)


@login_required
@require_http_methods(["GET"])
def redirect_consultar(request):
    return redirect("buscarrural:consultar")
