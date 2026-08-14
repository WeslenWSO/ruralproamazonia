import logging
import os
import re
import time
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

SELO_VERDE_URL = "https://seloverde.sema.ac.gov.br/consultar-car/"


class SeloVerdeAcreError(Exception):
    pass


class CaptchaPendenteError(SeloVerdeAcreError):
    pass


def _selenium_disponivel():
    try:
        import selenium  # noqa: F401

        return True
    except ImportError:
        return False


def _pasta_downloads():
    pasta = Path(settings.MEDIA_ROOT) / "buscarrural" / "tmp"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _chrome_options(download_dir):
    from selenium.webdriver.chrome.options import Options

    opcoes = Options()
    if not getattr(settings, "SELENIUM_HEADLESS", False):
        opcoes.add_argument("--start-maximized")
    else:
        opcoes.add_argument("--headless=new")
        opcoes.add_argument("--window-size=1400,900")

    opcoes.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        },
    )
    opcoes.add_experimental_option("excludeSwitches", ["enable-automation"])
    opcoes.add_experimental_option("useAutomationExtension", False)
    opcoes.add_argument("--disable-blink-features=AutomationControlled")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    return opcoes


def _aplicar_stealth(driver):
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = window.chrome || { runtime: {} };
                Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                """,
            },
        )
    except Exception:
        pass


def _criar_driver(download_dir):
    opcoes = _chrome_options(download_dir)
    if getattr(settings, "SELENIUM_USE_UNDETECTED", True):
        try:
            import undetected_chromedriver as uc

            driver = uc.Chrome(options=opcoes, use_subprocess=True)
            _aplicar_stealth(driver)
            return driver
        except Exception as exc:
            logger.warning("undetected-chromedriver indisponível, usando Selenium padrão: %s", exc)

    from selenium import webdriver

    driver = webdriver.Chrome(options=opcoes)
    _aplicar_stealth(driver)
    return driver


def _destacar_janela(driver):
    try:
        driver.maximize_window()
        driver.switch_to.window(driver.current_window_handle)
    except Exception:
        pass
    if os.name != "nt":
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        SW_RESTORE = 9

        titulo_alvo = (driver.title or "").lower()

        def _enum_callback(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            titulo = buffer.value.lower()
            if "chrome" in titulo and (
                "selo" in titulo
                or "consultar car" in titulo
                or (titulo_alvo and titulo_alvo in titulo)
            ):
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumWindows(WNDENUMPROC(_enum_callback), 0)
    except Exception:
        pass


def _instruir_captcha(driver):
    driver.execute_script(
        """
        (function () {
          var id = 'ruralpro-captcha-help';
          if (document.getElementById(id)) return;
          var box = document.createElement('div');
          box.id = id;
          box.style.cssText = [
            'position:fixed','top:0','left:0','right:0','z-index:999999',
            'background:#0f3320','color:#fff','padding:14px 18px',
            'font:600 16px/1.4 Segoe UI, Arial, sans-serif',
            'box-shadow:0 4px 20px rgba(0,0,0,.35)','text-align:center'
          ].join(';');
          box.innerHTML = 'RuralPro BuscarRural: clique em <strong>Não sou um robô</strong> abaixo. '
            + 'A consulta continua automaticamente após a verificação.';
          document.body.prepend(box);
        })();
        """
    )


def _captcha_resolvido(driver):
    return driver.execute_script(
        """
        function captchaResolvido() {
          var input = document.querySelector('[name=captcha_answer]');
          if (input && input.value && String(input.value).trim()) return true;

          var cap = document.getElementById('captcha_wrapper');
          if (!cap) return false;

          if (cap.getAttribute('data-cap-solved') === 'true') return true;
          if (cap.getAttribute('data-cap-state') === 'solved') return true;

          if (cap.shadowRoot) {
            var solved = cap.shadowRoot.querySelector('[data-cap-state="solved"], .cap-solved, [aria-label*="Verificado"]');
            if (solved) return true;
            var hidden = cap.shadowRoot.querySelector('[name=captcha_answer], input[type="hidden"]');
            if (hidden && hidden.value && String(hidden.value).trim()) return true;
          }

          var texto = (cap.textContent || cap.innerText || '').toLowerCase();
          if (texto.indexOf('verificado') >= 0 || texto.indexOf('você é humano') >= 0) return true;
          return false;
        }
        return captchaResolvido();
        """
    )


def _destacar_captcha(driver):
    driver.execute_script(
        """
        (function () {
          var cap = document.getElementById('captcha_wrapper');
          if (!cap) return;
          cap.scrollIntoView({ behavior: 'smooth', block: 'center' });
          cap.style.outline = '3px solid #c9a227';
          cap.style.outlineOffset = '4px';
          cap.style.boxShadow = '0 0 0 6px rgba(201,162,39,.25)';
        })();
        """
    )


def _aguardar_formulario(driver, timeout=45):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, "car_code"))
    )
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script(
            "var f=document.getElementById('car_form'); "
            "return f && window.getComputedStyle(f).display !== 'none';"
        )
    )
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, "captcha_wrapper"))
    )


def _resolver_captcha_automatico(driver, timeout=120):
    """Resolve o Cap.js via API programática ou clique no widget."""
    resultado = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        const timeoutMs = arguments[0];

        (async () => {
          const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

          const endpointAttr = document.getElementById('captcha_wrapper')
            ?.getAttribute('data-cap-api-endpoint') || '/captcha2/api/';
          const endpoint = new URL(endpointAttr, location.origin).href.replace(/\\/$/, '') + '/';

          const setToken = (token) => {
            if (!token) return false;
            let input = document.querySelector('[name=captcha_answer]');
            if (!input) {
              input = document.createElement('input');
              input.type = 'hidden';
              input.name = 'captcha_answer';
              document.getElementById('car_form')?.appendChild(input);
            }
            input.value = token;
            input.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
          };

          const already = () => {
            const input = document.querySelector('[name=captcha_answer]');
            return !!(input && String(input.value || '').trim());
          };

          if (already()) {
            done({ ok: true, method: 'existing' });
            return;
          }

          const waitToken = (timeout) => new Promise((resolve, reject) => {
            const started = Date.now();
            const timer = setInterval(() => {
              if (already()) {
                clearInterval(timer);
                resolve(document.querySelector('[name=captcha_answer]').value);
                return;
              }
              if (Date.now() - started > timeout) {
                clearInterval(timer);
                reject(new Error('timeout'));
              }
            }, 250);
          });

          // 1) Cap.solve() programático (modo documentado do Cap.js)
          try {
            const mod = await import('https://cdn.jsdelivr.net/npm/@cap.js/widget');
            const Cap = mod.default || mod.Cap;
            if (typeof Cap === 'function') {
              const cap = new Cap({ apiEndpoint: endpoint });
              const sol = await cap.solve();
              const token = sol?.token || sol?.answer || sol;
              if (typeof token === 'string' && setToken(token)) {
                done({ ok: true, method: 'cap.solve' });
                return;
              }
            }
          } catch (e) {
            /* tenta próxima estratégia */
          }

          // 2) Clicar no widget visível e aguardar proof-of-work
          const widget = document.getElementById('captcha_wrapper');
          if (widget) {
            try {
              widget.addEventListener('solve', (e) => {
                const token = e.detail?.token;
                if (token) setToken(token);
              }, { once: true });

              const clickTarget =
                widget.shadowRoot?.querySelector('[role="button"], button, .cap-box, .cap-widget') ||
                widget;
              clickTarget.click();
              await sleep(300);
              if (!already() && widget.shadowRoot) {
                widget.shadowRoot.querySelector('[role="button"], button, .cap-box')?.click();
              }

              const token = await waitToken(Math.min(timeoutMs, 90000));
              done({ ok: true, method: 'widget.click', tokenLen: token.length });
              return;
            } catch (e) {
              /* continua */
            }
          }

          done({ ok: false, error: 'Não foi possível resolver o Cap.js automaticamente.' });
        })();
        """,
        int(timeout * 1000),
    )
    if not resultado:
        return False
    if resultado.get("ok"):
        logger.info("Captcha Cap.js resolvido via %s", resultado.get("method"))
        return True
    logger.warning("Falha ao resolver captcha automaticamente: %s", resultado.get("error"))
    return False


def _aguardar_captcha(driver, timeout, on_progress=None):
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait

    if on_progress:
        on_progress("Resolvendo verificação anti-robô automaticamente…")

    if _resolver_captcha_automatico(driver, timeout=min(timeout, 120)):
        if _captcha_resolvido(driver):
            try:
                driver.execute_script(
                    "var el=document.getElementById('ruralpro-captcha-help'); if(el) el.remove();"
                )
            except Exception:
                pass
            return

    inicio = time.time()
    ultimo_lembrete = 0

    _destacar_janela(driver)
    _instruir_captcha(driver)
    _destacar_captcha(driver)

    if on_progress:
        on_progress(
            "Resolução automática falhou. Clique em “Não sou um robô” na janela do Chrome."
        )

    def resolvido(_driver):
        nonlocal ultimo_lembrete
        agora = time.time()
        if agora - ultimo_lembrete >= 12:
            ultimo_lembrete = agora
            _destacar_janela(_driver)
            _instruir_captcha(_driver)
            _destacar_captcha(_driver)
            if on_progress:
                restante = max(0, int(timeout - (agora - inicio)))
                on_progress(
                    f"Aguardando captcha no Chrome… ({restante}s restantes)."
                )
        ok = _captcha_resolvido(_driver)
        if ok:
            try:
                _driver.execute_script(
                    "var el=document.getElementById('ruralpro-captcha-help'); if(el) el.remove();"
                )
            except Exception:
                pass
        return ok

    try:
        WebDriverWait(driver, timeout, poll_frequency=0.5).until(resolvido)
    except TimeoutException as exc:
        raise CaptchaPendenteError(
            "Não foi possível concluir a verificação anti-robô. Tente novamente."
        ) from exc


def _clicar_gerar_relatorio(driver):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    botao = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='button'][value*='Gerar']"))
    )
    resposta = driver.execute_script(
        """
        var input = document.querySelector('[name=captcha_answer]');
        if (!input || !String(input.value || '').trim()) return 'sem_captcha';
        document.getElementById('ispdf').value = '';
        getCarInfo(document.getElementById('car_code').value, '', '');
        return 'ok';
        """
    )
    if resposta != "ok":
        botao.click()
    time.sleep(2)


def _aguardar_iframe_resultado(driver, timeout=120):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    iframe = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, "icar_result"))
    )

    def iframe_carregado(d):
        src = iframe.get_attribute("src") or ""
        if not src or "get_by_car_unificado.php" not in src:
            return False
        try:
            altura = d.execute_script(
                "var f = document.getElementById('icar_result'); return f ? f.offsetHeight : 0;"
            )
            return altura and int(altura) > 120
        except Exception:
            return False

    WebDriverWait(driver, timeout).until(iframe_carregado)
    return iframe


def _extrair_dados_iframe(driver, iframe):
    driver.switch_to.frame(iframe)
    time.sleep(2)

    dados = driver.execute_script(
        """
        const out = { campos: {}, secoes: [], texto_resumo: '' };
        const tabelas = document.querySelectorAll('table');
        tabelas.forEach((tabela) => {
          const secao = { titulo: '', linhas: [] };
          const titulo = tabela.previousElementSibling;
          if (titulo && titulo.textContent) secao.titulo = titulo.textContent.trim();
          tabela.querySelectorAll('tr').forEach(tr => {
            const cells = Array.from(tr.querySelectorAll('th,td')).map(c => c.innerText.trim()).filter(Boolean);
            if (cells.length >= 2) {
              secao.linhas.push({ rotulo: cells[0], valor: cells.slice(1).join(' | ') });
              out.campos[cells[0]] = cells.slice(1).join(' | ');
            } else if (cells.length === 1) {
              secao.linhas.push({ rotulo: cells[0], valor: '' });
            }
          });
          if (secao.linhas.length) out.secoes.push(secao);
        });

        document.querySelectorAll('dl').forEach(dl => {
          const dts = dl.querySelectorAll('dt');
          const dds = dl.querySelectorAll('dd');
          dts.forEach((dt, i) => {
            const rotulo = dt.innerText.trim();
            const valor = (dds[i] || {}).innerText ? dds[i].innerText.trim() : '';
            if (rotulo) out.campos[rotulo] = valor;
          });
        });

        out.texto_resumo = (document.body.innerText || '').slice(0, 12000);
        return out;
        """
    )

    atualizado = ""
    texto = dados.get("texto_resumo", "")
    match = re.search(r"Atualizado em:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})", texto)
    if match:
        atualizado = match.group(1)

    driver.switch_to.default_content()
    return dados, atualizado


def consultar_selo_verde_acre(numero_car, captcha_timeout=None, on_progress=None):
    if not _selenium_disponivel():
        raise SeloVerdeAcreError("Selenium não instalado. Rode: pip install selenium")

    from selenium.webdriver.common.by import By

    captcha_timeout = captcha_timeout or getattr(settings, "SELENIUM_CAPTCHA_TIMEOUT", 300)
    download_dir = _pasta_downloads()
    driver = None

    try:
        if on_progress:
            on_progress("Abrindo Chrome no Selo Verde AC…")
        driver = _criar_driver(download_dir)
        driver.set_page_load_timeout(90)
        driver.get(SELO_VERDE_URL)
        _aguardar_formulario(driver)

        campo = driver.find_element(By.ID, "car_code")
        campo.clear()
        campo.send_keys(numero_car)

        logger.info("Aguardando captcha Selo Verde para CAR %s", numero_car)
        driver.set_script_timeout(max(captcha_timeout, 120))
        _aguardar_captcha(driver, captcha_timeout, on_progress=on_progress)

        if on_progress:
            on_progress("Captcha verificado. Gerando relatório socioambiental…")
        _clicar_gerar_relatorio(driver)

        if on_progress:
            on_progress("Lendo dados do relatório na tela…")
        iframe = _aguardar_iframe_resultado(driver)
        dados, atualizado_em = _extrair_dados_iframe(driver, iframe)

        if not dados.get("campos") and not dados.get("secoes"):
            raise SeloVerdeAcreError(
                "Nenhum dado encontrado na tela. Verifique o código CAR ou tente novamente."
            )

        if on_progress:
            on_progress("Salvando dados no histórico…")
        return {
            "dados": dados,
            "atualizado_em_site": atualizado_em,
        }
    except SeloVerdeAcreError:
        raise
    except Exception as exc:
        raise SeloVerdeAcreError(str(exc)) from exc
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
