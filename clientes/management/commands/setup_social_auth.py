from django.core.management.base import BaseCommand

from clientes.social_auth import (
    apple_configurado,
    facebook_configurado,
    google_configurado,
    provedores_sociais,
    sync_social_apps,
)


class Command(BaseCommand):
    help = "Sincroniza provedores sociais a partir do .env (opcional; também pode usar o admin)"

    def handle(self, *args, **options):
        sync_social_apps()
        ativos = provedores_sociais()

        if ativos["google"]:
            self.stdout.write(self.style.SUCCESS("Google ativo"))
        else:
            self.stdout.write(self.style.WARNING("Google inativo"))

        if ativos["facebook"]:
            self.stdout.write(self.style.SUCCESS("Facebook ativo"))
        else:
            self.stdout.write(self.style.WARNING("Facebook inativo"))

        if ativos["apple"]:
            self.stdout.write(self.style.SUCCESS("Apple ativo"))
        else:
            self.stdout.write(self.style.WARNING("Apple inativo"))

        if not any(ativos.values()):
            self.stdout.write(
                self.style.ERROR(
                    "\nNenhum login social ativo.\n"
                    "Configure em /admin/socialaccount/socialapp/add/ "
                    "ou preencha GOOGLE_CLIENT_ID no .env e rode este comando."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("\nLogin social pronto para uso."))

        if google_configurado() or facebook_configurado() or apple_configurado():
            self.stdout.write("Credenciais do .env sincronizadas com o banco.")
