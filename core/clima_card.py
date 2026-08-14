import math
import textwrap
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

from core.clima import obter_clima_municipios, obter_data_clima
from core.clima_regioes import (
    montar_dados_regioes,
    texto_expectativa_geral,
    texto_planejamento,
)
from core.models import ConfiguracaoSite

LARGURA = 1080

CORES = {
    "fundo": "#FFFFFF",
    "branco": "#FFFFFF",
    "verde_escuro": "#0F3320",
    "verde": "#1A4D2E",
    "verde_medio": "#2D6A4F",
    "verde_claro": "#D8EAD8",
    "cinza_caixa": "#F7F8F6",
    "borda": "#D5DDD5",
    "texto": "#1F2937",
    "sub": "#5C6670",
    "dourado": "#C9A84C",
    "amarelo": "#E8B923",
    "nuvem": "#B0BEC5",
}


def _fonte(tamanho, negrito=False):
    candidatos = [
        "C:/Windows/Fonts/segoeuib.ttf" if negrito else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if negrito else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if negrito
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for caminho in candidatos:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def _hex(cor):
    cor = cor.lstrip("#")
    return tuple(int(cor[i : i + 2], 16) for i in (0, 2, 4))


def _texto_largura(draw, texto, fonte):
    box = draw.textbbox((0, 0), texto, font=fonte)
    return box[2] - box[0]


def _texto_altura(draw, texto, fonte):
    box = draw.textbbox((0, 0), texto, font=fonte)
    return box[3] - box[1]


def _desenhar_texto_multilinha(draw, xy, texto, fonte, fill, largura_max, espaco=6):
    x, y = xy
    for paragrafo in texto.split("\n"):
        linhas = textwrap.wrap(paragrafo, width=48) if paragrafo else [""]
        for linha in linhas:
            draw.text((x, y), linha, fill=fill, font=fonte)
            y += _texto_altura(draw, linha, fonte) + espaco
    return y


def _carregar_logo(max_altura=72):
    caminho = Path(settings.BASE_DIR) / "static" / "img" / "logo.png"
    if not caminho.exists():
        return None
    logo = Image.open(caminho).convert("RGBA")
    ratio = max_altura / logo.height
    logo = logo.resize((int(logo.width * ratio), max_altura), Image.Resampling.LANCZOS)
    return logo


def _carregar_hero(largura, altura):
    for nome in ("hero-1.png", "hero-3.png", "hero-2.png"):
        caminho = Path(settings.BASE_DIR) / "static" / "img" / nome
        if caminho.exists():
            img = Image.open(caminho).convert("RGB")
            img = img.resize((largura, altura), Image.Resampling.LANCZOS)
            return img
    return Image.new("RGB", (largura, altura), _hex(CORES["verde_medio"]))


def _desenhar_sol(draw, cx, cy, raio=14):
    draw.ellipse((cx - raio, cy - raio, cx + raio, cy + raio), fill=_hex(CORES["amarelo"]))
    for angulo in range(0, 360, 45):
        rad = math.radians(angulo)
        x1 = cx + math.cos(rad) * (raio + 3)
        y1 = cy + math.sin(rad) * (raio + 3)
        x2 = cx + math.cos(rad) * (raio + 8)
        y2 = cy + math.sin(rad) * (raio + 8)
        draw.line((x1, y1, x2, y2), fill=_hex(CORES["amarelo"]), width=2)


def _desenhar_nuvem(draw, x, y, largura=30, altura=16):
    draw.ellipse((x, y + altura // 3, x + largura * 0.45, y + altura), fill=_hex(CORES["nuvem"]))
    draw.ellipse(
        (x + largura * 0.25, y, x + largura * 0.75, y + altura * 0.85),
        fill=_hex(CORES["nuvem"]),
    )
    draw.ellipse(
        (x + largura * 0.5, y + altura // 4, x + largura, y + altura),
        fill=_hex(CORES["nuvem"]),
    )


def _desenhar_icone_clima(draw, x, y, codigo):
    cx, cy = x + 22, y + 24
    if codigo in (0,):
        _desenhar_sol(draw, cx, cy)
    elif codigo in (1, 2):
        _desenhar_sol(draw, cx - 5, cy - 3, raio=11)
        _desenhar_nuvem(draw, x + 10, y + 14, largura=38, altura=18)
    elif codigo in (3, 45, 48):
        _desenhar_nuvem(draw, x + 4, y + 10, largura=42, altura=22)
    elif codigo in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        _desenhar_nuvem(draw, x + 4, y + 8, largura=42, altura=20)
        draw.line((x + 14, y + 34, x + 14, y + 42), fill=_hex(CORES["verde"]), width=2)
        draw.line((x + 26, y + 34, x + 26, y + 44), fill=_hex(CORES["verde"]), width=2)
    elif codigo in (95, 96, 99):
        _desenhar_nuvem(draw, x + 4, y + 8, largura=42, altura=20)
        draw.line((x + 22, y + 32, x + 16, y + 44), fill=_hex(CORES["dourado"]), width=2)
        draw.line((x + 28, y + 32, x + 28, y + 46), fill=_hex(CORES["dourado"]), width=2)
    else:
        _desenhar_sol(draw, cx, cy)


def _contato_site():
    config = ConfiguracaoSite.load()
    endereco = config.endereco or "Edifício Via Towers, 6º Andar, Sala 606"
    cidade = f"{config.cidade}/{config.estado}" if config.cidade else "Rio Branco/AC"
    return {
        "telefone": config.telefone or "(68) 99901-2015",
        "email": config.email or "escritorioruraldrz@gmail.com",
        "endereco": f"{endereco} - {cidade}",
    }


def _calcular_altura(regioes):
    return (
        250
        + 56
        + len(regioes) * 148
        + 240
        + 170
        + 90
        + 110
        + 40
    )


def _regioes_com_dados(regioes):
    return any(
        not item.get("erro")
        for regiao in regioes
        for item in regiao.get("itens", [])
    )


def obter_ou_gerar_card_regional(destino_dir=None):
    data = obter_data_clima()
    pasta = Path(destino_dir) if destino_dir else _pasta_clima()
    caminho = pasta / f"card_regional_{data['iso']}.jpg"

    clima = obter_clima_municipios()
    regioes = montar_dados_regioes(clima["por_id"])
    if caminho.exists() and _regioes_com_dados(regioes):
        return caminho

    if not _regioes_com_dados(regioes):
        clima = obter_clima_municipios(forcar=True)
        regioes = montar_dados_regioes(clima["por_id"])

    if caminho.exists():
        caminho.unlink(missing_ok=True)

    return gerar_card_regional(pasta, clima=clima, regioes=regioes)


def _desenhar_cabecalho(base, draw, data):
    margem = 36
    logo = _carregar_logo(68)
    if logo:
        base.paste(logo, (margem, 28), logo)

    draw.text(
        (margem, 108),
        "CLIMA POR REGIÕES DO ACRE E ENTORNO",
        fill=_hex(CORES["verde_escuro"]),
        font=_fonte(34, negrito=True),
    )
    draw.text(
        (margem, 152),
        "INFORMAÇÃO PARA PLANEJAR O DIA NO CAMPO",
        fill=_hex(CORES["verde_medio"]),
        font=_fonte(18, negrito=True),
    )

    hero_largura, hero_altura = 250, 150
    hero = _carregar_hero(hero_largura, hero_altura)
    base.paste(hero, (LARGURA - margem - hero_largura, 24))

    y_barra = 210
    draw.rectangle((0, y_barra, LARGURA, y_barra + 56), fill=_hex(CORES["verde_escuro"]))
    draw.text(
        (margem, y_barra + 14),
        data["completa"].upper(),
        fill=_hex(CORES["branco"]),
        font=_fonte(20, negrito=True),
    )
    hora = data.get("hora_consulta", "6h")
    consulta = f"CONSULTA: {hora}"
    fonte_cons = _fonte(18, negrito=True)
    draw.text(
        (LARGURA - margem - _texto_largura(draw, consulta, fonte_cons), y_barra + 16),
        consulta,
        fill=_hex(CORES["dourado"]),
        font=fonte_cons,
    )
    return y_barra + 56


def _desenhar_regiao(draw, y, regiao):
    margem = 36
    altura = 136
    draw.rounded_rectangle(
        (margem, y, LARGURA - margem, y + altura),
        radius=12,
        fill=_hex(CORES["branco"]),
        outline=_hex(CORES["borda"]),
        width=1,
    )

    tag = regiao["titulo"]
    fonte_tag = _fonte(13, negrito=True)
    tag_largura = _texto_largura(draw, tag, fonte_tag) + 22
    draw.rounded_rectangle(
        (margem + 14, y + 12, margem + 14 + tag_largura, y + 38),
        radius=8,
        fill=_hex(CORES["verde_escuro"]),
    )
    draw.text(
        (margem + 24, y + 16),
        tag,
        fill=_hex(CORES["branco"]),
        font=fonte_tag,
    )
    draw.text(
        (margem + 22 + tag_largura, y + 16),
        regiao["cidades"],
        fill=_hex(CORES["texto"]),
        font=_fonte(14),
    )

    panel_x = margem + 14
    panel_y = y + 48
    panel_w = 168
    panel_h = 76
    draw.rounded_rectangle(
        (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h),
        radius=10,
        fill=_hex(CORES["verde_escuro"]),
    )
    _desenhar_icone_clima(draw, panel_x + 8, panel_y + 8, regiao.get("codigo", 0))
    temp_txt = f"{regiao['temp_min']}°-{regiao['temp_max']}°C"
    draw.text(
        (panel_x + 58, panel_y + 10),
        temp_txt,
        fill=_hex(CORES["branco"]),
        font=_fonte(22, negrito=True),
    )
    draw.text(
        (panel_x + 58, panel_y + 38),
        "MIN. / MÁX.",
        fill=_hex(CORES["verde_claro"]),
        font=_fonte(10),
    )
    condicao = regiao["condicao"][:24]
    draw.text(
        (panel_x + 10, panel_y + 56),
        condicao,
        fill=_hex(CORES["dourado"]),
        font=_fonte(11, negrito=True),
    )

    resumo_x = panel_x + panel_w + 18
    draw.text(
        (resumo_x, panel_y + 2),
        "RESUMO DA REGIÃO",
        fill=_hex(CORES["verde_escuro"]),
        font=_fonte(13, negrito=True),
    )
    fonte_resumo = _fonte(13)
    linhas = textwrap.wrap(regiao["resumo"], width=52)
    ry = panel_y + 24
    for linha in linhas[:3]:
        draw.text((resumo_x, ry), linha, fill=_hex(CORES["texto"]), font=fonte_resumo)
        ry += 18
    return y + altura + 12


def _desenhar_overview(draw, y, regioes):
    margem = 36
    altura = 220
    draw.rounded_rectangle(
        (margem, y, LARGURA - margem, y + altura),
        radius=14,
        fill=_hex(CORES["branco"]),
        outline=_hex(CORES["verde_claro"]),
        width=2,
    )
    meio = LARGURA // 2
    draw.line((meio, y + 16, meio, y + altura - 16), fill=_hex(CORES["verde_claro"]), width=2)

    draw.text(
        (margem + 20, y + 18),
        "O QUE ESPERAR NO ACRE E ENTORNO HOJE?",
        fill=_hex(CORES["verde_escuro"]),
        font=_fonte(16, negrito=True),
    )
    _desenhar_texto_multilinha(
        draw,
        (margem + 20, y + 48),
        texto_expectativa_geral(regioes),
        _fonte(14),
        _hex(CORES["texto"]),
        420,
    )

    draw.text(
        (meio + 20, y + 18),
        "PLANEJAMENTO DO CAMPO",
        fill=_hex(CORES["verde_escuro"]),
        font=_fonte(16, negrito=True),
    )
    py = y + 52
    for titulo, texto in texto_planejamento(regioes):
        draw.ellipse((meio + 20, py + 2, meio + 34, py + 16), fill=_hex(CORES["verde_medio"]))
        draw.text(
            (meio + 42, py),
            f"{titulo}: {texto}",
            fill=_hex(CORES["texto"]),
            font=_fonte(13),
        )
        py += 38
    return y + altura + 18


def _desenhar_tendencia(draw, y, regioes):
    margem = 36
    draw.text(
        (margem, y),
        "TENDÊNCIA RESUMIDA — SEXTA E SÁBADO",
        fill=_hex(CORES["verde_escuro"]),
        font=_fonte(18, negrito=True),
    )
    y += 34
    col_largura = (LARGURA - margem * 2 - 4 * 12) // 5
    for i, regiao in enumerate(regioes):
        x = margem + i * (col_largura + 12)
        draw.rounded_rectangle(
            (x, y, x + col_largura, y + 110),
            radius=10,
            fill=_hex(CORES["cinza_caixa"]),
            outline=_hex(CORES["verde_claro"]),
            width=1,
        )
        draw.text(
            (x + 10, y + 10),
            regiao["titulo"],
            fill=_hex(CORES["verde_escuro"]),
            font=_fonte(12, negrito=True),
        )
        draw.text(
            (x + 10, y + 34),
            f"SEX: {regiao['tendencia_sex']}",
            fill=_hex(CORES["texto"]),
            font=_fonte(11),
        )
        draw.text(
            (x + 10, y + 58),
            f"SÁB: {regiao['tendencia_sab']}",
            fill=_hex(CORES["texto"]),
            font=_fonte(11),
        )
    return y + 130


def _desenhar_alertas(draw, y, data):
    margem = 36
    draw.rounded_rectangle(
        (margem, y, LARGURA - margem, y + 56),
        radius=10,
        fill=_hex(CORES["verde_escuro"]),
    )
    draw.text(
        (margem + 18, y + 16),
        "ALERTAS OFICIAIS: nenhum aviso específico confirmado para os municípios na consulta.",
        fill=_hex(CORES["branco"]),
        font=_fonte(13, negrito=True),
    )
    y += 66
    fonte = _fonte(11)
    fontes_txt = (
        f"FONTES: INMET, CPTEC/INPE e Defesa Civil. Dados Open-Meteo. "
        f"Atualização {data['curta']}, {data.get('hora_consulta', '6h')}."
    )
    draw.text((margem, y), fontes_txt, fill=_hex(CORES["sub"]), font=fonte)
    return y + 28


def _desenhar_rodape(base, draw, y):
    contato = _contato_site()
    altura = 88
    draw.rectangle((0, y, LARGURA, y + altura), fill=_hex(CORES["verde_escuro"]))
    logo = _carregar_logo(44)
    if logo:
        base.paste(logo, (32, y + 18), logo)

    fonte_tel = _fonte(15, negrito=True)
    fonte_email = _fonte(13)
    fonte_end = _fonte(11)

    tel = contato["telefone"]
    draw.text((250, y + 22), tel, fill=_hex(CORES["branco"]), font=fonte_tel)

    email = contato["email"]
    draw.text((250, y + 46), email, fill=_hex(CORES["dourado"]), font=fonte_email)

    endereco = contato["endereco"]
    end_largura = _texto_largura(draw, endereco, fonte_end)
    draw.text(
        (LARGURA - 36 - end_largura, y + 34),
        endereco,
        fill=_hex(CORES["branco"]),
        font=fonte_end,
    )


def gerar_card_regional(destino_dir=None, clima=None, regioes=None):
    if clima is None:
        clima = obter_clima_municipios()
    data = obter_data_clima()
    from django.utils import timezone

    agora = timezone.localtime(timezone.now())
    data["hora_consulta"] = agora.strftime("%Hh").lstrip("0") or "6h"

    if regioes is None:
        regioes = montar_dados_regioes(clima["por_id"])
    altura = _calcular_altura(regioes)
    img = Image.new("RGB", (LARGURA, altura), _hex(CORES["fundo"]))
    draw = ImageDraw.Draw(img)

    y = _desenhar_cabecalho(img, draw, data)
    for regiao in regioes:
        y = _desenhar_regiao(draw, y + 16, regiao)
    y = _desenhar_overview(draw, y + 8, regioes)
    y = _desenhar_tendencia(draw, y, regioes)
    y = _desenhar_alertas(draw, y, data)
    _desenhar_rodape(img, draw, y + 8)

    pasta = Path(destino_dir) if destino_dir else _pasta_clima()
    caminho = pasta / f"card_regional_{data['iso']}.jpg"
    img.save(caminho, "JPEG", quality=95, subsampling=0, optimize=True)
    return caminho


def _pasta_clima():
    pasta = Path(settings.MEDIA_ROOT) / "clima"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def gerar_cards_regiao(destino_dir=None):
    caminho = gerar_card_regional(destino_dir)
    return [
        {
            "regiao": "Acre e entorno",
            "slug": "regional",
            "path": caminho,
        }
    ]


def gerar_card_clima(destino=None):
    return gerar_card_regional(destino)


def url_publica_card(slug=None):
    data = obter_data_clima()
    base = getattr(settings, "SITE_BASE_URL", "").strip().rstrip("/")
    if not base:
        return ""
    if slug in (None, "regional", "completo"):
        return f"{base}{settings.MEDIA_URL}clima/card_regional_{data['iso']}.jpg"
    return f"{base}{settings.MEDIA_URL}clima/card_{slug}_{data['iso']}.jpg"


def urls_publicas_cards():
    return {
        "regional": url_publica_card("regional"),
        "completo": url_publica_card("regional"),
    }
