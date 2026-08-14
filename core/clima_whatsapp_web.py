import subprocess
import sys
import time
from pathlib import Path

from django.conf import settings

from core.clima_whatsapp import normalizar_telefone_whatsapp


def _playwright_disponivel():
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def _pasta_sessao():
    pasta = Path(settings.BASE_DIR) / ".wa_browser"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _garantir_pagina(context, page):
    if page is None or page.is_closed():
        return context.new_page()
    return page


def _aguardar_whatsapp_logado(page, timeout_seg=180):
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector(
        '[data-testid="chat-list"], #pane-side, canvas, [data-testid="qrcode"]',
        timeout=timeout_seg * 1000,
    )
    if page.locator('[data-testid="chat-list"], #pane-side').count() == 0:
        page.wait_for_selector('[data-testid="chat-list"], #pane-side', timeout=timeout_seg * 1000)


def _aguardar_conversa(page, timeout_seg=45):
    page.wait_for_selector(
        'footer div[contenteditable="true"], [data-testid="conversation-compose-box-input"]',
        timeout=timeout_seg * 1000,
    )
    page.wait_for_timeout(1200)


def _compose(page):
    return page.locator('[data-testid="conversation-compose-box-input"]').first


def _clicar_enviar_mensagem(page):
    page.wait_for_timeout(500)
    for seletor in (
        '[data-testid="media-preview-send"]',
        '[data-testid="compose-btn-send"]',
        'footer button[aria-label="Enviar"]',
        'footer span[data-icon="send"]',
    ):
        botao = page.locator(seletor).last
        if botao.count():
            try:
                if botao.is_visible():
                    botao.click(timeout=8000)
                    return
            except Exception:
                continue
    _compose(page).click()
    page.keyboard.press("Enter")


def _copiar_imagem_clipboard(caminho):
    caminho = str(Path(caminho).resolve())
    if sys.platform == "win32":
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "Add-Type -AssemblyName System.Drawing; "
            f"$img = [System.Drawing.Image]::FromFile('{caminho.replace(chr(39), chr(39)+chr(39))}'); "
            "[System.Windows.Forms.Clipboard]::SetImage($img); "
            "$img.Dispose()"
        )
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if resultado.returncode != 0:
            raise RuntimeError(resultado.stderr.strip() or "Falha ao copiar imagem")
        return

    from PIL import Image
    import io

    try:
        import win32clipboard  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Clipboard indisponivel neste sistema.") from exc

    img = Image.open(caminho).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "BMP")
    data = buf.getvalue()[14:]
    buf.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def _enviar_imagem_colando(page, caminho):
    _copiar_imagem_clipboard(caminho)
    compose = _compose(page)
    compose.click()
    page.wait_for_timeout(400)
    page.keyboard.press("Control+V")
    page.wait_for_timeout(3500)
    page.wait_for_selector(
        '[data-testid="media-editor"], [data-testid="media-preview-send"], '
        '[data-testid="media-viewer-root"], span[data-icon="send"]',
        timeout=20000,
    )
    _clicar_enviar_mensagem(page)
    page.wait_for_timeout(2500)


def _clicar_anexar(page):
    for seletor in (
        '[data-testid="conversation-attach"]',
        'button[aria-label="Anexar"]',
        'div[title="Anexar"]',
        'footer span[data-icon="plus"]',
        'footer span[data-icon="attach-menu-plus"]',
    ):
        botao = page.locator(seletor).first
        if botao.count():
            try:
                botao.click(timeout=8000)
                page.wait_for_timeout(800)
                return
            except Exception:
                continue
    raise RuntimeError("Botao anexar nao encontrado.")


def _enviar_via_input_documento(page, caminho):
    caminho = str(Path(caminho).resolve())
    _clicar_anexar(page)
    with page.expect_file_chooser(timeout=15000) as fc_info:
        for seletor in ('[data-testid="mi-attach-document"]', '[aria-label="Documento"]'):
            item = page.locator(seletor).first
            if item.count():
                item.click(timeout=5000)
                break
        else:
            page.get_by_text("Documento", exact=False).first.click(timeout=5000)
    fc_info.value.set_files(caminho)
    page.wait_for_timeout(3000)
    _clicar_enviar_mensagem(page)
    page.wait_for_timeout(2500)


def _enviar_arquivo(page, caminho):
    _aguardar_conversa(page)
    erros = []

    try:
        _enviar_imagem_colando(page, caminho)
        return "colado"
    except Exception as exc:
        erros.append(f"colar: {exc}")

    try:
        _enviar_via_input_documento(page, caminho)
        return "documento"
    except Exception as exc:
        erros.append(f"documento: {exc}")

    for entrada in page.locator('input[type="file"]').all():
        try:
            entrada.set_input_files(str(Path(caminho).resolve()))
            page.wait_for_timeout(3000)
            _clicar_enviar_mensagem(page)
            page.wait_for_timeout(2500)
            return "input"
        except Exception:
            continue

    raise RuntimeError(" | ".join(erros))


def _enviar_texto(page, texto):
    if not texto:
        return
    compose = _compose(page)
    compose.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.insert_text(texto)
    page.wait_for_timeout(600)
    _clicar_enviar_mensagem(page)
    page.wait_for_timeout(2000)


def _anexar_cards_na_conversa(page, card_paths, legenda):
    detalhes = []

    for caminho in card_paths:
        try:
            modo = _enviar_arquivo(page, caminho)
            detalhes.append(f"{Path(caminho).name}: ok ({modo})")
        except Exception as exc:
            detalhes.append(f"{Path(caminho).name}: {exc}")

    falhas = [d for d in detalhes if ": ok" not in d]
    if len(falhas) == len(card_paths):
        raise RuntimeError("Nenhum card enviado. " + " | ".join(falhas))

    _enviar_texto(page, legenda)

    if falhas:
        raise RuntimeError("Parcial: " + " | ".join(detalhes))
    return detalhes


def _abrir_contexto(playwright):
    user_data = str(_pasta_sessao())
    opcoes = {
        "user_data_dir": user_data,
        "headless": False,
        "args": ["--disable-blink-features=AutomationControlled"],
        "viewport": {"width": 1280, "height": 900},
        "accept_downloads": True,
    }
    for canal in ("chrome", "msedge", None):
        try:
            if canal:
                return playwright.chromium.launch_persistent_context(channel=canal, **opcoes)
            return playwright.chromium.launch_persistent_context(**opcoes)
        except Exception:
            continue
    raise RuntimeError("Nao foi possivel abrir o navegador para o WhatsApp Web.")


def disparar_cards_whatsapp_web(contatos, legenda, card_paths, intervalo=8, enviar=True):
    if not _playwright_disponivel():
        return False, (
            "Playwright nao instalado. Rode: pip install playwright "
            "&& python -m playwright install chromium"
        )

    from playwright.sync_api import sync_playwright

    resultados = []
    context = None

    try:
        with sync_playwright() as p:
            context = _abrir_contexto(p)
            page = _garantir_pagina(context, context.pages[0] if context.pages else None)

            try:
                _aguardar_whatsapp_logado(page)
            except Exception as exc:
                return False, f"WhatsApp Web nao conectou. Escaneie o QR code: {exc}"

            for contato in contatos:
                telefone = contato["telefone"] if isinstance(contato, dict) else contato
                nome = contato.get("nome", telefone) if isinstance(contato, dict) else telefone
                numero = normalizar_telefone_whatsapp(telefone)
                url = f"https://web.whatsapp.com/send?phone={numero}"

                try:
                    page = _garantir_pagina(context, page)
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(2000)
                    if enviar:
                        info = _anexar_cards_na_conversa(page, card_paths, legenda)
                        resultados.append((nome, True, " | ".join(info)))
                    else:
                        resultados.append((nome, True, "simulado"))
                except Exception as exc:
                    resultados.append((nome, False, str(exc)))
                    page = _garantir_pagina(context, page)

                if intervalo > 0:
                    time.sleep(intervalo)

            page.wait_for_timeout(1500)
            try:
                context.close()
            except Exception:
                pass
    except Exception as exc:
        if context:
            try:
                context.close()
            except Exception:
                pass
        return False, str(exc)

    falhas = [r for r in resultados if not r[1]]
    if falhas and len(falhas) == len(resultados):
        return False, falhas[0][2]
    return True, resultados
