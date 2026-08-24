import os

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

        admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
        admin_user = User.objects.filter(username="admin").first()
        if not admin_user:
            if not admin_password:
                admin_password = "admin123"
            User.objects.create_superuser(
                "admin",
                "admin@ruralproamazonia.com.br",
                admin_password,
            )
            self.stdout.write(self.style.SUCCESS("Admin criado: admin"))
        elif admin_password:
            admin_user.set_password(admin_password)
            admin_user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS("Senha do admin atualizada."))
        else:
            self.stdout.write("Admin ja existe (admin).")

        call_command("setup_social_auth")

        self.stdout.write(self.style.SUCCESS("Producao configurada com sucesso."))
