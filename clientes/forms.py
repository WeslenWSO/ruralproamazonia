from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from clientes.models import PerfilCliente


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "seu@email.com", "autocomplete": "email"}
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Sua senha", "autocomplete": "current-password"}
        ),
    )

    def clean(self):
        email = self.cleaned_data.get("username")
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                self.cleaned_data["username"] = user.username
        return super().clean()


class CadastroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "seu@email.com", "autocomplete": "email"}
        ),
    )
    nome_completo = forms.CharField(
        max_length=150,
        label="Nome completo",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )
    empresa = forms.CharField(
        max_length=150,
        required=False,
        label="Empresa",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    telefone = forms.CharField(
        max_length=30,
        required=False,
        label="Telefone",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel"}),
    )
    documento = forms.CharField(
        max_length=20,
        required=False,
        label="Documento",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    field_order = ["email", "password1", "password2", "nome_completo", "empresa", "telefone", "documento"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = forms.HiddenInput()
        self.fields["username"].required = False
        self.fields["password1"].label = "Senha"
        self.fields["password2"].label = "Confirmação de senha"
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "form-control", "autocomplete": "new-password"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def _gerar_username(self, email):
        base = email.split("@")[0].replace(".", "_")[:30] or "cliente"
        username = base
        n = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{n}"
            n += 1
        return username

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        if email and not cleaned.get("username"):
            cleaned["username"] = self._gerar_username(email)
        return cleaned

    def save(self, commit=True):
        email = self.cleaned_data["email"].strip().lower()
        self.cleaned_data["username"] = self._gerar_username(email)
        user = super().save(commit=False)
        user.email = email
        user.username = self.cleaned_data["username"]
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
