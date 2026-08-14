#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera arquivos do site institucional Rural Pro Amazônia."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS_DIR = Path(
    r"C:\Users\wesle\.cursor\projects\c-Users-wesle-OneDrive-Documentos-GitHub-ruralproamazonia\assets"
)


def write(rel: str, content: str) -> None:
    path = ROOT / rel.replace("/", "\\") if "\\" not in rel else ROOT / rel
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"  + {rel}")


def copy_static_images() -> None:
    dest = ROOT / "static" / "img"
    dest.mkdir(parents=True, exist_ok=True)
    names = [
        "logo.png",
        "hero-1.png",
        "hero-2.png",
        "hero-3.png",
        "servico-1.png",
        "servico-2.png",
        "servico-3.png",
        "blog-1.png",
        "blog-2.png",
        "blog-3.png",
        "about.jpg",
    ]
    if not ASSETS_DIR.is_dir():
        print("  (assets não encontrados — usando caminhos static/img/)")
        return
    files = []
    for candidate in ASSETS_DIR.glob("*.*"):
        try:
            candidate.stat()
        except OSError:
            continue
        files.append(candidate)
    files.sort(key=lambda p: p.stat().st_size)
    if not files:
        return
    # logo: menor arquivo; demais por tamanho decrescente para heroes
    logo = min(files, key=lambda p: p.stat().st_size)
    rest = [f for f in files if f != logo]
    rest.sort(key=lambda p: p.stat().st_size, reverse=True)
    ordered = [logo] + rest
    for i, src in enumerate(ordered):
        ext = src.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            ext = ".png"
        name = names[i] if i < len(names) else f"img-{i + 1}{ext}"
        if not name.lower().endswith(ext.replace(".", "")):
            stem = Path(name).stem
            name = stem + ext
        target = dest / name
        shutil.copy2(src, target)
        print(f"  img: {src.name} -> static/img/{name}")


def build_files():
    files = {}

    files["config/urls.py"] = """
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.admin import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("core.urls")),
    path("servicos/", include("servicos.urls")),
    path("blog/", include("blog.urls")),
    path("contato/", include("contato.urls")),
    path("clientes/", include("clientes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""

    files["config/admin.py"] = """
from django.contrib import admin
from django.contrib.auth.models import Group, User


class RuralProAdminSite(admin.AdminSite):
    site_header = "Rural Pro Amazônia — Painel Admin"
    site_title = "Rural Pro Amazônia"
    index_title = "Administração do site"


admin_site = RuralProAdminSite(name="ruralpro_admin")

admin_site.register(User)
admin_site.register(Group)
"""

    files["core/models.py"] = """
from ckeditor.fields import RichTextField
from django.db import models
from django.utils.text import slugify


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ConfiguracaoSite(SingletonModel):
    nome_site = models.CharField("Nome do site", max_length=120, default="Rural Pro Amazônia")
    slogan = models.CharField(max_length=200, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=80, blank=True, default="Manaus")
    estado = models.CharField(max_length=2, blank=True, default="AM")
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    logo = models.ImageField(upload_to="site/", blank=True, null=True)
    favicon = models.ImageField(upload_to="site/", blank=True, null=True)
    pilar_1_titulo = models.CharField(max_length=80, default="Sustentabilidade")
    pilar_1_texto = models.TextField(blank=True)
    pilar_2_titulo = models.CharField(max_length=80, default="Inovação")
    pilar_2_texto = models.TextField(blank=True)
    pilar_3_titulo = models.CharField(max_length=80, default="Comunidade")
    pilar_3_texto = models.TextField(blank=True)
    texto_rodape = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = "Configuração do site"
        verbose_name_plural = "Configuração do site"

    def __str__(self):
        return self.nome_site


class HistoriaEmpresa(SingletonModel):
    titulo = models.CharField(max_length=200, default="Nossa história")
    conteudo = RichTextField()
    imagem = models.ImageField(upload_to="historia/", blank=True, null=True)

    class Meta:
        verbose_name = "História da empresa"
        verbose_name_plural = "História da empresa"

    def __str__(self):
        return self.titulo


class SlideHero(models.Model):
    titulo = models.CharField(max_length=150)
    subtitulo = models.CharField(max_length=255, blank=True)
    imagem = models.ImageField(upload_to="slides/", blank=True, null=True)
    imagem_estatica = models.CharField(
        "Imagem estática (static/img)",
        max_length=120,
        blank=True,
        help_text="Caminho relativo em static, ex: img/hero-1.png",
    )
    texto_botao = models.CharField(max_length=60, blank=True, default="Saiba mais")
    link = models.CharField(max_length=255, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordem", "id"]
        verbose_name = "Slide do hero"
        verbose_name_plural = "Slides do hero"

    def __str__(self):
        return self.titulo

    @property
    def imagem_url(self):
        if self.imagem:
            return self.imagem.url
        if self.imagem_estatica:
            return f"/static/{self.imagem_estatica.lstrip('/')}"
        return "/static/img/hero-1.png"
"""


    files["core/admin.py"] = """
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
"""

    files["core/views.py"] = """
from django.shortcuts import render

from blog.models import Post
from core.models import HistoriaEmpresa, SlideHero
from servicos.models import Servico


def home(request):
    slides = SlideHero.objects.filter(ativo=True)
    servicos = Servico.objects.filter(ativo=True, destaque=True)[:6]
    if not servicos.exists():
        servicos = Servico.objects.filter(ativo=True)[:6]
    posts = Post.objects.filter(publicado=True, destaque=True)[:3]
    if not posts.exists():
        posts = Post.objects.filter(publicado=True)[:3]
    historia = HistoriaEmpresa.load()
    return render(
        request,
        "core/home.html",
        {
            "slides": slides,
            "servicos_destaque": servicos,
            "posts_destaque": posts,
            "historia": historia,
        },
    )
"""

    files["core/urls.py"] = """
from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
]
"""

    files["core/context_processors.py"] = """
from core.models import ConfiguracaoSite


def site_config(request):
    try:
        config = ConfiguracaoSite.load()
    except Exception:
        config = None
    return {"site_config": config}
"""

    files["core/management/__init__.py"] = ""

    files["core/management/commands/__init__.py"] = ""


    files["servicos/models.py"] = """
from ckeditor.fields import RichTextField
from django.db import models
from django.utils.text import slugify


class Servico(models.Model):
    titulo = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    resumo = models.TextField(max_length=400)
    descricao = RichTextField()
    imagem = models.ImageField(upload_to="servicos/", blank=True, null=True)
    imagem_estatica = models.CharField(max_length=120, blank=True)
    destaque = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordem", "titulo"]
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo) or "servico"
            slug = base
            n = 1
            while Servico.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def imagem_url(self):
        if self.imagem:
            return self.imagem.url
        if self.imagem_estatica:
            return f"/static/{self.imagem_estatica.lstrip('/')}"
        return "/static/img/servico-1.png"
"""

    files["servicos/views.py"] = """
from django.shortcuts import get_object_or_404, render

from servicos.models import Servico


def lista_servicos(request):
    servicos = Servico.objects.filter(ativo=True)
    return render(request, "servicos/lista.html", {"servicos": servicos})


def detalhe_servico(request, slug):
    servico = get_object_or_404(Servico, slug=slug, ativo=True)
    relacionados = Servico.objects.filter(ativo=True).exclude(pk=servico.pk)[:3]
    return render(
        request,
        "servicos/detalhe.html",
        {"servico": servico, "relacionados": relacionados},
    )
"""

    files["servicos/admin.py"] = """
from django.contrib import admin
from django.utils.html import format_html

from config.admin import admin_site
from servicos.models import Servico


@admin.register(Servico, site=admin_site)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "destaque", "ativo", "ordem", "preview")
    list_editable = ("destaque", "ativo", "ordem")
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ("titulo", "resumo")
    ordering = ("ordem",)

    def preview(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="max-height:40px"/>', obj.imagem.url)
        return "—"
"""

    files["servicos/urls.py"] = """
from django.urls import path

from servicos import views

app_name = "servicos"

urlpatterns = [
    path("", views.lista_servicos, name="lista"),
    path("<slug:slug>/", views.detalhe_servico, name="detalhe"),
]
"""

    files["blog/models.py"] = """
from ckeditor.fields import RichTextField
from django.db import models
from django.utils.text import slugify


class Categoria(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome) or "categoria"
        super().save(*args, **kwargs)


class Post(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    autor = models.CharField(max_length=100, default="Rural Pro Amazônia")
    resumo = models.TextField(max_length=500)
    conteudo = RichTextField()
    imagem = models.ImageField(upload_to="blog/", blank=True, null=True)
    imagem_estatica = models.CharField(max_length=120, blank=True)
    link_externo = models.URLField("Link externo", blank=True)
    destaque = models.BooleanField(default=False)
    publicado = models.BooleanField(default=True)
    publicado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publicado_em"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo) or "post"
            slug = base
            n = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def imagem_url(self):
        if self.imagem:
            return self.imagem.url
        if self.imagem_estatica:
            return f"/static/{self.imagem_estatica.lstrip('/')}"
        return "/static/img/blog-1.png"
"""


    files["blog/views.py"] = """
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from blog.models import Post


def lista_posts(request):
    qs = Post.objects.filter(publicado=True)
    paginator = Paginator(qs, 9)
    page = request.GET.get("page")
    posts = paginator.get_page(page)
    return render(request, "blog/lista.html", {"posts": posts})


def detalhe_post(request, slug):
    post = get_object_or_404(Post, slug=slug, publicado=True)
    recentes = Post.objects.filter(publicado=True).exclude(pk=post.pk)[:3]
    return render(request, "blog/detalhe.html", {"post": post, "recentes": recentes})
"""

    files["blog/admin.py"] = """
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
"""

    files["blog/urls.py"] = """
from django.urls import path

from blog import views

app_name = "blog"

urlpatterns = [
    path("", views.lista_posts, name="lista"),
    path("<slug:slug>/", views.detalhe_post, name="detalhe"),
]
"""

    files["contato/models.py"] = """
from django.db import models


class MensagemContato(models.Model):
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    assunto = models.CharField(max_length=150)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Mensagem de contato"
        verbose_name_plural = "Mensagens de contato"

    def __str__(self):
        return f"{self.nome} — {self.assunto}"
"""

    files["contato/forms.py"] = """
from django import forms

from contato.models import MensagemContato


class ContatoForm(forms.ModelForm):
    class Meta:
        model = MensagemContato
        fields = ("nome", "email", "telefone", "assunto", "mensagem")
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu nome"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "E-mail"}),
            "telefone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Telefone"}),
            "assunto": forms.TextInput(attrs={"class": "form-control", "placeholder": "Assunto"}),
            "mensagem": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Sua mensagem"}
            ),
        }
"""

    files["contato/views.py"] = """
from django.contrib import messages
from django.shortcuts import redirect, render

from contato.forms import ContatoForm


def contato(request):
    if request.method == "POST":
        form = ContatoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mensagem enviada com sucesso! Em breve entraremos em contato.")
            return redirect("contato:contato")
    else:
        form = ContatoForm()
    return render(request, "contato/contato.html", {"form": form})
"""

    files["contato/admin.py"] = """
from django.contrib import admin

from config.admin import admin_site
from contato.models import MensagemContato


@admin.register(MensagemContato, site=admin_site)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "assunto", "lida", "criado_em")
    list_filter = ("lida", "criado_em")
    search_fields = ("nome", "email", "assunto", "mensagem")
    readonly_fields = ("nome", "email", "telefone", "assunto", "mensagem", "criado_em")
    list_editable = ("lida",)
"""

    files["contato/urls.py"] = """
from django.urls import path

from contato import views

app_name = "contato"

urlpatterns = [
    path("", views.contato, name="contato"),
]
"""


    files["clientes/models.py"] = """
from django.conf import settings
from django.db import models


class PerfilCliente(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    nome_completo = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    documento = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de cliente"
        verbose_name_plural = "Perfis de clientes"

    def __str__(self):
        return self.nome_completo or self.user.username
"""

    files["clientes/forms.py"] = """
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from clientes.models import PerfilCliente


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Usuário"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Senha"}))


class CadastroForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    nome_completo = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    empresa = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    telefone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    documento = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            PerfilCliente.objects.create(
                user=user,
                nome_completo=self.cleaned_data["nome_completo"],
                empresa=self.cleaned_data.get("empresa", ""),
                telefone=self.cleaned_data.get("telefone", ""),
                documento=self.cleaned_data.get("documento", ""),
            )
        return user
"""

    files["clientes/views.py"] = """
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from clientes.forms import CadastroForm, LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("clientes:painel")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("clientes:painel")
    return render(request, "clientes/login.html", {"form": form})


def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect("clientes:painel")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Cadastro realizado com sucesso!")
        return redirect("clientes:painel")
    return render(request, "clientes/cadastro.html", {"form": form})


@login_required
def painel_view(request):
    perfil = getattr(request.user, "perfil", None)
    return render(request, "clientes/painel.html", {"perfil": perfil})


def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect("core:home")
"""

    files["clientes/admin.py"] = """
from django.contrib import admin

from config.admin import admin_site
from clientes.models import PerfilCliente


@admin.register(PerfilCliente, site=admin_site)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "user", "empresa", "telefone", "criado_em")
    search_fields = ("nome_completo", "user__username", "empresa", "documento")
"""

    files["clientes/urls.py"] = """
from django.urls import path

from clientes import views

app_name = "clientes"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("cadastro/", views.cadastro_view, name="cadastro"),
    path("painel/", views.painel_view, name="painel"),
    path("sair/", views.logout_view, name="logout"),
]
"""


    files["core/management/commands/seed_demo.py"] = """
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from blog.models import Categoria, Post
from core.models import ConfiguracaoSite, HistoriaEmpresa, SlideHero
from servicos.models import Servico


class Command(BaseCommand):
    help = "Popula dados de demonstração do site Rural Pro Amazônia"

    def handle(self, *args, **options):
        config = ConfiguracaoSite.load()
        config.nome_site = "Rural Pro Amazônia"
        config.slogan = "Soluções sustentáveis para o agronegócio na Amazônia"
        config.telefone = "(92) 3000-0000"
        config.whatsapp = "5592300000000"
        config.email = "contato@ruralproamazonia.com.br"
        config.endereco = "Av. Example, 1000 — Adrianópolis"
        config.cidade = "Manaus"
        config.estado = "AM"
        config.pilar_1_titulo = "Sustentabilidade"
        config.pilar_1_texto = "Práticas responsáveis que preservam a floresta e geram valor."
        config.pilar_2_titulo = "Inovação"
        config.pilar_2_texto = "Tecnologia e conhecimento aplicados ao campo amazônico."
        config.pilar_3_titulo = "Comunidade"
        config.pilar_3_texto = "Parcerias com produtores e cooperativas em toda a região."
        config.texto_rodape = "© Rural Pro Amazônia. Todos os direitos reservados."
        config.meta_description = "Consultoria e serviços para o agronegócio sustentável na Amazônia."
        config.save()

        historia = HistoriaEmpresa.load()
        historia.titulo = "Nossa história na Amazônia"
        historia.conteudo = (
            "<p>A <strong>Rural Pro Amazônia</strong> nasceu da união entre experiência técnica "
            "e compromisso com o desenvolvimento sustentável da região.</p>"
            "<p>Atuamos apoiando produtores rurais, cooperativas e empresas com consultoria, "
            "capacitação e soluções integradas para o campo.</p>"
        )
        historia.save()

        SlideHero.objects.all().delete()
        slides = [
            ("Agronegócio sustentável", "Tecnologia e respeito à floresta", "img/hero-1.png", "/servicos/", 1),
            ("Consultoria especializada", "Do planejamento à execução", "img/hero-2.png", "/contato/", 2),
            ("Fortalecendo comunidades", "Parcerias que transformam", "img/hero-3.png", "/blog/", 3),
        ]
        for titulo, subtitulo, img, link, ordem in slides:
            SlideHero.objects.create(
                titulo=titulo,
                subtitulo=subtitulo,
                imagem_estatica=img,
                link=link,
                ordem=ordem,
                ativo=True,
            )

        Servico.objects.all().delete()
        servicos_data = [
            ("Consultoria agrícola", "Planejamento de safra e manejo sustentável.", "servico-1.png", True, 1),
            ("Gestão ambiental", "Regularização e boas práticas ambientais.", "servico-2.png", True, 2),
            ("Capacitação rural", "Treinamentos presenciais e online.", "servico-3.png", True, 3),
        ]
        for titulo, resumo, img, destaque, ordem in servicos_data:
            Servico.objects.create(
                titulo=titulo,
                resumo=resumo,
                descricao=f"<p>{resumo}</p><p>Entre em contato para um diagnóstico personalizado.</p>",
                imagem_estatica=f"img/{img}",
                destaque=destaque,
                ativo=True,
                ordem=ordem,
            )
        cat, _ = Categoria.objects.get_or_create(slug="noticias", defaults={"nome": "Notícias"})
        Post.objects.all().delete()
        posts_data = [
            ("Novidades do setor na Amazônia", "Panorama das tendências para o agronegócio regional.", "blog-1.png"),
            ("Evento de capacitação rural", "Inscrições abertas para workshop gratuito.", "blog-2.png"),
            ("Parceria com cooperativas", "Ampliamos atendimento a produtores associados.", "blog-3.png"),
        ]
        for titulo, resumo, img in posts_data:
            Post.objects.create(
                titulo=titulo,
                resumo=resumo,
                conteudo=f"<p>{resumo}</p>",
                categoria=cat,
                imagem_estatica=f"img/{img}",
                destaque=True,
                publicado=True,
            )

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@ruralproamazonia.com.br", "admin123")

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados com sucesso."))
"""


    files["templates/base.html"] = """
{% load static %}
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}{{ site_config.nome_site|default:"Rural Pro Amazônia" }}{% endblock %}</title>
  {% if site_config and site_config.meta_description %}
  <meta name="description" content="{{ site_config.meta_description }}">
  {% endif %}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  {% include "partials/topbar.html" %}
  {% include "partials/header.html" %}
  {% if messages %}
  <div class="container messages-wrap">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }}">{{ message }}</div>
    {% endfor %}
  </div>
  {% endif %}
  <main>{% block content %}{% endblock %}</main>
  {% include "partials/footer.html" %}
  <script src="{% static 'js/main.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
"""

    files["templates/partials/topbar.html"] = """
<div class="topbar">
  <div class="container topbar-inner">
    <div class="topbar-contact">
      {% if site_config.telefone %}<span>Tel: {{ site_config.telefone }}</span>{% endif %}
      {% if site_config.email %}<span>{{ site_config.email }}</span>{% endif %}
    </div>
    <div class="topbar-links">
      <a href="{% url 'clientes:login' %}">Área do cliente</a>
      {% if site_config.instagram %}<a href="{{ site_config.instagram }}" target="_blank" rel="noopener">Instagram</a>{% endif %}
    </div>
  </div>
</div>
"""

    files["templates/partials/header.html"] = """
{% load static %}
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{% url 'core:home' %}">
      {% if site_config.logo %}
      <img src="{{ site_config.logo.url }}" alt="{{ site_config.nome_site }}">
      {% else %}
      <img src="{% static 'img/logo.png' %}" alt="Rural Pro Amazônia" onerror="this.style.display='none'">
      <span class="brand-text">{{ site_config.nome_site|default:"Rural Pro Amazônia" }}</span>
      {% endif %}
    </a>
    <button type="button" class="nav-toggle" aria-label="Abrir menu" data-nav-toggle>
      <span></span><span></span><span></span>
    </button>
    <nav class="main-nav" data-main-nav>
      <a href="{% url 'core:home' %}">Início</a>
      <a href="{% url 'servicos:lista' %}">Serviços</a>
      <a href="{% url 'blog:lista' %}">Blog</a>
      <a href="{% url 'contato:contato' %}">Contato</a>
      <a class="btn btn-sm btn-primary" href="{% url 'clientes:cadastro' %}">Cadastre-se</a>
    </nav>
  </div>
</header>
"""

    files["templates/partials/footer.html"] = """
<div class="footer-newsletter">
  <div class="container newsletter-inner">
    <div>
      <h3>Newsletter</h3>
      <p>Receba novidades sobre agronegócio sustentável na Amazônia.</p>
    </div>
    <form class="newsletter-form" action="#" method="post" onsubmit="return false;">
      <input type="email" placeholder="Seu e-mail" aria-label="E-mail">
      <button type="submit" class="btn btn-accent">Inscrever-se</button>
    </form>
  </div>
</div>
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <h4>{{ site_config.nome_site|default:"Rural Pro Amazônia" }}</h4>
      <p>{{ site_config.slogan }}</p>
    </div>
    <div>
      <h4>Contato</h4>
      <p>{{ site_config.endereco }}<br>{{ site_config.cidade }} — {{ site_config.estado }}</p>
      <p>{{ site_config.email }}</p>
    </div>
    <div>
      <h4>Links</h4>
      <ul class="footer-links">
        <li><a href="{% url 'servicos:lista' %}">Serviços</a></li>
        <li><a href="{% url 'blog:lista' %}">Blog</a></li>
        <li><a href="{% url 'contato:contato' %}">Fale conosco</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom container">
    <p>{{ site_config.texto_rodape|default:"© Rural Pro Amazônia" }}</p>
  </div>
</footer>
"""


    files["templates/partials/hero_carousel.html"] = """
<section class="hero-carousel" data-hero-carousel>
  <div class="hero-slides">
    {% for slide in slides %}
    <article class="hero-slide{% if forloop.first %} is-active{% endif %}" style="background-image:url('{{ slide.imagem_url }}')">
      <div class="container hero-content">
        <h1>{{ slide.titulo }}</h1>
        {% if slide.subtitulo %}<p>{{ slide.subtitulo }}</p>{% endif %}
        {% if slide.link %}
        <a href="{{ slide.link }}" class="btn btn-accent">{{ slide.texto_botao|default:"Saiba mais" }}</a>
        {% endif %}
      </div>
    </article>
    {% empty %}
    <article class="hero-slide is-active hero-slide--fallback">
      <div class="container hero-content">
        <h1>Rural Pro Amazônia</h1>
        <p>Soluções sustentáveis para o agronegócio</p>
        <a href="{% url 'contato:contato' %}" class="btn btn-accent">Fale conosco</a>
      </div>
    </article>
    {% endfor %}
  </div>
  {% if slides|length > 1 %}
  <div class="hero-dots" data-hero-dots>
    {% for slide in slides %}
    <button type="button" class="hero-dot{% if forloop.first %} is-active{% endif %}" aria-label="Slide {{ forloop.counter }}"></button>
    {% endfor %}
  </div>
  {% endif %}
</section>
"""

    files["templates/partials/pillars.html"] = """
<section class="section pillars">
  <div class="container">
    <header class="section-header">
      <h2>Nossos pilares</h2>
      <p>Compromisso com a Amazônia e com quem produz</p>
    </header>
    <div class="pillars-grid">
      <article class="pillar-card">
        <span class="pillar-icon">01</span>
        <h3>{{ site_config.pilar_1_titulo|default:"Sustentabilidade" }}</h3>
        <p>{{ site_config.pilar_1_texto }}</p>
      </article>
      <article class="pillar-card">
        <span class="pillar-icon">02</span>
        <h3>{{ site_config.pilar_2_titulo|default:"Inovação" }}</h3>
        <p>{{ site_config.pilar_2_texto }}</p>
      </article>
      <article class="pillar-card">
        <span class="pillar-icon">03</span>
        <h3>{{ site_config.pilar_3_titulo|default:"Comunidade" }}</h3>
        <p>{{ site_config.pilar_3_texto }}</p>
      </article>
    </div>
  </div>
</section>
"""

    files["templates/core/home.html"] = """
{% extends "base.html" %}
{% block content %}
{% include "partials/hero_carousel.html" %}
{% include "partials/pillars.html" %}
<section class="section">
  <div class="container">
    <header class="section-header">
      <h2>Serviços em destaque</h2>
      <a href="{% url 'servicos:lista' %}" class="link-more">Ver todos</a>
    </header>
    <div class="cards-grid">
      {% for servico in servicos_destaque %}
      <article class="card card-service">
        <div class="card-image" style="background-image:url('{{ servico.imagem_url }}')"></div>
        <div class="card-body">
          <h3><a href="{% url 'servicos:detalhe' servico.slug %}">{{ servico.titulo }}</a></h3>
          <p>{{ servico.resumo|truncatewords:20 }}</p>
          <a href="{% url 'servicos:detalhe' servico.slug %}" class="link-more">Saiba mais</a>
        </div>
      </article>
      {% empty %}
      <p>Cadastre serviços no painel administrativo.</p>
      {% endfor %}
    </div>
  </div>
</section>
<section class="section section-alt">
  <div class="container about-split">
    <div class="about-text">
      <h2>{{ historia.titulo }}</h2>
      <div class="richtext">{{ historia.conteudo|safe }}</div>
      <a href="{% url 'contato:contato' %}" class="btn btn-primary">Entre em contato</a>
    </div>
    <div class="about-image" style="background-image:url('{% if historia.imagem %}{{ historia.imagem.url }}{% else %}/static/img/servico-2.png{% endif %}')"></div>
  </div>
</section>
<section class="section">
  <div class="container">
    <header class="section-header">
      <h2>Blog</h2>
      <a href="{% url 'blog:lista' %}" class="link-more">Ver todas as notícias</a>
    </header>
    <div class="cards-grid">
      {% for post in posts_destaque %}
      <article class="card card-blog">
        <div class="card-image" style="background-image:url('{{ post.imagem_url }}')"></div>
        <div class="card-body">
          {% if post.categoria %}<span class="tag">{{ post.categoria.nome }}</span>{% endif %}
          <h3>
            {% if post.link_externo %}
            <a href="{{ post.link_externo }}" target="_blank" rel="noopener">{{ post.titulo }}</a>
            {% else %}
            <a href="{% url 'blog:detalhe' post.slug %}">{{ post.titulo }}</a>
            {% endif %}
          </h3>
          <p>{{ post.resumo|truncatewords:18 }}</p>
        </div>
      </article>
      {% endfor %}
    </div>
  </div>
</section>
{% endblock %}
"""


    files["templates/servicos/lista.html"] = """
{% extends "base.html" %}
{% block title %}Serviços — {{ block.super }}{% endblock %}
{% block content %}
<section class="page-hero">
  <div class="container">
    <h1>Serviços</h1>
    <p>Soluções completas para o agronegócio amazônico</p>
  </div>
</section>
<section class="section">
  <div class="container cards-grid">
    {% for servico in servicos %}
    <article class="card card-service">
      <div class="card-image" style="background-image:url('{{ servico.imagem_url }}')"></div>
      <div class="card-body">
        <h2><a href="{% url 'servicos:detalhe' servico.slug %}">{{ servico.titulo }}</a></h2>
        <p>{{ servico.resumo }}</p>
        <a class="btn btn-outline" href="{% url 'servicos:detalhe' servico.slug %}">Detalhes</a>
      </div>
    </article>
    {% empty %}
    <p>Nenhum serviço disponível no momento.</p>
    {% endfor %}
  </div>
</section>
{% endblock %}
"""

    files["templates/servicos/detalhe.html"] = """
{% extends "base.html" %}
{% block title %}{{ servico.titulo }} — {{ block.super }}{% endblock %}
{% block content %}
<section class="page-hero page-hero--compact">
  <div class="container">
    <h1>{{ servico.titulo }}</h1>
    <p>{{ servico.resumo }}</p>
  </div>
</section>
<section class="section">
  <div class="container detail-layout">
    <div class="detail-image" style="background-image:url('{{ servico.imagem_url }}')"></div>
    <div class="richtext">{{ servico.descricao|safe }}</div>
  </div>
  {% if relacionados %}
  <div class="container section-top">
    <h2>Outros serviços</h2>
    <div class="cards-grid cards-grid--3">
      {% for s in relacionados %}
      <article class="card card-service">
        <div class="card-body">
          <h3><a href="{% url 'servicos:detalhe' s.slug %}">{{ s.titulo }}</a></h3>
        </div>
      </article>
      {% endfor %}
    </div>
  </div>
  {% endif %}
</section>
{% endblock %}
"""

    files["templates/blog/lista.html"] = """
{% extends "base.html" %}
{% block title %}Blog — {{ block.super }}{% endblock %}
{% block content %}
<section class="page-hero">
  <div class="container">
    <h1>Blog</h1>
    <p>Notícias e conteúdos sobre agronegôcio na Amazônia</p>
  </div>
</section>
<section class="section">
  <div class="container cards-grid">
    {% for post in posts %}
    <article class="card card-blog">
      <div class="card-image" style="background-image:url('{{ post.imagem_url }}')"></div>
      <div class="card-body">
        <time datetime="{{ post.publicado_em|date:'c' }}">{{ post.publicado_em|date:'d/m/Y' }}</time>
        <h2>
          {% if post.link_externo %}
          <a href="{{ post.link_externo }}" target="_blank" rel="noopener">{{ post.titulo }}</a>
          {% else %}
          <a href="{% url 'blog:detalhe' post.slug %}">{{ post.titulo }}</a>
          {% endif %}
        </h2>
        <p>{{ post.resumo|truncatewords:25 }}</p>
      </div>
    </article>
    {% empty %}
    <p>Nenhuma publicação encontrada.</p>
    {% endfor %}
  </div>
  {% if posts.has_other_pages %}
  <nav class="pagination container">
    {% if posts.has_previous %}<a href="?page={{ posts.previous_page_number }}">Anterior</a>{% endif %}
    <span>Página {{ posts.number }} de {{ posts.paginator.num_pages }}</span>
    {% if posts.has_next %}<a href="?page={{ posts.next_page_number }}">Próxima</a>{% endif %}
  </nav>
  {% endif %}
</section>
{% endblock %}
"""

    files["templates/blog/detalhe.html"] = """
{% extends "base.html" %}
{% block title %}{{ post.titulo }} — {{ block.super }}{% endblock %}
{% block content %}
<article class="section">
  <div class="container post-detail">
    <header>
      <time datetime="{{ post.publicado_em|date:'c' }}">{{ post.publicado_em|date:'d/m/Y' }}</time>
      <h1>{{ post.titulo }}</h1>
      <p class="lead">{{ post.resumo }}</p>
    </header>
    <div class="post-cover" style="background-image:url('{{ post.imagem_url }}')"></div>
    <div class="richtext">{{ post.conteudo|safe }}</div>
  </div>
  {% if recentes %}
  <div class="container section-top">
    <h2>Leia também</h2>
    <ul class="recent-list">
      {% for p in recentes %}
      <li><a href="{% url 'blog:detalhe' p.slug %}">{{ p.titulo }}</a></li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}
</article>
{% endblock %}
"""

    files["templates/contato/contato.html"] = """
{% extends "base.html" %}
{% block title %}Contato — {{ block.super }}{% endblock %}
{% block content %}
<section class="page-hero">
  <div class="container">
    <h1>Contato</h1>
    <p>Envie sua mensagem — responderemos o mais breve possível</p>
  </div>
</section>
<section class="section">
  <div class="container contact-grid">
    <div class="contact-info">
      <h2>Fale conosco</h2>
      <p><strong>Telefone:</strong> {{ site_config.telefone }}</p>
      <p><strong>E-mail:</strong> {{ site_config.email }}</p>
      <p><strong>Endereço:</strong> {{ site_config.endereco }}, {{ site_config.cidade }} — {{ site_config.estado }}</p>
    </div>
    <form method="post" class="contact-form" novalidate>
      {% csrf_token %}
      {{ form.non_field_errors }}
      {% for field in form %}
      <div class="form-group">
        <label for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {{ field.errors }}
      </div>
      {% endfor %}
      <button type="submit" class="btn btn-primary">Enviar mensagem</button>
    </form>
  </div>
</section>
{% endblock %}
"""


    files["templates/clientes/login.html"] = """
{% extends "base.html" %}
{% block title %}Login — {{ block.super }}{% endblock %}
{% block content %}
<section class="section auth-section">
  <div class="container auth-card">
    <h1>Área do cliente</h1>
    <form method="post">
      {% csrf_token %}
      {{ form.non_field_errors }}
      {% for field in form %}
      <div class="form-group">
        <label for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {{ field.errors }}
      </div>
      {% endfor %}
      <button type="submit" class="btn btn-primary">Entrar</button>
    </form>
    <p class="auth-alt">Ainda não tem conta? <a href="{% url 'clientes:cadastro' %}">Cadastre-se</a></p>
  </div>
</section>
{% endblock %}
"""

    files["templates/clientes/cadastro.html"] = """
{% extends "base.html" %}
{% block title %}Cadastro — {{ block.super }}{% endblock %}
{% block content %}
<section class="section auth-section">
  <div class="container auth-card auth-card--wide">
    <h1>Criar conta</h1>
    <form method="post">
      {% csrf_token %}
      {{ form.non_field_errors }}
      {% for field in form %}
      <div class="form-group">
        <label for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {{ field.errors }}
      </div>
      {% endfor %}
      <button type="submit" class="btn btn-primary">Cadastrar</button>
    </form>
    <p class="auth-alt">Já possui conta? <a href="{% url 'clientes:login' %}">Faça login</a></p>
  </div>
</section>
{% endblock %}
"""

    files["templates/clientes/painel.html"] = """
{% extends "base.html" %}
{% block title %}Painel — {{ block.super }}{% endblock %}
{% block content %}
<section class="section">
  <div class="container auth-card">
    <h1>Olá, {{ user.get_full_name|default:user.username }}</h1>
    {% if perfil %}
    <ul class="profile-list">
      <li><strong>Nome:</strong> {{ perfil.nome_completo }}</li>
      {% if perfil.empresa %}<li><strong>Empresa:</strong> {{ perfil.empresa }}</li>{% endif %}
      {% if perfil.telefone %}<li><strong>Telefone:</strong> {{ perfil.telefone }}</li>{% endif %}
    </ul>
    {% endif %}
    <p>Bem-vindo à área do cliente Rural Pro Amazônia.</p>
    <a href="{% url 'clientes:logout' %}" class="btn btn-outline">Sair</a>
  </div>
</section>
{% endblock %}
"""


    files["static/css/main.css"] = """
:root {
  --green: #1B5E20;
  --green-dark: #0D3B1E;
  --charcoal: #2C2C2C;
  --cream: #FAF8F5;
  --blue: #2E86AB;
  --yellow: #E8B923;
  --white: #ffffff;
  --shadow: 0 8px 24px rgba(13, 59, 30, 0.12);
  --radius: 8px;
  --font: \"Source Sans 3\", system-ui, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font);
  color: var(--charcoal);
  background: var(--cream);
  line-height: 1.6;
}
img { max-width: 100%; height: auto; }
a { color: var(--green); text-decoration: none; }
a:hover { color: var(--blue); }
.container { width: min(1140px, 92vw); margin-inline: auto; }

.topbar {
  background: var(--green-dark);
  color: var(--cream);
  font-size: 0.875rem;
}
.topbar-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.45rem 0;
  flex-wrap: wrap;
}
.topbar a { color: var(--yellow); margin-left: 1rem; }
.topbar-contact span { margin-right: 1rem; }

.site-header {
  background: var(--white);
  box-shadow: 0 2px 0 rgba(27, 94, 32, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 0;
  gap: 1rem;
}
.brand { display: flex; align-items: center; gap: 0.75rem; font-weight: 700; color: var(--green-dark); }
.brand img { height: 48px; width: auto; }
.brand-text { font-size: 1.15rem; }
.main-nav { display: flex; align-items: center; gap: 1.25rem; }
.main-nav a { font-weight: 600; color: var(--charcoal); }
.nav-toggle {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: 0;
  cursor: pointer;
}
.nav-toggle span { display: block; width: 24px; height: 2px; background: var(--green-dark); }

.btn {
  display: inline-block;
  padding: 0.65rem 1.25rem;
  border-radius: var(--radius);
  font-weight: 600;
  border: 2px solid transparent;
  cursor: pointer;
  transition: 0.2s ease;
}
.btn-sm { padding: 0.4rem 0.9rem; font-size: 0.9rem; }
.btn-primary { background: var(--green); color: var(--white); }
.btn-primary:hover { background: var(--green-dark); color: var(--white); }
.btn-accent { background: var(--yellow); color: var(--green-dark); }
.btn-accent:hover { filter: brightness(1.05); color: var(--green-dark); }
.btn-outline { border-color: var(--green); color: var(--green); background: transparent; }

.hero-carousel { position: relative; overflow: hidden; background: var(--green-dark); }
.hero-slide {
  min-height: clamp(320px, 55vh, 520px);
  background-size: cover;
  background-position: center;
  display: none;
  align-items: center;
  position: relative;
}
.hero-slide.is-active { display: flex; }
.hero-slide::before {
  content: \"\";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(13,59,30,0.85), rgba(13,59,30,0.35));
}
.hero-content { position: relative; z-index: 1; color: var(--white); padding: 3rem 0; max-width: 640px; }
.hero-content h1 { font-size: clamp(1.75rem, 4vw, 2.75rem); margin: 0 0 0.75rem; line-height: 1.15; }
.hero-content p { font-size: 1.125rem; margin-bottom: 1.25rem; opacity: 0.95; }
.hero-dots {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.5rem;
  z-index: 2;
}
.hero-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 0;
  background: rgba(255,255,255,0.45);
  cursor: pointer;
}
.hero-dot.is-active { background: var(--yellow); }

.section { padding: 3.5rem 0; }
.section-alt { background: var(--white); }
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.section-header h2 { margin: 0; color: var(--green-dark); font-size: 1.75rem; }
.link-more { font-weight: 600; color: var(--blue); }

.pillars-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}
.pillar-card {
  background: var(--white);
  padding: 1.75rem;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border-top: 4px solid var(--green);
}
.pillar-icon { font-weight: 700; color: var(--yellow); font-size: 1.25rem; }

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}
.card {
  background: var(--white);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
}
.card-image {
  height: 180px;
  background-size: cover;
  background-position: center;
  background-color: var(--green-dark);
}
.card-body { padding: 1.25rem; flex: 1; }
.tag {
  display: inline-block;
  font-size: 0.75rem;
  background: rgba(46, 134, 171, 0.15);
  color: var(--blue);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.about-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: center;
}
.about-image {
  min-height: 280px;
  border-radius: var(--radius);
  background-size: cover;
  background-position: center;
  background-color: var(--green);
}

.page-hero {
  background: linear-gradient(135deg, var(--green-dark), var(--green));
  color: var(--white);
  padding: 2.5rem 0;
}
.contact-grid, .detail-layout {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 2rem;
}
.form-group { margin-bottom: 1rem; }
.form-control {
  width: 100%;
  padding: 0.65rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: var(--radius);
  font: inherit;
}

.auth-card {
  max-width: 420px;
  margin: 0 auto;
  background: var(--white);
  padding: 2rem;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.footer-newsletter { background: var(--blue); color: var(--white); padding: 2rem 0; }
.site-footer { background: var(--charcoal); color: #e8e8e8; padding: 2.5rem 0 0; }
.footer-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; }

@media (max-width: 900px) {
  .pillars-grid, .about-split, .detail-layout, .contact-grid, .footer-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .nav-toggle { display: flex; }
  .main-nav {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--white);
    flex-direction: column;
    padding: 1rem;
    box-shadow: var(--shadow);
    display: none;
  }
  .main-nav.is-open { display: flex; }
  .site-header, .header-inner { position: relative; }
}
"""


    files["static/js/main.js"] = """
(function () {
  \"use strict\";

  var navToggle = document.querySelector(\"[data-nav-toggle]\");
  var mainNav = document.querySelector(\"[data-main-nav]\");
  if (navToggle && mainNav) {
    navToggle.addEventListener(\"click\", function () {
      mainNav.classList.toggle(\"is-open\");
    });
  }

  var carousel = document.querySelector(\"[data-hero-carousel]\");
  if (!carousel) return;

  var slides = carousel.querySelectorAll(\".hero-slide\");
  var dots = carousel.querySelectorAll(\".hero-dot\");
  if (slides.length <= 1) return;

  var index = 0;
  var timer;

  function show(i) {
    index = (i + slides.length) % slides.length;
    slides.forEach(function (slide, idx) {
      slide.classList.toggle(\"is-active\", idx === index);
    });
    dots.forEach(function (dot, idx) {
      dot.classList.toggle(\"is-active\", idx === index);
    });
  }

  function next() {
    show(index + 1);
  }

  function start() {
    stop();
    timer = setInterval(next, 6000);
  }

  function stop() {
    if (timer) clearInterval(timer);
  }

  dots.forEach(function (dot, idx) {
    dot.addEventListener(\"click\", function () {
      show(idx);
      start();
    });
  });

  carousel.addEventListener(\"mouseenter\", stop);
  carousel.addEventListener(\"mouseleave\", start);
  start();
})();
"""

    files["README.md"] = """
# Rural Pro Amazônia

Site institucional em Django para a **Rural Pro Amazônia**, com foco em agronegócio sustentável na região Amazônica. Layout inspirado em portais setoriais (topbar, header, hero em carrossel, pilares, cards de serviços e blog).

## Requisitos

- Python 3.10+
- pip

## Instalação

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

## Banco de dados e conteúdo demo

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
```

## Executar

```bash
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`. Painel admin: `/admin/` (após `seed_demo`: usuário `admin`, senha `admin123` — altere em produção).

## Gerar arquivos do projeto

Se precisar recriar templates e apps a partir do gerador:

```bash
python _build_site.py
```

## Estrutura

- `core/` — home, slides, configuração do site, história
- `servicos/` — listagem e detalhe de serviços
- `blog/` — posts e categorias
- `contato/` — formulário de mensagens
- `clientes/` — cadastro, login e painel do cliente
- `templates/` e `static/` — front-end institucional

## Licença

Uso interno / projeto institucional Rural Pro Amazônia.
"""

    return files


def main() -> None:
    print("Rural Pro Amazônia — gerando arquivos...")
    copy_static_images()
    for rel, content in build_files().items():
        write(rel, content)
    print("Concluído.")


if __name__ == "__main__":
    main()



