import logging

from django.conf import settings
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

logger = logging.getLogger(__name__)

MODELOS_FALLBACK = (
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
)


class ParecerGeminiError(Exception):
    pass


def _validar_chave_api(api_key):
    if not api_key:
        raise ParecerGeminiError(
            "GEMINI_API_KEY nao configurada. Adicione a chave no arquivo .env (nao versionado)."
        )


def _modelos_para_tentar():
    principal = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash").strip()
    vistos = set()
    modelos = []
    for nome in (principal, *MODELOS_FALLBACK):
        if nome and nome not in vistos:
            vistos.add(nome)
            modelos.append(nome)
    return modelos


def _extrair_erro_api(exc):
    if isinstance(exc, genai_errors.ClientError):
        mensagem = str(exc).strip()
        if mensagem:
            return mensagem
    return str(exc).strip() or "Erro desconhecido ao chamar o Gemini."


def _cliente_gemini(api_key):
    return genai.Client(api_key=api_key)


def _chamar_gemini(client, model, prompt):
    config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1200,
    )
    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )


def _montar_contexto(numero_car, dados, atualizado_em_site=""):
    linhas = [f"Código CAR: {numero_car}"]
    if atualizado_em_site:
        linhas.append(f"Dados atualizados no Selo Verde AC em: {atualizado_em_site}")

    secoes = dados.get("secoes") or []
    if secoes:
        for secao in secoes:
            titulo = (secao.get("titulo") or "").strip()
            if titulo:
                linhas.append(f"\n## {titulo}")
            for item in secao.get("linhas") or []:
                rotulo = (item.get("rotulo") or "").strip()
                valor = (item.get("valor") or "").strip()
                if rotulo:
                    linhas.append(f"- {rotulo}: {valor or '—'}")
    else:
        for rotulo, valor in (dados.get("campos") or {}).items():
            linhas.append(f"- {rotulo}: {valor or '—'}")

    resumo = (dados.get("texto_resumo") or "").strip()
    if resumo and len(resumo) > 500:
        linhas.append("\n## Resumo complementar (trecho)")
        linhas.append(resumo[:8000])

    return "\n".join(linhas)


def _montar_prompt(contexto):
    return f"""Você é assistente da Rural Pro Amazônia, com foco em regularização fundiária e ambiental de imóveis rurais no Acre.

Com base EXCLUSIVAMENTE nos dados abaixo do Selo Verde AC (SEMA/AC), redija um MINI PARECER sobre a situação deste imóvel rural, relacionando os achados à legislação aplicável quando houver base nos dados.

Legislação de referência (cite apenas o que for pertinente ao que aparece nos dados):
- Lei nº 12.651/2012 (Código Florestal): CAR, APP, Reserva Legal, restauração e compensação.
- Reserva Legal na Amazônia Legal: 80% do imóvel (ou percentuais/ regimes específicos se constarem nos dados).
- APP em curso d'água, nascentes, veredas, topos de morro e demais restritivos legais.
- Obrigatoriedade e validação do CAR junto ao órgão estadual (SEMA/AC).
- Eventuais embargos, pendências, sobreposições ou inconsistências cadastrais indicadas no relatório.

Regras:
- Escreva em português do Brasil, tom técnico porém acessível ao produtor rural.
- Seja BREVE: mini parecer com no máximo 12 linhas ou ~150 palavras.
- Não invente dados, áreas, percentuais ou status que não estejam no contexto.
- Se faltar informação, diga o que não foi possível avaliar.
- Estruture em parágrafos curtos:
  1) Síntese da situação;
  2) Conformidades e/ou pendências observadas (com menção legal quando couber);
  3) Recomendação prática imediata.
- NÃO inclua o aviso final sobre engenheiro ambiental (será adicionado pelo sistema).
- Não use markdown com títulos longos; preferir texto corrido objetivo.

DADOS DO SELO VERDE AC:
{contexto}
"""


def gerar_parecer_selo_verde(numero_car, dados, atualizado_em_site=""):
    api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
    _validar_chave_api(api_key)

    if not dados:
        raise ParecerGeminiError("Sem dados do Selo Verde para gerar o parecer.")

    contexto = _montar_contexto(numero_car, dados, atualizado_em_site)
    prompt = _montar_prompt(contexto)
    client = _cliente_gemini(api_key)

    ultimo_erro = ""
    for model in _modelos_para_tentar():
        try:
            resposta = _chamar_gemini(client, model, prompt)
            texto = (resposta.text or "").strip()
            if texto:
                logger.info("Parecer gerado com modelo %s", model)
                return texto
            ultimo_erro = "Resposta vazia do Gemini."
        except genai_errors.ClientError as exc:
            ultimo_erro = _extrair_erro_api(exc)
            logger.warning("Gemini modelo %s falhou: %s", model, ultimo_erro)
            if exc.code in (401, 403):
                raise ParecerGeminiError(
                    "Chave Gemini recusada pela Google. Verifique GEMINI_API_KEY no .env "
                    "(chave do Google AI Studio)."
                ) from exc
            continue
        except Exception as exc:
            ultimo_erro = str(exc)
            logger.warning("Erro Gemini (%s): %s", model, exc)

    raise ParecerGeminiError(
        ultimo_erro
        or "Nao foi possivel gerar o parecer. Confira a chave e o modelo Gemini no .env."
    )
