from django.contrib import admin
from django.contrib.auth.models import Group, User


class RuralProAdminSite(admin.AdminSite):
    site_header = "Rural Pro Amazônia — Painel Admin"
    site_title = "Rural Pro Amazônia"
    index_title = "Administração do site"


admin_site = RuralProAdminSite(name="ruralpro_admin")

admin_site.register(User)
admin_site.register(Group)
