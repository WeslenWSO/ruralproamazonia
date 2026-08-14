import logging
import re

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

BLOCOS_RELATORIO = (
    "Identificação e dados do CAR",
    "Cadastro Ambiental Rural (CAR)",
    "Protocolo MPF / monitoramento de gado",
    "Projeto Floresta + Amazônia",
    "Cobertura do solo e vegetação",
    "Balanço ambiental (Código Florestal)",
    "Reserva Legal e APP",
    "Conformidade socioambiental",
    "Embargos, infrações e sanções",
    "Desmatamento (PRODES/DETER)",
    "Sobreposições e conflitos fundiários",
    "Sistema de Gestão Fundiária (SIGEF/INCRA)",
    "Demais informações do relatório",
)

VALORES_OK = frozenset(
    {
        "",
        "—",
        "-",
        "nao",
        "não",
        "nao ha",
        "não há",
        "nao ha.",
        "não há.",
        "sem",
        "nenhum",
        "nenhuma",
        "0",
        "0,00",
        "0.00",
        "nao detectado",
        "não detectado",
        "nao detectadas",
        "não detectadas",
        "nao foram detectadas",
        "não foram detectadas",
        "apto",
        "regular",
        "regularizado",
        "ativo",
        "conforme",
        "sem pendencia",
        "sem pendência",
    }
)

ROTULOS_CRITICOS = (
    ("déficit", "Déficit ambiental declarado"),
    ("deficit", "Déficit ambiental declarado"),
    ("embargo", "Embargo ou restrição ambiental"),
    ("infração", "Auto de infração ou sanção"),
    ("infracao", "Auto de infração ou sanção"),
    ("prodes", "Alerta de desmatamento (PRODES)"),
    ("deter", "Alerta de desmatamento (DETER)"),
    ("sobrepos", "Sobreposição de imóveis ou cadastros"),
    ("inapto", "Situação inapta em protocolo/programa"),
    ("irregular", "Irregularidade cadastral ou ambiental"),
    ("pendenc", "Pendência cadastral ou ambiental"),
    ("sigef", "Pendência no SIGEF/INCRA"),
    ("incra", "Pendência fundiária (INCRA/SIGEF)"),
    ("assentamento", "Conflito com assentamento ou área pública"),
    ("supress", "Supressão de vegetação"),
    ("desmat", "Indício de desmatamento"),
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
        temperature=0.25,
        max_output_tokens=2200,
    )
    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )


def _normalizar(texto):
    return re.sub(r"\s+", " ", (texto or "").strip().lower())


def _valor_critico(valor):
    norm = _normalizar(valor)
    if not norm or norm in VALORES_OK:
        return False
    if any(
        termo in norm
        for termo in (
            "déficit",
            "deficit",
            "embarg",
            "infra",
            "inapto",
            "irregular",
            "prodes",
            "deter",
            "sobrepos",
            "pendenc",
            "supress",
            "desmat",
            "nao conforme",
            "não conforme",
            "inconsistente",
        )
    ):
        return True
    if norm.startswith("sim") or norm == "sim":
        return True
    return bool(re.search(r"\b\d+[,.]?\d*\s*ha\b", norm))


def _classificar_bloco(titulo, rotulo=""):
    texto = _normalizar(f"{titulo} {rotulo}")
    if "sigef" in texto or "incra" in texto or "gestao fundi" in texto or "gestão fundi" in texto:
        return "Sistema de Gestão Fundiária (SIGEF/INCRA)"
    if "car" in texto and ("codigo" in texto or "código" in texto or "cadastro" in texto):
        return "Cadastro Ambiental Rural (CAR)"
    if "mpf" in texto or "gado" in texto or "monitoramento" in texto:
        return "Protocolo MPF / monitoramento de gado"
    if "floresta" in texto and "amazon" in texto:
        return "Projeto Floresta + Amazônia"
    if "cobertura" in texto or "vegeta" in texto:
        return "Cobertura do solo e vegetação"
    if "balanco" in texto or "balanço" in texto or "codigo florestal" in texto:
        return "Balanço ambiental (Código Florestal)"
    if "reserva legal" in texto or " app" in f" {texto} " or "preservacao permanente" in texto:
        return "Reserva Legal e APP"
    if "conformidade" in texto or "socioambient" in texto:
        return "Conformidade socioambiental"
    if "embargo" in texto or "infra" in texto or "san" in texto:
        return "Embargos, infrações e sanções"
    if "prodes" in texto or "deter" in texto or "desmat" in texto:
        return "Desmatamento (PRODES/DETER)"
    if "sobrepos" in texto or "assentamento" in texto or "conflit" in texto:
        return "Sobreposições e conflitos fundiários"
    if "emiss" in texto or "atualizado" in texto:
        return "Identificação e dados do CAR"
    return "Demais informações do relatório"


def _iterar_itens(dados):
    vistos = set()
    for secao in dados.get("secoes") or []:
        titulo = (secao.get("titulo") or "").strip()
        for item in secao.get("linhas") or []:
            rotulo = (item.get("rotulo") or "").strip()
            valor = (item.get("valor") or "").strip()
            if not rotulo:
                continue
            chave = (rotulo, valor)
            if chave in vistos:
                continue
            vistos.add(chave)
            yield titulo, rotulo, valor

    for rotulo, valor in (dados.get("campos") or {}).items():
        rotulo = (rotulo or "").strip()
        valor = (valor or "").strip()
        if not rotulo:
            continue
        chave = (rotulo, valor)
        if chave in vistos:
            continue
        vistos.add(chave)
        yield "", rotulo, valor


def _montar_contexto(numero_car, dados, atualizado_em_site=""):
    linhas = [
        f"Código CAR consultado: {numero_car}",
        "Relatório socioambiental integrado Selo Verde AC (SEMA/AC), do CAR ao SIGEF/INCRA.",
    ]
    if atualizado_em_site:
        linhas.append(f"Dados atualizados no Selo Verde AC em: {atualizado_em_site}")

    blocos = {nome: [] for nome in BLOCOS_RELATORIO}
    for titulo_secao, rotulo, valor in _iterar_itens(dados):
        bloco = _classificar_bloco(titulo_secao, rotulo)
        blocos[bloco].append(f"- {rotulo}: {valor or '—'}")

    for nome in BLOCOS_RELATORIO:
        itens = blocos.get(nome) or []
        if not itens:
            continue
        linhas.append(f"\n### {nome}")
        linhas.extend(itens[:40])

    resumo = (dados.get("texto_resumo") or "").strip()
    if resumo:
        linhas.append("\n### Trecho bruto complementar do relatório")
        linhas.append(resumo[:10000])

    return "\n".join(linhas)


def _detectar_alertas_automaticos(dados):
    alertas = []
    for _, rotulo, valor in _iterar_itens(dados):
        rotulo_norm = _normalizar(rotulo)
        valor_norm = _normalizar(valor)
        if not valor_norm or valor_norm in VALORES_OK:
            continue

        for termo, titulo in ROTULOS_CRITICOS:
            if termo in rotulo_norm or termo in valor_norm:
                if _valor_critico(valor) or termo in valor_norm:
                    alertas.append(f"{titulo}: {rotulo} — {valor}")
                    break

    vistos = set()
    unicos = []
    for item in alertas:
        if item not in vistos:
            vistos.add(item)
            unicos.append(item)
    return unicos


def _montar_prompt(contexto, alertas_auto):
    alertas_hint = ""
    if alertas_auto:
        alertas_hint = (
            "\nIndícios já detectados automaticamente nos dados (confirme ou refine):\n"
            + "\n".join(f"- {a}" for a in alertas_auto[:12])
        )

    return f"""Você é assistente da Rural Pro Amazônia, especializado em regularização ambiental e fundiária de imóveis rurais no Acre.

Analise TODO o relatório Selo Verde AC abaixo, cobrindo integralmente:
1) Cadastro Ambiental Rural (CAR) e situação do imóvel;
2) Protocolos e programas (MPF, Floresta+Amazônia, quando houver);
3) Cobertura do solo, vegetação e balanço ambiental (Código Florestal — Lei 12.651/2012);
4) Reserva Legal, APP, restauração, compensação e déficits;
5) Conformidade socioambiental, embargos, infrações, PRODES/DETER e sobreposições;
6) Situação fundiária no SIGEF/INCRA e demais pendências cadastrais.

Legislação de referência (cite só o pertinente aos dados):
- Lei nº 12.651/2012 (Código Florestal): CAR, RL, APP, restauração e compensação;
- Reserva Legal na Amazônia Legal: regra geral de 80% (ou percentual/regime indicado nos dados);
- Restrições de APP e uso consolidado;
- Obrigações de validação/atualização do CAR perante a SEMA/AC;
- Regularização fundiária (SIGEF/INCRA) quando constar nos dados;
- Embargos, autos de infração, sanções e sobreposições, quando indicados.

Regras:
- Use EXCLUSIVAMENTE os dados fornecidos; não invente áreas, status ou percentuais.
- Se faltar dado para avaliar um bloco (ex.: SIGEF), diga explicitamente.
- Tom técnico e acessível ao produtor rural, em português do Brasil.
- NÃO inclua aviso para procurar engenheiro ambiental (será adicionado pelo sistema).
{alertas_hint}

Responda EXATAMENTE neste formato (mantenha os marcadores):

===MINI PARECER===
Parágrafo 1 — síntese geral do imóvel (CAR, área, situação cadastral/ambiental).
Parágrafo 2 — análise ambiental (RL, APP, balanço, conformidade, embargos/PRODES se houver).
Parágrafo 3 — análise fundiária (SIGEF/INCRA, sobreposições, assentamentos, se houver dados).
Parágrafo 4 — recomendação prática imediata e próximos passos.
Total aproximado: 250 a 450 palavras, objetivo e completo.

===ALERTAS CRITICOS===
Liste em bullets apenas pontos CRÍTICOS (risco legal, embargo, déficit RL/APP, desmatamento, inaptidão, pendência SIGEF, sobreposição grave).
Se não houver criticidade com base nos dados, escreva uma única linha: Nenhum alerta crítico identificado nos dados disponíveis.

DADOS DO SELO VERDE AC:
{contexto}
"""


def _parsear_resposta_gemini(texto):
    bruto = (texto or "").strip()
    if not bruto:
        return {"parecer": "", "alertas_criticos": ""}

    match_parecer = re.search(
        r"===MINI PARECER===\s*(.*?)\s*(?:===ALERTAS CRITICOS===|$)",
        bruto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    match_alertas = re.search(
        r"===ALERTAS CRITICOS===\s*(.*)$",
        bruto,
        flags=re.IGNORECASE | re.DOTALL,
    )

    parecer = (match_parecer.group(1).strip() if match_parecer else bruto).strip()
    alertas = (match_alertas.group(1).strip() if match_alertas else "").strip()

    if alertas.startswith("- "):
        alertas = alertas
    elif alertas and not alertas.lower().startswith("nenhum alerta"):
        alertas = alertas

    return {"parecer": parecer, "alertas_criticos": alertas}


def _combinar_alertas(alertas_auto, alertas_gemini):
    linhas = []
    vistos = set()

    def adicionar(item):
        item = (item or "").strip()
        if not item:
            return
        chave = _normalizar(item)
        if chave in vistos:
            return
        vistos.add(chave)
        linhas.append(item if item.startswith("- ") else f"- {item}")

    for item in alertas_auto:
        adicionar(item)

    if alertas_gemini:
        if alertas_gemini.lower().startswith("nenhum alerta"):
            if not linhas:
                return alertas_gemini
        else:
            for parte in re.split(r"[\r\n]+", alertas_gemini):
                parte = parte.strip(" •-\t")
                if parte:
                    adicionar(parte)

    if not linhas:
        return "Nenhum alerta crítico identificado nos dados disponíveis."
    return "\n".join(linhas)


def gerar_parecer_selo_verde(numero_car, dados, atualizado_em_site=""):
    api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
    _validar_chave_api(api_key)

    if not dados:
        raise ParecerGeminiError("Sem dados do Selo Verde para gerar o parecer.")

    alertas_auto = _detectar_alertas_automaticos(dados)
    contexto = _montar_contexto(numero_car, dados, atualizado_em_site)
    prompt = _montar_prompt(contexto, alertas_auto)
    client = _cliente_gemini(api_key)

    ultimo_erro = ""
    for model in _modelos_para_tentar():
        try:
            resposta = _chamar_gemini(client, model, prompt)
            texto = (resposta.text or "").strip()
            if not texto:
                ultimo_erro = "Resposta vazia do Gemini."
                continue

            parsed = _parsear_resposta_gemini(texto)
            if not parsed["parecer"]:
                ultimo_erro = "Resposta do Gemini sem mini parecer."
                continue

            logger.info("Parecer gerado com modelo %s", model)
            return {
                "parecer": parsed["parecer"],
                "alertas_criticos": _combinar_alertas(
                    alertas_auto,
                    parsed["alertas_criticos"],
                ),
            }
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
