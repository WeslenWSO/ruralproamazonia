from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from clientes.forms import CadastroForm, LoginForm

AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


def login_view(request):
    if request.user.is_authenticated:
        return redirect("clientes:painel")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user(), backend=AUTH_BACKEND)
        return redirect("clientes:painel")
    return render(request, "clientes/login.html", {"form": form})


def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect("clientes:painel")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend=AUTH_BACKEND)
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
