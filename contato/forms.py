from django import forms
import re

from contato.models import InscricaoWhatsApp, MensagemContato


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



class WhatsAppInscricaoForm(forms.ModelForm):
    class Meta:
        model = InscricaoWhatsApp
        fields = ("telefone",)
        widgets = {
            "telefone": forms.TextInput(
                attrs={
                    "class": "newsletter-input",
                    "placeholder": "Seu WhatsApp (DDD + número)",
                    "inputmode": "tel",
                    "autocomplete": "tel",
                    "aria-label": "WhatsApp",
                }
            ),
        }

    def clean_telefone(self):
        telefone = re.sub(r"\D", "", self.cleaned_data.get("telefone", ""))
        if len(telefone) not in (10, 11):
            raise forms.ValidationError("Informe um WhatsApp válido com DDD (10 ou 11 dígitos).")
        if len(telefone) == 11 and telefone[2] != "9":
            raise forms.ValidationError("WhatsApp celular deve começar com 9 após o DDD.")
        return telefone
