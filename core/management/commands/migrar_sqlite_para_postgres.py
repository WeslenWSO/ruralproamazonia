import os
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Migra dados do SQLite local para PostgreSQL (DATABASE_URL do Render)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default="fixtures/migracao_producao.json",
            help="Fixture JSON (gerada por exportar_dados_sqlite)",
        )
        parser.add_argument(
            "--apenas-importar",
            action="store_true",
            help="So importa fixture no Postgres (nao reexporta do SQLite)",
        )

    def handle(self, *args, **options):
        db_url = os.environ.get("DATABASE_URL", "").strip()
        if not db_url.startswith("postgres"):
            raise CommandError(
                "Defina DATABASE_URL com a URL External do Postgres no Render.\n"
                "Exemplo (PowerShell):\n"
                '$env:DATABASE_URL="postgresql://..."; python manage.py migrar_sqlite_para_postgres'
            )

        if settings.DATABASES["default"]["ENGINE"].endswith("sqlite3"):
            raise CommandError(
                "DATABASE_URL nao foi aplicada. Verifique a variavel e reinicie o terminal."
            )

        fixture = Path(settings.BASE_DIR) / options["fixture"]

        if not options["apenas_importar"]:
            if "legacy" not in settings.DATABASES:
                raise CommandError("db.sqlite3 nao encontrado para exportacao legacy.")
            self.stdout.write("Exportando dados do SQLite...")
            call_command("exportar_dados_sqlite", saida=str(fixture))

        if not fixture.exists():
            raise CommandError(f"Fixture nao encontrada: {fixture}")

        self.stdout.write("Migrando schema no PostgreSQL...")
        call_command("migrate", "--no-input")

        self.stdout.write("Atualizando site...")
        call_command("atualizar_site")

        self.stdout.write("Importando dados no PostgreSQL...")
        call_command("loaddata", str(fixture))

        call_command("setup_social_auth")

        self.stdout.write(
            self.style.SUCCESS(
                "Migracao concluida. Confira o site no Render e rode redeploy se necessario."
            )
        )
