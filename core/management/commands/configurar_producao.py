from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Configura producao no Render: migrate, site, seed e admin"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sem-seed",
            action="store_true",
            help="Nao roda seed_demo (so migrate, site e admin)",
        )

    def handle(self, *args, **options):
        self.stdout.write("Migrando banco...")
        call_command("migrate", "--no-input")

        self.stdout.write("Atualizando site...")
        call_command("atualizar_site")

        if not options["sem_seed"]:
            self.stdout.write("Carregando conteudo demo...")
            call_command("seed_demo")

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                "admin",
                "admin@ruralproamazonia.com.br",
                "admin123",
            )
            self.stdout.write(self.style.SUCCESS("Admin criado: admin / admin123"))
        else:
            self.stdout.write("Admin ja existe (admin).")

        call_command("setup_social_auth")

        self.stdout.write(self.style.SUCCESS("Producao configurada com sucesso."))
