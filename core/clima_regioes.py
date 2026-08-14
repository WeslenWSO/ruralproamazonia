from core.clima import MUNICIPIOS_CLIMA, _descricao_clima, _icone_clima

REGIOES_CLIMA = [
    {
        "numero": 1,
        "titulo": "REGIÃO 1",
        "cidades": "Assis Brasil • Brasiléia • Xapuri",
        "ids": ["assis-brasil", "brasileia"],
    },
    {
        "numero": 2,
        "titulo": "REGIÃO 2",
        "cidades": "Capixaba • Porto Acre • Rio Branco • Sena Madureira",
        "ids": ["capixaba", "rio-branco", "sena-madureira"],
    },
    {
        "numero": 3,
        "titulo": "REGIÃO 3",
        "cidades": "Cruzeiro do Sul • Feijó • Manoel Urbano • Tarauacá",
        "ids": ["cruzeiro-do-sul", "feijo", "tarauaca"],
    },
    {
        "numero": 4,
        "titulo": "REGIÃO 4",
        "cidades": "Acrelândia • Plácido de Castro",
        "ids": ["acrelandia", "placido-de-castro"],
    },
    {
        "numero": 5,
        "titulo": "REGIÃO 5",
        "cidades": "Extrema • Vista Alegre do Abunã • Nova Califórnia",
        "ids": ["extrema", "vista-alegre-do-abuna", "nova-california"],
    },
]

MUNICIPIOS_POR_ID = {m["id"]: m for m in MUNICIPIOS_CLIMA}


def _resumo_regiao(itens):
    if not itens or all(i.get("erro") for i in itens):
        return "Dados temporariamente indisponíveis para esta região."

    validos = [i for i in itens if not i.get("erro")]
    chuva = sum(float(i.get("chuva_dia") or 0) for i in validos)
    max_temp = max(i["temp_max"] for i in validos)
    codigos = [i.get("codigo", 0) for i in validos]
    tempestade = any(c in (95, 96, 99, 82) for c in codigos)
    nublado = sum(1 for c in codigos if c >= 3) >= len(codigos) / 2

    if tempestade:
        return (
            "Risco de pancadas e trovoadas isoladas. Evite operações a céu aberto "
            "e monitore alertas oficiais durante a tarde."
        )
    if chuva >= 5:
        return (
            "Chuva prevista em parte da região. Priorize serviços pela manhã "
            "e mantenha cobertura para equipamentos e grãos."
        )
    if nublado:
        return (
            "Céu variável com períodos de sol e nuvens. Boa janela para campo "
            "no início da manhã e final da tarde."
        )
    if max_temp >= 34:
        return (
            "Sol forte e calor intenso ao meio-dia. Umidade tende a cair "
            "entre 11h e 15h — planeje esforço físico fora desse horário."
        )
    return (
        "Sol forte e pouco volume de chuva ao longo do dia. Condições favoráveis "
        "para atividades de campo com atenção ao calor da tarde."
    )


def _condicao_resumida(itens):
    validos = [i for i in itens if not i.get("erro")]
    if not validos:
        return "SEM DADOS", 0
    codigo = max(i.get("codigo", 0) for i in validos)
    condicao = _descricao_clima(codigo).upper()
    if all(i.get("codigo", 0) in (0, 1) for i in validos):
        condicao = "SOL E POUCAS NUVENS"
    elif any(i.get("chuva_dia", 0) and float(i["chuva_dia"]) >= 1 for i in validos):
        condicao = "PERÍODOS DE CHUVA"
    return condicao, codigo


def _tendencia_dia(itens, indice):
    mins, maxs, chuvas, codigos = [], [], [], []
    for item in itens:
        if item.get("erro"):
            continue
        dias = item.get("dias") or []
        if len(dias) <= indice:
            continue
        dia = dias[indice]
        mins.append(dia["temp_min"])
        maxs.append(dia["temp_max"])
        chuvas.append(float(dia.get("chuva") or 0))
        codigos.append(dia.get("codigo", 0))

    if not mins:
        return "sem dados"

    tmin, tmax = min(mins), max(maxs)
    if any(c in (95, 96, 99) for c in codigos):
        return f"instável {tmin}-{tmax}°C"
    if sum(chuvas) >= 3:
        return f"chuva {tmin}-{tmax}°C"
    if tmax >= 34:
        return f"calor {tmin}-{tmax}°C"
    return f"sol {tmin}-{tmax}°C"


def montar_dados_regioes(dados_municipios):
    regioes = []
    for cfg in REGIOES_CLIMA:
        itens = [dados_municipios[mid] for mid in cfg["ids"] if mid in dados_municipios]
        validos = [i for i in itens if not i.get("erro")]
        if validos:
            temp_min = min(i["temp_min"] for i in validos)
            temp_max = max(i["temp_max"] for i in validos)
        else:
            temp_min = temp_max = "--"
        condicao, codigo = _condicao_resumida(itens)
        regioes.append(
            {
                **cfg,
                "itens": itens,
                "temp_min": temp_min,
                "temp_max": temp_max,
                "condicao": condicao,
                "codigo": codigo,
                "icone": _icone_clima(codigo),
                "resumo": _resumo_regiao(itens),
                "tendencia_sex": _tendencia_dia(itens, 0),
                "tendencia_sab": _tendencia_dia(itens, 1),
            }
        )
    return regioes


def texto_expectativa_geral(regioes):
    if not regioes:
        return "Previsão indisponível no momento."
    return (
        "Expectativa de sol forte com calor intenso entre 11h e 15h na maior parte do Acre "
        "e entorno. Chuvas isoladas podem ocorrer no fim da tarde em alguns municípios. "
        "Confirme alertas oficiais do INMET e Defesa Civil antes de operações críticas."
    )


def texto_planejamento(regioes):
    validos = []
    for regiao in regioes:
        validos.extend(i for i in regiao["itens"] if not i.get("erro"))
    chuva = any(float(i.get("chuva_dia") or 0) >= 2 for i in validos)
    tempestade = any(i.get("codigo", 0) in (95, 96, 99, 82) for i in validos)
    calor = any(i.get("temp_max", 0) >= 34 for i in validos)

    campo = "Priorizar janelas secas no início da manhã."
    drone = "Operação normal com vento abaixo de 30 km/h."
    pulverizacao = "Evitar horário de maior calor (11h–15h)."
    secagem = "Manter cobertura disponível para grãos."

    if chuva:
        campo = "Priorizar janelas secas cedo; evitar solo encharcado."
        secagem = "Proteger produção — risco de aumento de umidade."
    if tempestade:
        drone = "Suspender voos com trovoada ou rajadas."
        pulverizacao = "Adiar aplicação — risco de lavagem da calda."
    elif calor:
        pulverizacao = "Evitar calor forte e baixa umidade relativa."

    return [
        ("CAMPO", campo),
        ("DRONE", drone),
        ("PULVERIZAÇÃO", pulverizacao),
        ("SECAGEM", secagem),
    ]
