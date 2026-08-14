import re

from django import forms


class ConsultaCARForm(forms.Form):
    numero_car = forms.CharField(
        label="Código CAR",
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "UF-GEOCÓDIGO-CÓDIGOdoIMÓVEL (ex.: AC-1200450-...)",
                "autocomplete": "off",
            }
        ),
        help_text="Informe o código CAR completo do imóvel no Acre (Selo Verde AC).",
    )

    def clean_numero_car(self):
        valor = self.cleaned_data["numero_car"].strip().upper()
        if not valor:
            raise forms.ValidationError("Informe o código CAR.")
        if not re.match(r"^[A-Z]{2}-", valor):
            raise forms.ValidationError("O CAR deve começar com a UF, ex.: AC-1200450-...")
        return valor
