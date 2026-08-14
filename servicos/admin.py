from django.contrib import admin
from django.utils.html import format_html

from config.admin import admin_site
from servicos.models import Servico


@admin.register(Servico, site=admin_site)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "link", "destaque", "ativo", "ordem", "preview")
    list_editable = ("destaque", "ativo", "ordem")
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ("titulo", "resumo", "link")
    ordering = ("ordem",)
    fieldsets = (
        (None, {"fields": ("titulo", "slug", "resumo", "link", "descricao")}),
        ("Mídia", {"fields": ("imagem", "imagem_estatica")}),
        ("Publicação", {"fields": ("destaque", "ativo", "ordem")}),
    )

    def preview(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="max-height:40px"/>', obj.imagem.url)
        return "—"
