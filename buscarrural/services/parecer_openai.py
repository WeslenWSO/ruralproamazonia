import json
import logging

from django.conf import settings
from openai import OpenAI

from buscarrural.services.parecer_gemini import (
    _combinar_alertas,
    _detectar_alertas_automaticos,
    _montar_contexto,
)

logger = logging.getLogger(__name__)

SECOES_DIAGNOSTICO = (
    ("resumo", "leitura_direta_resumo", "RESUMO DA SITUAÇÃO ATUAL"),
    ("certo_falta", "leitura_direta_certo_falta", "O QUE ESTÁ CERTO E O QUE FALTA"),
    ("riscos", "leitura_direta_riscos", "RISCOS E IMPACTOS PRÁTICOS NO DIA A DIA DO PRODUTOR"),
    ("plano_acao", "leitura_direta_plano", "PLANO PRÁTICO DE AÇÃO"),
    ("conclusao", "leitura_direta_conclusao", "CONCLUSÃO & CHAMADA PARA AÇÃO"),
)

SCHEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "resumo": {"type": "string"},
        "leitura_direta_resumo": {"type": "string"},
        "certo_falta": {"type": "string"},
        "leitura_direta_certo_falta": {"type": "string"},
        "riscos": {"type": "string"},
        "leitura_direta_riscos": {"type": "string"},
        "plano_acao": {"type": "string"},
        "leitura_direta_plano": {"type": "string"},
        "conclusao": {"type": "string"},
        "leitura_direta_conclusao": {"type": "string"},
        "alertas_criticos": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "resumo",
        "leitura_direta_resumo",
        "certo_falta",
        "leitura_direta_certo_falta",
        "riscos",
        "leitura_direta_riscos",
        "plano_acao",
        "leitura_direta_plano",
        "conclusao",
        "leitura_direta_conclusao",
        "alertas_criticos",
    ],
    "additionalProperties": False,
}


class ParecerIAError(Exception):
    pass


def _validar_chave():
    if not settings.OPENAI_API_KEY:
        raise ParecerIAError(
            "OPENAI_API_KEY não configurada. Adicione a chave no arquivo .env (não versionado)."
        )


def _montar_prompt(contexto, alertas_auto):
    alertas_hint = ""
    if alertas_auto:
        alertas_hint = (
            "\nIndícios detectados nos dados (confirme ou refine):\n"
            + "\n".join(f"- {a}" for a in alertas_auto[:12])
        )

    return f"""Atue como Consultor Especialista em Gestão, Regularização Fundiária e Ambiental da RuralPro.

Analise os dados do Selo Verde AC abaixo e elabore um Diagnóstico Técnico Preliminar em linguagem simples para o produtor rural.

DIRETRIZES:
- Evite juridiquês; explique termos técnicos indispensáveis (CAR, APP, RL, SIGEF, PRADA, CCIR, LAU) em frase prática.
- Tom profissional, transparente e focado em soluções.
- Use EXCLUSIVAMENTE os dados fornecidos; não invente áreas, status ou percentuais.
- Cada seção: 2 a 4 parágrafos curtos ou bullets claros.
- plano_acao: organize como Etapa 1, Etapa 2, Etapa 3 em ordem de prioridade.
- leitura_direta_*: 1 ou 2 frases resumindo o essencial da seção.
- alertas_criticos: bullets só de riscos críticos reais nos dados; se não houver, lista vazia.
{alertas_hint}

DADOS DO SELO VERDE AC:
{contexto}
"""


def _montar_secoes_pdf(parsed):
    secoes = []
    for idx, (campo, campo_leitura, titulo) in enumerate(SECOES_DIAGNOSTICO, start=1):
        secoes.append(
            {
                "numero": idx,
                "titulo": titulo,
                "texto": (parsed.get(campo) or "").strip(),
                "leitura_direta": (parsed.get(campo_leitura) or "").strip(),
            }
        )
    return secoes


def _texto_parecer_completo(secoes):
    partes = []
    for secao in secoes:
        partes.append(f"## {secao['titulo']}\n{secao['texto']}")
    return "\n\n".join(partes)


def gerar_diagnostico_openai(numero_car, dados, atualizado_em_site=""):
    _validar_chave()
    if not dados:
        raise ParecerIAError("Sem dados do Selo Verde para gerar o diagnóstico.")

    alertas_auto = _detectar_alertas_automaticos(dados)
    contexto = _montar_contexto(numero_car, dados, atualizado_em_site)
    prompt = _montar_prompt(contexto, alertas_auto)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = settings.OPENAI_MODEL or "gpt-4o-mini"

    try:
        resposta = client.chat.completions.create(
            model=model,
            temperature=0.25,
            max_tokens=3500,
            messages=[
                {
                    "role": "system",
                    "content": "Você responde somente em JSON válido conforme o schema solicitado, em português do Brasil.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "diagnostico_ruralpro",
                    "strict": True,
                    "schema": SCHEMA_RESPOSTA,
                },
            },
        )
    except Exception as exc:
        logger.warning("OpenAI falhou (%s): %s", model, exc)
        raise ParecerIAError(
            f"Não foi possível gerar o diagnóstico. Verifique OPENAI_API_KEY e o modelo ({model})."
        ) from exc

    bruto = (resposta.choices[0].message.content or "").strip()
    if not bruto:
        raise ParecerIAError("Resposta vazia da OpenAI.")

    try:
        parsed = json.loads(bruto)
    except json.JSONDecodeError as exc:
        raise ParecerIAError("Resposta da OpenAI não é JSON válido.") from exc

    secoes = _montar_secoes_pdf(parsed)
    alertas_ia = parsed.get("alertas_criticos") or []
    alertas_texto = _combinar_alertas(
        alertas_auto,
        "\n".join(f"- {a}" for a in alertas_ia if a),
    )

    diagnostico = {
        "secoes": secoes,
        "alertas_lista": alertas_ia,
    }

    return {
        "parecer": _texto_parecer_completo(secoes),
        "parecer_diagnostico": diagnostico,
        "alertas_criticos": alertas_texto,
    }
