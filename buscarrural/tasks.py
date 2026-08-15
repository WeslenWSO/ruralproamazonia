import logging
import threading

from django.conf import settings
from django.db import close_old_connections

from buscarrural.models import ConsultaHistorico
from buscarrural.services.parecer_ia import ParecerIAError, chave_ia_configurada, gerar_diagnostico_consulta
from buscarrural.services.parecer_pdf import gerar_pdf_diagnostico
from buscarrural.services.selo_verde_acre import SeloVerdeAcreError, _salvar_imagem_terreno_consulta, consultar_selo_verde_acre
from buscarrural.services.storage_consulta import anexar_pdf_consulta, salvar_resultado_consulta

logger = logging.getLogger(__name__)


def _aplicar_diagnostico(consulta, resultado):
    consulta.parecer = resultado["parecer"]
    consulta.parecer_diagnostico = resultado.get("parecer_diagnostico") or {}
    consulta.alertas_criticos = resultado.get("alertas_criticos", "")
    consulta.save(
        update_fields=[
            "parecer",
            "parecer_diagnostico",
            "alertas_criticos",
            "atualizado_em",
        ]
    )


def _gerar_pdf_e_storage(consulta):
    if not consulta.parecer_diagnostico:
        return consulta
    try:
        caminho = gerar_pdf_diagnostico(consulta)
        anexar_pdf_consulta(consulta, caminho)
        salvar_resultado_consulta(consulta)
    except Exception as exc:
        logger.warning("PDF diagnóstico não gerado (consulta %s): %s", consulta.pk, exc)
    return consulta


def salvar_parecer_consulta(consulta):
    if not chave_ia_configurada():
        raise ParecerIAError(
            "OPENAI_API_KEY ou GEMINI_API_KEY não configurada. Adicione a chave no arquivo .env."
        )
    if not consulta.dados:
        raise ParecerIAError("Esta consulta não possui dados do Selo Verde.")

    resultado = gerar_diagnostico_consulta(
        consulta.numero_car,
        consulta.dados,
        consulta.atualizado_em_site,
    )
    _aplicar_diagnostico(consulta, resultado)
    _gerar_pdf_e_storage(consulta)
    return consulta.parecer


def executar_consulta_em_background(consulta_id):
    close_old_connections()
    consulta = ConsultaHistorico.objects.filter(pk=consulta_id).first()
    if not consulta:
        return

    def atualizar_progresso(mensagem):
        ConsultaHistorico.objects.filter(pk=consulta_id).update(mensagem_erro=mensagem)

    try:
        resultado = consultar_selo_verde_acre(
            consulta.numero_car,
            on_progress=atualizar_progresso,
            consulta_id=consulta.pk,
        )
        consulta.dados = resultado["dados"]
        consulta.atualizado_em_site = resultado.get("atualizado_em_site", "")

        caminho_mapa = resultado.get("imagem_terreno")
        if caminho_mapa:
            _salvar_imagem_terreno_consulta(consulta, caminho_mapa)

        if chave_ia_configurada():
            atualizar_progresso("Elaborando diagnóstico técnico preliminar (IA)…")
            try:
                diag = gerar_diagnostico_consulta(
                    consulta.numero_car,
                    consulta.dados,
                    consulta.atualizado_em_site,
                )
                consulta.parecer = diag["parecer"]
                consulta.parecer_diagnostico = diag.get("parecer_diagnostico") or {}
                consulta.alertas_criticos = diag.get("alertas_criticos", "")
            except ParecerIAError as exc:
                consulta.parecer = ""
                consulta.parecer_diagnostico = {}
                consulta.alertas_criticos = ""
                logger.warning("Diagnóstico IA não gerado (consulta %s): %s", consulta_id, exc)

        consulta.status = ConsultaHistorico.STATUS_SUCESSO
        consulta.mensagem_erro = ""
        consulta.save()

        if consulta.parecer_diagnostico:
            atualizar_progresso("Gerando PDF folder RuralPro…")
            _gerar_pdf_e_storage(consulta)
        elif consulta.dados:
            salvar_resultado_consulta(consulta)

        logger.info("Consulta %s concluída com sucesso", consulta_id)
    except SeloVerdeAcreError as exc:
        consulta.refresh_from_db()
        consulta.status = ConsultaHistorico.STATUS_ERRO
        consulta.mensagem_erro = str(exc)
        consulta.save()
        logger.warning("Consulta %s falhou: %s", consulta_id, exc)
    except Exception as exc:
        consulta.refresh_from_db()
        msg = str(exc)
        if "invalid session id" in msg.lower() or "not connected to devtools" in msg.lower():
            msg = (
                "O Chrome foi fechado durante a consulta. "
                "Deixe a janela aberta, marque o captcha e tente novamente."
            )
        consulta.status = ConsultaHistorico.STATUS_ERRO
        consulta.mensagem_erro = f"Erro inesperado: {msg}" if not msg.startswith("O Chrome") else msg
        consulta.save()
        logger.exception("Consulta %s erro inesperado", consulta_id)
    finally:
        close_old_connections()


def iniciar_consulta_async(consulta):
    thread = threading.Thread(
        target=executar_consulta_em_background,
        args=(consulta.pk,),
        daemon=True,
        name=f"selo-verde-{consulta.pk}",
    )
    thread.start()
    return thread
