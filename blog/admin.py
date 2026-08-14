from django.contrib import admin
from django.utils.html import format_html

from config.admin import admin_site
from blog.models import Categoria, Post


@admin.register(Categoria, site=admin_site)
class CategoriaAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("nome",)}
    search_fields = ("nome",)


@admin.register(Post, site=admin_site)
class PostAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "publicado", "destaque", "publicado_em", "preview")
    list_filter = ("publicado", "destaque", "categoria")
    list_editable = ("publicado", "destaque")
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ("titulo", "resumo")
    date_hierarchy = "publicado_em"

    def preview(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="max-height:40px"/>', obj.imagem.url)
        return "—"
