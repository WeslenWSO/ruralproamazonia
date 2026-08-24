from pathlib import Path

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from buscarrural.services.diagnostico_dados import extrair_indicadores_car
from core.models import ConfiguracaoSite

VERDE_ESCURO = colors.HexColor("#114b32")
VERDE_MEDIO = colors.HexColor("#2d8a56")
FUNDO = colors.HexColor("#FAFAF8")
BORDA = colors.HexColor("#D5DDD5")
ALERTA = colors.HexColor("#C47A2A")
LEITURA_FUNDO = colors.HexColor("#FFF8E7")
TEXTO = colors.HexColor("#1F2937")
SUBTEXTO = colors.HexColor("#5C6670")

LARGURA_UTIL = 170 * mm
MARGEM = 20 * mm


def _logo_path():
    config = ConfiguracaoSite.load()
    if config.logo:
        try:
            return Path(config.logo.path)
        except (ValueError, OSError):
            pass
    caminho = Path(settings.BASE_DIR) / "static" / "img" / "logo.png"
    return caminho if caminho.exists() else None


def _contato():
    config = ConfiguracaoSite.load()
    endereco = config.endereco or "RODOVIA BR-364 VIA VERDE, Nº 3600- VIA TOWER CORPORATE - 6º ANDAR - SALA 606B"
    cidade = f"{config.cidade}/{config.estado}" if config.cidade else "Rio Branco/AC"
    return {
        "telefone": config.telefone or "(68) 9.9901-2015",
        "email": config.email or "escritorioruraldrz@gmail.com",
        "endereco": f"{endereco} - {cidade}",
    }


def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo_doc": ParagraphStyle(
            "titulo_doc",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.white,
            leading=22,
        ),
        "subtitulo_doc": ParagraphStyle(
            "subtitulo_doc",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.white,
            leading=12,
        ),
        "header_dir": ParagraphStyle(
            "header_dir",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=VERDE_ESCURO,
            alignment=TA_LEFT,
        ),
        "header_data": ParagraphStyle(
            "header_data",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=SUBTEXTO,
        ),
        "secao_titulo": ParagraphStyle(
            "secao_titulo",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=VERDE_ESCURO,
            leading=14,
        ),
        "corpo": ParagraphStyle(
            "corpo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=TEXTO,
            leading=14,
        ),
        "card_valor": ParagraphStyle(
            "card_valor",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=VERDE_MEDIO,
            leading=18,
        ),
        "card_valor_alerta": ParagraphStyle(
            "card_valor_alerta",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=ALERTA,
            leading=18,
        ),
        "card_titulo": ParagraphStyle(
            "card_titulo",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=TEXTO,
            leading=10,
        ),
        "card_sub": ParagraphStyle(
            "card_sub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            textColor=SUBTEXTO,
            leading=10,
        ),
        "leitura_label": ParagraphStyle(
            "leitura_label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=VERDE_ESCURO,
        ),
        "leitura_texto": ParagraphStyle(
            "leitura_texto",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=VERDE_ESCURO,
            leading=13,
        ),
        "rodape": ParagraphStyle(
            "rodape",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.white,
            leading=11,
        ),
    }


def _rodape_canvas(canvas, doc):
    contato = _contato()
    canvas.saveState()
    canvas.setFillColor(VERDE_ESCURO)
    canvas.rect(0, 0, A4[0], 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    linha1 = (
        f"Para mais informações agende uma conversa com nossos especialistas {contato['telefone']}"
    )
    linha2 = f"{contato['email']}  |  {contato['endereco']}"
    canvas.drawString(MARGEM, 10 * mm, linha1)
    canvas.drawString(MARGEM, 6 * mm, linha2)
    canvas.restoreState()


def _cabecalho_pagina(indicadores, estilos):
    elementos = []
    logo = _logo_path()
    col_esq = []
    if logo:
        col_esq.append(Image(str(logo), width=42 * mm, height=12 * mm))
    else:
        col_esq.append(Paragraph("<b>RuralPro</b>", estilos["header_dir"]))
    col_esq.append(
        Paragraph(
            "SOLUÇÕES FUNDIÁRIAS E AMBIENTAIS — TUDO EM UM SÓ LUGAR —",
            estilos["card_sub"],
        )
    )
    col_dir = [
        Paragraph("DIAGNÓSTICO TÉCNICO | CAR", estilos["header_dir"]),
        Paragraph(f"Emissão: {indicadores['emissao']}", estilos["header_data"]),
    ]
    tabela_header = Table(
        [[col_esq, col_dir]],
        colWidths=[LARGURA_UTIL * 0.62, LARGURA_UTIL * 0.38],
    )
    tabela_header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elementos.append(tabela_header)
    elementos.append(Spacer(1, 4 * mm))
    return elementos


def _faixa_titulo(indicadores, estilos):
    area = indicadores.get("area_numero", "—")
    subtitulos = [
        Paragraph("DIAGNÓSTICO TÉCNICO PRELIMINAR", estilos["titulo_doc"]),
        Paragraph("Cadastro Ambiental Rural - CAR", estilos["subtitulo_doc"]),
        Paragraph(
            f"Imóvel de {area} ha | Código {indicadores['numero_car']}",
            estilos["subtitulo_doc"],
        ),
        Paragraph(
            f"Base analisada: {indicadores['base_analisada']}",
            estilos["subtitulo_doc"],
        ),
    ]
    tabela = Table([[subtitulos]], colWidths=[LARGURA_UTIL])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), VERDE_ESCURO),
                ("BOX", (0, 0), (-1, -1), 0, VERDE_ESCURO),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return tabela


def _cards_kpi(cards, estilos):
    colunas = []
    for card in cards:
        valor = card.get("valor", "—")
        unidade = card.get("unidade", "")
        valor_txt = f"{valor} {unidade}".strip()
        estilo_valor = (
            estilos["card_valor_alerta"]
            if card.get("tipo") == "alerta"
            else estilos["card_valor"]
        )
        faixa_cor = ALERTA if card.get("tipo") == "alerta" else VERDE_MEDIO
        celula = [
            Paragraph(valor_txt, estilo_valor),
            Paragraph(card.get("titulo", ""), estilos["card_titulo"]),
            Paragraph(card.get("subtitulo", ""), estilos["card_sub"]),
        ]
        t = Table([[celula]], colWidths=[LARGURA_UTIL / 4 - 2 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
                    ("LINEBELOW", (0, 0), (-1, 0), 3, faixa_cor),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        colunas.append(t)

    tabela = Table([colunas], colWidths=[LARGURA_UTIL / 4] * 4, hAlign="LEFT")
    tabela.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return tabela


def _secao_bloco(secao, estilos, primeira=False):
    elementos = []
    if not primeira:
        elementos.append(PageBreak())

    numero = secao.get("numero", 1)
    titulo = secao.get("titulo", "")
    badge = Table(
        [[Paragraph(f"<font color='white'>{numero}</font>", estilos["card_titulo"])]],
        colWidths=[8 * mm],
        rowHeights=[8 * mm],
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), VERDE_ESCURO),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    titulo_row = Table(
        [[badge, Paragraph(titulo, estilos["secao_titulo"])]],
        colWidths=[10 * mm, LARGURA_UTIL - 10 * mm],
    )
    titulo_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elementos.append(titulo_row)
    elementos.append(Spacer(1, 3 * mm))

    texto = (secao.get("texto") or "").replace("\n", "<br/>")
    caixa = Table([[Paragraph(texto, estilos["corpo"])]], colWidths=[LARGURA_UTIL])
    caixa.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elementos.append(caixa)
    elementos.append(Spacer(1, 4 * mm))

    leitura = (secao.get("leitura_direta") or "").strip()
    if leitura:
        leitura_tbl = Table(
            [
                [
                    Paragraph("LEITURA<br/>DIRETA", estilos["leitura_label"]),
                    Paragraph(leitura.replace("\n", "<br/>"), estilos["leitura_texto"]),
                ]
            ],
            colWidths=[22 * mm, LARGURA_UTIL - 22 * mm],
        )
        leitura_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), LEITURA_FUNDO),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elementos.append(leitura_tbl)

    return elementos


def _pagina_mapa(caminho_imagem, estilos):
    elementos = [PageBreak()]
    elementos.append(Paragraph("MAPA DO IMÓVEL", estilos["secao_titulo"]))
    elementos.append(Spacer(1, 3 * mm))
    if caminho_imagem and Path(caminho_imagem).exists():
        img = Image(str(caminho_imagem))
        max_largura = LARGURA_UTIL
        max_altura = 220 * mm
        ratio = min(max_largura / img.imageWidth, max_altura / img.imageHeight)
        img.drawWidth = img.imageWidth * ratio
        img.drawHeight = img.imageHeight * ratio
        elementos.append(img)
    else:
        elementos.append(
            Paragraph(
                "Mapa não disponível nesta consulta.",
                estilos["corpo"],
            )
        )
    return elementos


def gerar_pdf_diagnostico(consulta, destino=None):
    estilos = _estilos()
    indicadores = extrair_indicadores_car(
        consulta.dados or {},
        consulta.numero_car,
        consulta.atualizado_em_site,
    )
    diagnostico = consulta.parecer_diagnostico or {}
    secoes = diagnostico.get("secoes") or []

    if destino:
        caminho = Path(destino)
        caminho.parent.mkdir(parents=True, exist_ok=True)
    else:
        pasta = Path(settings.MEDIA_ROOT) / "buscarrural" / "tmp"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / f"diagnostico_{consulta.pk}.pdf"

    doc = SimpleDocTemplate(
        str(caminho),
        pagesize=A4,
        leftMargin=MARGEM,
        rightMargin=MARGEM,
        topMargin=MARGEM,
        bottomMargin=24 * mm,
    )

    story = []
    story.extend(_cabecalho_pagina(indicadores, estilos))
    story.append(_faixa_titulo(indicadores, estilos))
    story.append(Spacer(1, 4 * mm))
    story.append(_cards_kpi(indicadores["cards"], estilos))
    story.append(Spacer(1, 6 * mm))

    for idx, secao in enumerate(secoes):
        story.extend(_secao_bloco(secao, estilos, primeira=(idx == 0)))

    caminho_mapa = None
    if consulta.imagem_terreno:
        try:
            caminho_mapa = consulta.imagem_terreno.path
        except (ValueError, OSError):
            caminho_mapa = None
    story.extend(_pagina_mapa(caminho_mapa, estilos))

    doc.build(story, onFirstPage=_rodape_canvas, onLaterPages=_rodape_canvas)
    return caminho
