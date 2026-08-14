import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

from core.clima import obter_clima_municipios, obter_data_clima
from core.clima_card import gerar_cards_regiao, url_publica_card, urls_publicas_cards


def normalizar_telefone_whatsapp(telefone):
    digits = re.sub(r"\D", "", telefone or "")
    if not digits:
        return ""
    if digits.startswith("55") and len(digits) in (12, 13):
        return digits
    if len(digits) in (10, 11):
        return f"55{digits}"
    return digits


def formatar_linha_municipio(item):
    if item.get("erro"):
        return f"⚠️ {item['nome']}/{item['uf']}: indisponível"
    return (
        f"{item.get('icone', '🌡️')} *{item['nome']}/{item['uf']}*: "
        f"{item['temperatura']}°C — {item['condicao']}\n"
        f"   Máx {item['temp_max']}°C | Mín {item['temp_min']}°C | "
        f"Umidade {item['umidade']}% | Vento {item['vento']} km/h"
    )


def formatar_mensagem_clima():
    clima = obter_clima_municipios()
    data = obter_data_clima()
    from core.clima_regioes import montar_dados_regioes

    regioes = montar_dados_regioes(clima["por_id"])
    linhas = [
        "🌤️ *Clima RuralPro — Acre e entorno*",
        data["completa"],
        "",
    ]
    for regiao in regioes:
        linhas.append(
            f"*{regiao['titulo']}* ({regiao['cidades']}): "
            f"{regiao['temp_min']}-{regiao['temp_max']}°C — {regiao['condicao'].title()}"
        )
    linhas.extend(["", "Fonte: Open-Meteo | RuralPro Amazônia"])
    return "\n".join(linhas)


def legenda_card_clima():
    data = obter_data_clima()
    clima = obter_clima_municipios()
    from core.clima_regioes import montar_dados_regioes

    regioes = montar_dados_regioes(clima["por_id"])
    linhas = [
        "*Clima RuralPro — Acre e entorno*",
        data["completa"],
        "",
        "Resumo por região:",
    ]
    for regiao in regioes:
        linhas.append(
            f"*{regiao['titulo']}*: {regiao['temp_min']}-{regiao['temp_max']}°C — "
            f"{regiao['condicao'].title()}"
        )
    linhas.extend(
        [
            "",
            "Card completo com planejamento de campo na imagem abaixo.",
            "Fonte: Open-Meteo / INMET",
        ]
    )
    return "\n".join(linhas)


def preparar_disparo_card():
    cards = gerar_cards_regiao()
    legenda = legenda_card_clima()
    urls = urls_publicas_cards()
    mensagem_wa = legenda
    card_paths = [c["path"] for c in cards]
    return cards, card_paths, mensagem_wa, urls, legenda


def link_whatsapp(telefone, mensagem):
    numero = normalizar_telefone_whatsapp(telefone)
    texto = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero}?text={texto}"


def abrir_links_whatsapp(contatos, mensagem, intervalo=5):
    """Abre wa.me só com texto (nao envia cards — uso manual)."""
    urls = []
    for contato in contatos:
        telefone = contato["telefone"] if isinstance(contato, dict) else contato
        urls.append(link_whatsapp(telefone, mensagem))

    for i, url in enumerate(urls):
        webbrowser.open(url, new=2)
        if i < len(urls) - 1 and intervalo > 0:
            time.sleep(intervalo)
    return urls


def enviar_disparo_clima_contato(telefone, cards, legenda):
    """Envia cards + texto direto para o WhatsApp do cliente (API Meta)."""
    for card in cards:
        ok, info = enviar_imagem_whatsapp(
            telefone,
            "",
            f"Clima — {card['regiao']}",
            caminho_local=card["path"],
        )
        if not ok:
            return False, f"{card['regiao']}: {info}"
        time.sleep(1)

    ok, info = enviar_mensagem_whatsapp(telefone, legenda)
    if not ok:
        return False, info
    return True, "enviado"


def disparar_cards_anexados(contatos, legenda, card_paths, intervalo=8):
    """Anexa os cards na conversa via WhatsApp Web (Playwright)."""
    from core.clima_whatsapp_web import disparar_cards_whatsapp_web

    return disparar_cards_whatsapp_web(contatos, legenda, card_paths, intervalo=intervalo)


def whatsapp_api_configurada():
    token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    return bool(token and phone_id)


def enviar_mensagem_whatsapp(telefone, mensagem):
    numero = normalizar_telefone_whatsapp(telefone)
    if not numero:
        return False, "Telefone inválido"

    token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if not token or not phone_id:
        return False, "API do WhatsApp não configurada no .env"

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "text",
        "text": {"preview_url": True, "body": mensagem},
    }
    return _post_whatsapp(token, phone_id, url, payload)


def enviar_imagem_whatsapp(telefone, imagem_url, legenda="", caminho_local=None):
    """Envia card como documento (evita conversao para figurinha)."""
    numero = normalizar_telefone_whatsapp(telefone)
    if not numero:
        return False, "Telefone inválido"

    token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if not token or not phone_id:
        return False, "API do WhatsApp não configurada no .env"

    media_id = None
    filename = "card.jpg"
    if caminho_local:
        filename = Path(caminho_local).name
        ok_upload, resultado = upload_media_whatsapp(caminho_local)
        if not ok_upload:
            return False, resultado
        media_id = resultado

    if not media_id and not imagem_url:
        return False, "URL ou arquivo do card ausente"

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    doc_payload = {"caption": legenda, "filename": filename}
    if media_id:
        doc_payload["id"] = media_id
    else:
        doc_payload["link"] = imagem_url

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "document",
        "document": doc_payload,
    }
    return _post_whatsapp(token, phone_id, url, payload)


def upload_media_whatsapp(caminho_arquivo):
    path = Path(caminho_arquivo)
    if not path.exists():
        return False, f"Arquivo não encontrado: {path}"

    token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if not token or not phone_id:
        return False, "API do WhatsApp não configurada no .env"

    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = "application/octet-stream"

    boundary = f"----FormBoundary{os.urandom(8).hex()}"
    file_data = path.read_bytes()
    parts = [
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="messaging_product"\r\n\r\n'
            f"whatsapp\r\n"
        ).encode(),
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="type"\r\n\r\n'
            f"{mime}\r\n"
        ).encode(),
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode(),
        file_data,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    body = b"".join(parts)

    api_url = f"https://graph.facebook.com/v21.0/{phone_id}/media"
    request = urllib.request.Request(
        api_url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body_json = json.loads(response.read().decode())
            media_id = body_json.get("id")
            if media_id:
                return True, media_id
            return False, "Upload sem ID de mídia"
    except urllib.error.HTTPError as exc:
        try:
            erro = json.loads(exc.read().decode())
            msg = erro.get("error", {}).get("message", str(exc))
        except (json.JSONDecodeError, AttributeError):
            msg = str(exc)
        return False, msg
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, str(exc)


def _post_whatsapp(token, phone_id, url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode())
            if body.get("messages"):
                return True, body["messages"][0].get("id", "enviado")
            return True, "enviado"
    except urllib.error.HTTPError as exc:
        try:
            erro = json.loads(exc.read().decode())
            msg = erro.get("error", {}).get("message", str(exc))
        except (json.JSONDecodeError, AttributeError):
            msg = str(exc)
        return False, msg
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, str(exc)
