import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Atualiza django.contrib.sites com SITE_DOMAIN (Render/producao)"

    def handle(self, *args, **options):
        domain = (
            os.environ.get("SITE_DOMAIN", "").strip()
            or getattr(settings, "SITE_DOMAIN", "")
            or os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
        )
        if not domain:
            self.stdout.write(self.style.WARNING("SITE_DOMAIN nao definido; site nao alterado."))
            return

        site, created = Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={
                "domain": domain,
                "name": "Rural Pro Amazônia",
            },
        )
        acao = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Site {acao}: {site.domain}"))
