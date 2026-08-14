from django.contrib import admin
from django.utils.html import format_html

from config.admin import admin_site
from core.models import ConfiguracaoSite, HistoriaEmpresa, SlideHero


class SingletonAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConfiguracaoSite, site=admin_site)
class ConfiguracaoSiteAdmin(SingletonAdmin):
    fieldsets = (
        ("Identidade", {"fields": ("nome_site", "slogan", "logo", "favicon", "meta_description")}),
        (
            "Contato",
            {"fields": ("telefone", "whatsapp", "email", "endereco", "cidade", "estado")},
        ),
        ("Redes sociais", {"fields": ("facebook", "instagram", "linkedin", "youtube")}),
        (
            "Pilares",
            {
                "fields": (
                    "pilar_1_titulo",
                    "pilar_1_texto",
                    "pilar_2_titulo",
                    "pilar_2_texto",
                    "pilar_3_titulo",
                    "pilar_3_texto",
                )
            },
        ),
        ("Rodapé", {"fields": ("texto_rodape",)}),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:60px"/>', obj.logo.url)
        return "—"

    logo_preview.short_description = "Logo"


@admin.register(HistoriaEmpresa, site=admin_site)
class HistoriaEmpresaAdmin(SingletonAdmin):
    fields = ("titulo", "conteudo", "imagem")

    def imagem_preview(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="max-height:80px"/>', obj.imagem.url)
        return "—"

    readonly_fields = ("imagem_preview",)


@admin.register(SlideHero, site=admin_site)
class SlideHeroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "ordem", "ativo", "preview")
    list_editable = ("ordem", "ativo")
    ordering = ("ordem",)

    def preview(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="max-height:40px"/>', obj.imagem.url)
        if obj.imagem_estatica:
            return format_html('<img src="/static/{}" style="max-height:40px"/>', obj.imagem_estatica)
        return "—"

    preview.short_description = "Imagem"
