from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from allauth.socialaccount.models import SocialApp

from config.admin import admin_site


@admin.register(Site, site=admin_site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("domain", "name")
    fieldsets = (
        (
            None,
            {
                "fields": ("domain", "name"),
                "description": (
                    "Em desenvolvimento use <strong>127.0.0.1:8000</strong>. "
                    "Em produção use o domínio real do site."
                ),
            },
        ),
    )


@admin.register(SocialApp, site=admin_site)
class SocialAppAdmin(admin.ModelAdmin):
    list_display = ("provider", "name", "client_id", "sites_display", "ativo_display")
    list_filter = ("provider",)
    search_fields = ("name", "client_id")
    filter_horizontal = ("sites",)
    fieldsets = (
        (
            "Provedor",
            {
                "fields": ("provider", "name"),
                "description": (
                    "Cadastre Google, Facebook ou Apple. "
                    "Após salvar, o botão correspondente é liberado no cadastro/login."
                ),
            },
        ),
        ("Credenciais OAuth", {"fields": ("client_id", "secret", "key")}),
        ("Site", {"fields": ("sites",)}),
        (
            "URLs de callback (desenvolvimento)",
            {
                "fields": ("callback_help",),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("callback_help",)

    def sites_display(self, obj):
        return ", ".join(obj.sites.values_list("domain", flat=True)) or "—"

    sites_display.short_description = "Sites"

    def ativo_display(self, obj):
        if obj.client_id and obj.secret:
            return format_html('<span style="color:#2e7d32;">Ativo</span>')
        return format_html('<span style="color:#999;">Incompleto</span>')

    ativo_display.short_description = "Status"

    def callback_help(self, obj):
        urls = {
            "google": "http://127.0.0.1:8000/accounts/google/login/callback/",
            "facebook": "http://127.0.0.1:8000/accounts/facebook/login/callback/",
            "apple": "http://127.0.0.1:8000/accounts/apple/login/callback/",
        }
        linhas = "".join(
            f"<li><strong>{nome.title()}:</strong> <code>{url}</code></li>"
            for nome, url in urls.items()
        )
        return mark_safe(
            "<p>Use estas URLs nos consoles OAuth:</p>"
            f"<ul>{linhas}</ul>"
        )

    callback_help.short_description = "Callbacks"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        site = Site.objects.get_current()
        if not obj.sites.filter(pk=site.pk).exists():
            obj.sites.add(site)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "provider":
            field.help_text = "Escolha google, facebook ou apple."
        return field

    def get_changeform_initial_data(self, request):
        site = Site.objects.get_current()
        return {"sites": [site.pk]}
