from django.contrib import admin

from config.admin import admin_site
from contato.models import ContatoAlertaClima, InscricaoWhatsApp, MensagemContato


@admin.register(InscricaoWhatsApp, site=admin_site)
class InscricaoWhatsAppAdmin(admin.ModelAdmin):
    list_display = ("telefone", "nome", "ativo", "criado_em")
    list_filter = ("ativo", "criado_em")
    search_fields = ("telefone", "nome")
    list_editable = ("ativo",)
    readonly_fields = ("criado_em",)


@admin.register(ContatoAlertaClima, site=admin_site)
class ContatoAlertaClimaAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "ativo", "ultimo_envio", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "telefone")
    list_editable = ("ativo",)
    readonly_fields = ("ultimo_envio", "criado_em")


@admin.register(MensagemContato, site=admin_site)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "assunto", "lida", "criado_em")
    list_filter = ("lida", "criado_em")
    search_fields = ("nome", "email", "assunto", "mensagem")
    readonly_fields = ("nome", "email", "telefone", "assunto", "mensagem", "criado_em")
    list_editable = ("lida",)
