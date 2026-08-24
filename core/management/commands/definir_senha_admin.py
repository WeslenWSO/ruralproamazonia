import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Define a senha do superusuario admin (usa ADMIN_PASSWORD do ambiente ou --senha)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--senha",
            help="Nova senha (preferir ADMIN_PASSWORD no ambiente em producao)",
        )
        parser.add_argument(
            "--username",
            default="admin",
            help="Usuario admin (padrao: admin)",
        )

    def handle(self, *args, **options):
        senha = (options.get("senha") or os.environ.get("ADMIN_PASSWORD", "")).strip()
        if not senha:
            raise CommandError(
                "Informe --senha ou defina a variavel de ambiente ADMIN_PASSWORD."
            )

        username = options["username"]
        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_superuser(
                username,
                "admin@ruralproamazonia.com.br",
                senha,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Admin criado: {username}")
            )
            return

        user.set_password(senha)
        user.save(update_fields=["password"])
        self.stdout.write(
            self.style.SUCCESS(f"Senha de {username} alterada com sucesso.")
        )
