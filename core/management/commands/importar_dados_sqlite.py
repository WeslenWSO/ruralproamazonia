from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Importa fixtures/dados_sqlite.json para o banco atual (PostgreSQL no Render)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--arquivo",
            default="fixtures/dados_sqlite.json",
            help="Fixture JSON gerada por exportar_sqlite",
        )
        parser.add_argument(
            "--forcar",
            action="store_true",
            help="Importa mesmo se ja houver dados em servicos.Servico",
        )

    def handle(self, *args, **options):
        from django.conf import settings
        from django.db import connection

        arquivo = Path(options["arquivo"])
        if not arquivo.exists():
            self.stdout.write(
                self.style.WARNING(f"Fixture nao encontrada: {arquivo.as_posix()}")
            )
            return

        engine = connection.settings_dict["ENGINE"]
        if "postgresql" not in engine and "postgres" not in engine:
            if settings.ON_RENDER:
                self.stdout.write(
                    self.style.ERROR(
                        "No Render, configure DATABASE_URL (PostgreSQL) antes de importar."
                    )
                )
                return
            self.stdout.write(
                self.style.WARNING(
                    f"Banco atual: {engine}. Importacao pensada para PostgreSQL."
                )
            )

        Servico = apps.get_model("servicos", "Servico")
        if Servico.objects.exists() and not options["forcar"]:
            self.stdout.write(
                self.style.WARNING(
                    "Banco ja possui dados. Use --forcar para reimportar."
                )
            )
            return

        if options["forcar"] and Servico.objects.exists():
            self.stdout.write("Limpando dados existentes antes da importacao...")
            for model in reversed(apps.get_models()):
                if model._meta.app_label in {
                    "admin",
                    "auth",
                    "contenttypes",
                    "sessions",
                    "sites",
                }:
                    continue
                model.objects.all().delete()

        call_command("loaddata", str(arquivo))
        self.stdout.write(self.style.SUCCESS(f"Dados importados de {arquivo.as_posix()}"))
