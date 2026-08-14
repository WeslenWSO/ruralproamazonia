from django.contrib import admin

from config.admin import admin_site
from clientes.models import PerfilCliente


@admin.register(PerfilCliente, site=admin_site)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "user", "empresa", "telefone", "criado_em")
    search_fields = ("nome_completo", "user__username", "empresa", "documento")
