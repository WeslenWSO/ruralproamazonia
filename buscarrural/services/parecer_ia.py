import logging

from django.conf import settings

from buscarrural.services.parecer_openai import ParecerIAError, gerar_diagnostico_openai

logger = logging.getLogger(__name__)


def _importar_gemini():
    from buscarrural.services.parecer_gemini import (
        ParecerGeminiError,
        gerar_parecer_selo_verde as gerar_parecer_gemini,
    )

    return ParecerGeminiError, gerar_parecer_gemini


def _gemini_para_diagnostico(resultado):
    parecer = resultado.get("parecer", "")
    return {
        "parecer": parecer,
        "parecer_diagnostico": {
            "secoes": [
                {
                    "numero": 1,
                    "titulo": "RESUMO DA SITUAÇÃO ATUAL",
                    "texto": parecer,
                    "leitura_direta": (resultado.get("alertas_criticos") or "")[:280],
                }
            ],
            "alertas_lista": [],
        },
        "alertas_criticos": resultado.get("alertas_criticos", ""),
    }


def gerar_diagnostico_consulta(numero_car, dados, atualizado_em_site=""):
    provider = (settings.PARECER_IA_PROVIDER or "openai").lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ParecerIAError("GEMINI_API_KEY não configurada.")
        ParecerGeminiError, gerar_parecer_gemini = _importar_gemini()
        try:
            resultado = gerar_parecer_gemini(numero_car, dados, atualizado_em_site)
            return _gemini_para_diagnostico(resultado)
        except ParecerGeminiError as exc:
            raise ParecerIAError(str(exc)) from exc

    try:
        return gerar_diagnostico_openai(numero_car, dados, atualizado_em_site)
    except ParecerIAError:
        if settings.GEMINI_API_KEY:
            logger.warning("OpenAI falhou; tentando Gemini como fallback.")
            ParecerGeminiError, gerar_parecer_gemini = _importar_gemini()
            try:
                resultado = gerar_parecer_gemini(numero_car, dados, atualizado_em_site)
                return _gemini_para_diagnostico(resultado)
            except ParecerGeminiError as exc:
                raise ParecerIAError(str(exc)) from exc
        raise


def chave_ia_configurada():
    provider = (settings.PARECER_IA_PROVIDER or "openai").lower()
    if provider == "gemini":
        return bool(settings.GEMINI_API_KEY)
    return bool(settings.OPENAI_API_KEY) or bool(settings.GEMINI_API_KEY)
