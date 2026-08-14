import logging
import threading

from django.conf import settings
from django.db import close_old_connections

from buscarrural.models import ConsultaHistorico
from buscarrural.services.parecer_gemini import ParecerGeminiError, gerar_parecer_selo_verde
from buscarrural.services.selo_verde_acre import SeloVerdeAcreError, consultar_selo_verde_acre

logger = logging.getLogger(__name__)


def salvar_parecer_consulta(consulta):
    if not settings.GEMINI_API_KEY:
        raise ParecerGeminiError(
            "GEMINI_API_KEY não configurada. Adicione a chave no arquivo .env."
        )
    if not consulta.dados:
        raise ParecerGeminiError("Esta consulta não possui dados do Selo Verde.")

    resultado = gerar_parecer_selo_verde(
        consulta.numero_car,
        consulta.dados,
        consulta.atualizado_em_site,
    )
    consulta.parecer = resultado["parecer"]
    consulta.alertas_criticos = resultado["alertas_criticos"]
    consulta.save(update_fields=["parecer", "alertas_criticos", "atualizado_em"])
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
        )
        consulta.dados = resultado["dados"]
        consulta.atualizado_em_site = resultado.get("atualizado_em_site", "")

        if settings.GEMINI_API_KEY:
            atualizar_progresso("Analisando situação conforme legislação ambiental (IA)…")
            try:
                salvar_parecer_consulta(consulta)
            except ParecerGeminiError as exc:
                consulta.parecer = ""
                consulta.alertas_criticos = ""
                logger.warning("Parecer Gemini não gerado (consulta %s): %s", consulta_id, exc)

        consulta.status = ConsultaHistorico.STATUS_SUCESSO
        consulta.mensagem_erro = ""
        consulta.save()
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
