import sys
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from contato.models import ContatoAlertaClima, InscricaoWhatsApp
from core.clima_whatsapp import (
    abrir_links_whatsapp,
    disparar_cards_anexados,
    enviar_disparo_clima_contato,
    enviar_mensagem_whatsapp,
    formatar_mensagem_clima,
    link_whatsapp,
    normalizar_telefone_whatsapp,
    preparar_disparo_card,
    whatsapp_api_configurada,
)


class Command(BaseCommand):
    help = "Envia o card de clima por WhatsApp para os contatos cadastrados"

    def add_arguments(self, parser):
        parser.add_argument("--hora", help="Aguarda até o horário local (HH:MM)")
        parser.add_argument("--agora", action="store_true", help="Envia imediatamente")
        parser.add_argument("--minutos", type=int, help="Aguarda N minutos antes de enviar")
        parser.add_argument("--segundos", type=int, help="Aguarda N segundos antes de enviar")
        parser.add_argument(
            "--fonte",
            choices=("clima", "noticias", "todos"),
            default="noticias",
        )
        parser.add_argument("--telefones", help="Telefones separados por vírgula")
        parser.add_argument("--texto", action="store_true", help="Envia só texto longo")
        parser.add_argument("--dry-run", action="store_true", help="Mostra o plano sem enviar")
        parser.add_argument(
            "--whatsapp-web",
            action="store_true",
            help="Envia via WhatsApp Web (Playwright) — exige Chrome logado nesta máquina",
        )
        parser.add_argument(
            "--abrir-links",
            action="store_true",
            help="Abre wa.me só com texto (sem cards, manual)",
        )
        parser.add_argument("--intervalo", type=int, default=5)

    def handle(self, *args, **options):
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

        if options["minutos"] and not options["agora"]:
            self._aguardar_minutos(options["minutos"])
        elif options["segundos"] and not options["agora"]:
            self._aguardar_segundos(options["segundos"])
        elif options["hora"] and not options["agora"]:
            self._aguardar_hora(options["hora"])

        contatos = self._obter_contatos(options["telefones"], options["fonte"])
        if not contatos:
            self.stdout.write(self.style.ERROR("Nenhum contato ativo encontrado."))
            return

        self.stdout.write(f"Contatos: {len(contatos)}")

        cards = []
        card_paths = []
        legenda_api = ""
        if options["texto"]:
            mensagem = formatar_mensagem_clima()
            self.stdout.write(mensagem)
        else:
            cards, card_paths, mensagem, urls, legenda_api = preparar_disparo_card()
            for card in cards:
                self.stdout.write(self.style.SUCCESS(f"Card {card['regiao']}: {card['path']}"))
            self.stdout.write(mensagem)
        self.stdout.write("")

        if options["dry_run"]:
            modo = self._modo_envio(options)
            self.stdout.write(f"Modo: {modo}")
            for contato in contatos:
                self.stdout.write(link_whatsapp(contato["telefone"], mensagem))
            for path in card_paths:
                self.stdout.write(f"Anexo cliente: {path}")
            return

        if options["abrir_links"]:
            self.stdout.write(
                self.style.WARNING("wa.me nao anexa cards — apenas texto pre-preenchido.")
            )
            wa_urls = abrir_links_whatsapp(contatos, mensagem, options["intervalo"])
            for contato, url in zip(contatos, wa_urls):
                label = contato.get("nome") or contato["telefone"]
                self.stdout.write(f"{label}: {url}")
            return

        if options["whatsapp_web"]:
            self.stdout.write("Enviando via WhatsApp Web para o cliente...")
            ok, info = disparar_cards_anexados(
                contatos, mensagem, card_paths, intervalo=options["intervalo"]
            )
            self._reportar_resultado(ok, info, card_paths)
            return

        if not whatsapp_api_configurada():
            self.stdout.write(
                self.style.ERROR(
                    "Envio ao cliente exige a API Meta do WhatsApp.\n"
                    "Configure no .env:\n"
                    "  WHATSAPP_ACCESS_TOKEN=...\n"
                    "  WHATSAPP_PHONE_NUMBER_ID=...\n\n"
                    "Cadastro gratuito: https://developers.facebook.com/docs/whatsapp/cloud-api/\n"
                    "Alternativa local (nao recomendada): --whatsapp-web"
                )
            )
            return

        enviados = 0
        for contato in contatos:
            label = contato.get("nome") or contato["telefone"]
            if options["texto"]:
                ok, info = enviar_mensagem_whatsapp(contato["telefone"], mensagem)
            else:
                ok, info = enviar_disparo_clima_contato(contato["telefone"], cards, legenda_api)

            if ok:
                enviados += 1
                self.stdout.write(self.style.SUCCESS(f"{label}: enviado ao cliente ({info})"))
                db_contato = contato.get("obj")
                if db_contato:
                    db_contato.ultimo_envio = timezone.now()
                    db_contato.save(update_fields=["ultimo_envio"])
            else:
                self.stdout.write(self.style.ERROR(f"{label}: falhou — {info}"))

        self.stdout.write(self.style.SUCCESS(f"\n{enviados}/{len(contatos)} cliente(s) atendido(s)."))

    def _modo_envio(self, options):
        if options["abrir_links"]:
            return "wa.me (texto manual)"
        if options["whatsapp_web"]:
            return "WhatsApp Web (Playwright)"
        if whatsapp_api_configurada():
            return "API Meta (direto ao cliente)"
        return "nao configurado — falta API Meta"

    def _reportar_resultado(self, ok, info, card_paths):
        if ok:
            for nome, sucesso, detalhe in info:
                if sucesso:
                    self.stdout.write(self.style.SUCCESS(f"{nome}: {detalhe}"))
                else:
                    self.stdout.write(self.style.ERROR(f"{nome}: {detalhe}"))
            self.stdout.write(
                self.style.SUCCESS(f"\n{len(card_paths)} card(s) por contato (WhatsApp Web).")
            )
        else:
            self.stdout.write(self.style.ERROR(f"Falha: {info}"))
            if isinstance(info, list):
                for nome, sucesso, detalhe in info:
                    if not sucesso:
                        self.stdout.write(self.style.ERROR(f"  {nome}: {detalhe}"))

    def _obter_contatos(self, telefones_arg, fonte="noticias"):
        if telefones_arg:
            contatos = []
            for raw in telefones_arg.split(","):
                telefone = raw.strip()
                if telefone:
                    contatos.append({"telefone": telefone, "nome": telefone, "obj": None})
            return contatos

        contatos = {}
        if fonte in ("clima", "todos"):
            for c in ContatoAlertaClima.objects.filter(ativo=True):
                chave = normalizar_telefone_whatsapp(c.telefone)
                contatos[chave] = {
                    "telefone": c.telefone,
                    "nome": c.nome or c.telefone_formatado,
                    "obj": c,
                }
        if fonte in ("noticias", "todos"):
            for c in InscricaoWhatsApp.objects.filter(ativo=True):
                chave = normalizar_telefone_whatsapp(c.telefone)
                contatos[chave] = {
                    "telefone": c.telefone,
                    "nome": c.nome or c.telefone_formatado,
                    "obj": None,
                }
        return list(contatos.values())

    def _aguardar_segundos(self, segundos):
        if segundos < 1:
            return
        alvo = timezone.now() + timezone.timedelta(seconds=segundos)
        self.stdout.write(
            f"Aguardando {segundos} segundo(s)... disparo às "
            f"{timezone.localtime(alvo).strftime('%H:%M:%S')}."
        )
        while timezone.now() < alvo:
            time.sleep(0.2)

    def _aguardar_minutos(self, minutos):
        if minutos < 1:
            return
        alvo = timezone.now() + timezone.timedelta(minutes=minutos)
        self.stdout.write(
            f"Aguardando {minutos} minuto(s)... disparo às "
            f"{timezone.localtime(alvo).strftime('%H:%M:%S')}."
        )
        while timezone.now() < alvo:
            time.sleep(1)

    def _aguardar_hora(self, hora_str):
        try:
            alvo = datetime.strptime(hora_str.strip(), "%H:%M").time()
        except ValueError:
            self.stdout.write(self.style.ERROR("Horário inválido. Use HH:MM"))
            return

        agora = timezone.localtime(timezone.now())
        disparo = agora.replace(hour=alvo.hour, minute=alvo.minute, second=0, microsecond=0)
        if disparo < agora and (agora - disparo).total_seconds() > 90:
            disparo = disparo + timezone.timedelta(days=1)

        self.stdout.write(f"Aguardando até {disparo.strftime('%d/%m/%Y %H:%M')}...")
        while timezone.localtime(timezone.now()) < disparo:
            time.sleep(2)
