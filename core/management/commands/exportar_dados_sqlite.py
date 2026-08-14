from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Exporta dados do SQLite local para fixture JSON (UTF-8)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--saida",
            default="fixtures/migracao_producao.json",
            help="Arquivo JSON de saida",
        )

    def handle(self, *args, **options):
        origem = "legacy" if "legacy" in settings.DATABASES else "default"
        engine = settings.DATABASES[origem]["ENGINE"]
        if not engine.endswith("sqlite3"):
            raise CommandError(
                "Nenhum SQLite disponivel para exportacao. "
                "Mantenha db.sqlite3 local ou use DATABASE_URL apenas ao importar."
            )

        saida = Path(settings.BASE_DIR) / options["saida"]
        saida.parent.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f"Exportando de {origem} -> {saida} ...")

        with open(saida, "w", encoding="utf-8") as arquivo:
            call_command(
                "dumpdata",
                "--natural-foreign",
                "--natural-primary",
                "-e",
                "contenttypes",
                "-e",
                "auth.Permission",
                "-e",
                "sessions.Session",
                "-e",
                "admin.LogEntry",
                "--database",
                origem,
                indent=2,
                stdout=arquivo,
            )

        self.stdout.write(self.style.SUCCESS(f"Exportado: {saida} ({saida.stat().st_size} bytes)"))
