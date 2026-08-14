from django.contrib import admin

from buscarrural.models import ConsultaHistorico
from config.admin import admin_site


@admin.register(ConsultaHistorico, site=admin_site)
class ConsultaHistoricoAdmin(admin.ModelAdmin):
    list_display = ("numero_car", "usuario", "tipo", "status", "criado_em")
    list_filter = ("status", "tipo", "criado_em")
    search_fields = ("numero_car", "usuario__username", "usuario__email")
    readonly_fields = ("criado_em", "atualizado_em", "dados", "parecer")
    date_hierarchy = "criado_em"
