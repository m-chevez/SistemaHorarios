from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Aula, Clase, Docente


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class DocenteForm(StyledModelForm):
    class Meta:
        model = Docente
        fields = ('id', 'nombre', 'apellido')


class ClaseForm(StyledModelForm):
    class Meta:
        model = Clase
        fields = ('id', 'clase', 'uv', 'cantidadEM')


class AulaForm(StyledModelForm):
    class Meta:
        model = Aula
        fields = ('idAula', 'nombreAula', 'tipo', 'capacidad')


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        max_length=150,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password
