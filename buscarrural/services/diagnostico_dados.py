import re
from io import BytesIO
from pathlib import Path

from django.utils import timezone


def _normalizar(texto):
    return re.sub(r"\s+", " ", (texto or "").strip().lower())


def _buscar_valor(dados, *termos):
    termos_norm = [_normalizar(t) for t in termos]
    for _, rotulo, valor in _iterar_itens(dados):
        rotulo_norm = _normalizar(rotulo)
        if any(t in rotulo_norm for t in termos_norm):
            return (valor or "").strip()
    return ""


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


def _formatar_area(valor):
    if not valor:
        return "—"
    match = re.search(r"([\d.,]+)\s*ha", valor, re.IGNORECASE)
    if match:
        num = match.group(1).replace(".", "").replace(",", ".")
        try:
            return f"{float(num):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " ha"
        except ValueError:
            return match.group(0)
    match = re.search(r"[\d.,]+", valor)
    if match:
        return f"{match.group(0)} ha"
    return valor[:20]


def _status_card(valor, ok_termos, alerta_termos):
    norm = _normalizar(valor)
    if not norm or norm in ("—", "-", "nao informado", "não informado"):
        return "—", "Sem informação", "alerta"
    for termo in alerta_termos:
        if termo in norm:
            return valor.upper()[:24], "Verificar situação", "alerta"
    for termo in ok_termos:
        if termo in norm:
            return valor.upper()[:24], "Conforme consulta", "ok"
    return valor.upper()[:24], "Conforme consulta", "ok"


def _extrair_coordenadas(dados):
    geo = _buscar_valor(dados, "geolocal", "latitude", "coordenada", "centróide", "centroide")
    if not geo:
        for _, rotulo, valor in _iterar_itens(dados):
            if "latitude" in _normalizar(rotulo) or "geolocal" in _normalizar(rotulo):
                geo = valor
                break
    if not geo:
        return None, None
    match = re.search(
        r"Latitude:\s*([-\d.]+)\s*.*Longitude:\s*([-\d.]+)",
        geo,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1), match.group(2)
    nums = re.findall(r"-?\d+\.\d+", geo)
    if len(nums) >= 2:
        return nums[0], nums[1]
    return None, None


def gerar_mapa_estatico_coordenadas(dados, destino):
    lat, lon = _extrair_coordenadas(dados)
    if not lat or not lon:
        return None

    try:
        return _gerar_mapa_tiles_osm(float(lat), float(lon), destino)
    except Exception:
        return None


def _gerar_mapa_tiles_osm(lat, lon, destino, zoom=13):
    import math

    import requests
    from PIL import Image, ImageDraw

    def latlon_para_tile(lat_deg, lon_deg, z):
        lat_rad = math.radians(lat_deg)
        n = 2**z
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y

    tile_size = 256
    grid = 3
    x_center, y_center = latlon_para_tile(lat, lon, zoom)
    canvas = Image.new("RGB", (tile_size * grid, tile_size * grid), "#dbe7db")
    headers = {"User-Agent": "RuralProAmazonia/1.0 (mapa-car; +https://ruralproamazonia.com.br)"}

    baixados = 0
    for dx in range(grid):
        for dy in range(grid):
            url = f"https://tile.openstreetmap.org/{zoom}/{x_center + dx - 1}/{y_center + dy - 1}.png"
            try:
                response = requests.get(url, timeout=15, headers=headers)
                if response.status_code == 200:
                    tile = Image.open(BytesIO(response.content)).convert("RGB")
                    canvas.paste(tile, (dx * tile_size, dy * tile_size))
                    baixados += 1
            except Exception:
                continue

    if baixados < 4:
        return None

    n = 2**zoom
    x_float = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y_float = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    px = int((x_float - (x_center - 1)) * tile_size)
    py = int((y_float - (y_center - 1)) * tile_size)

    draw = ImageDraw.Draw(canvas)
    raio = 10
    draw.ellipse(
        (px - raio, py - raio, px + raio, py + raio),
        fill="#114b32",
        outline="#ffffff",
        width=3,
    )

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destino, "PNG", optimize=True)
    return destino if destino.stat().st_size > 3000 else None


def extrair_indicadores_car(dados, numero_car, atualizado_em_site=""):
    area_bruta = _buscar_valor(
        dados,
        "area total",
        "área total",
        "area do imovel",
        "área do imóvel",
        "area declarada",
    )
    modulos = _buscar_valor(dados, "modulo fiscal", "módulo fiscal", "modulos fiscais")
    situacao = _buscar_valor(dados, "situacao do car", "situação do car", "situacao cadastral", "status")
    analise = _buscar_valor(
        dados,
        "analise",
        "análise",
        "validacao",
        "validação",
        "analise oficial",
    )
    protocolo = _buscar_valor(
        dados,
        "protocolo",
        "pecuaria",
        "pecuária",
        "mpf",
        "monitoramento de gado",
    )

    area_fmt = _formatar_area(area_bruta)
    modulos_fmt = modulos or "—"
    if modulos_fmt != "—" and "modulo" not in _normalizar(modulos_fmt):
        modulos_fmt = f"{modulos_fmt} módulos fiscais"

    sit_valor, sit_sub, sit_tipo = _status_card(
        situacao or "ATIVO",
        ("ativo", "regular", "conforme", "apto", "validado"),
        ("inativo", "cancelado", "suspenso", "inapto", "irregular"),
    )
    ana_valor, ana_sub, ana_tipo = _status_card(
        analise or "PENDENTE",
        ("analisado", "validado", "aprovado", "concluido", "concluído"),
        ("pendente", "aguardando", "analise", "análise", "nao analisado"),
    )
    pro_valor, pro_sub, pro_tipo = _status_card(
        protocolo or "APTO",
        ("apto", "regular", "conforme", "sem pendencia"),
        ("inapto", "irregular", "pendente", "nao apto"),
    )

    agora = timezone.localtime(timezone.now())
    emissao = agora.strftime("%d/%m/%Y")
    base_data = atualizado_em_site or emissao

    match_area_num = re.search(r"([\d.,]+)", area_fmt)
    area_num = match_area_num.group(1) if match_area_num else "—"

    return {
        "numero_car": numero_car,
        "area_formatada": area_fmt,
        "area_numero": area_num,
        "modulos_fiscais": modulos_fmt,
        "emissao": emissao,
        "base_analisada": (
            f"consulta SeloVerde AC emitida e atualizada em {base_data}"
        ),
        "cards": [
            {
                "valor": area_num if area_num != "—" else area_fmt.replace(" ha", ""),
                "unidade": "ha" if area_num != "—" else "",
                "titulo": "Área declarada",
                "subtitulo": modulos_fmt if modulos_fmt != "—" else "Área do imóvel",
                "tipo": "ok",
            },
            {
                "valor": sit_valor,
                "unidade": "",
                "titulo": "Situação do CAR",
                "subtitulo": sit_sub if sit_sub != "Conforme consulta" else "Cadastro vigente",
                "tipo": sit_tipo,
            },
            {
                "valor": ana_valor,
                "unidade": "",
                "titulo": "Análise oficial",
                "subtitulo": ana_sub if ana_tipo == "alerta" else "Aguardando análise"
                if "pend" in _normalizar(ana_valor)
                else ana_sub,
                "tipo": ana_tipo,
            },
            {
                "valor": pro_valor,
                "unidade": "",
                "titulo": "Protocolo da pecuária",
                "subtitulo": "Critérios MPF",
                "tipo": pro_tipo,
            },
        ],
    }
