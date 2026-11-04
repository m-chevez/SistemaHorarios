from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Aula, CensoEstudiante, Clase, Docente, Estudiante, PreferenciaDocenteClase


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class DocenteForm(StyledModelForm):
    class Meta:
        model = Docente
        fields = (
            'id',
            'nombre',
            'apellido',
            'carga_maxima_uv',
            'hora_inicio',
            'hora_fin',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['carga_maxima_uv'].required = True
        self.fields['hora_inicio'].required = False
        self.fields['hora_fin'].required = False
        self.fields['carga_maxima_uv'].help_text = (
            'Límite total de UV que el algoritmo podrá asignar a este docente.'
        )

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('hora_inicio')
        fin = cleaned.get('hora_fin')
        if inicio is not None and fin is not None and fin <= inicio:
            self.add_error('hora_fin', 'La hora de fin debe ser mayor que la hora de inicio.')
        return cleaned


class PreferenciaDocenteClaseForm(StyledModelForm):
    class Meta:
        model = PreferenciaDocenteClase
        fields = ('clase', 'prioridad')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clase'].widget.attrs['class'] = 'form-select'
        self.fields['prioridad'].widget.attrs['class'] = 'form-select'


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


class EstudianteIdentificacionForm(forms.Form):
    numero_cuenta = forms.CharField(
        max_length=30,
        label='Número de cuenta',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej. 20211001234',
            'autocomplete': 'off',
            'required': True,
        }),
    )
    nombre = forms.CharField(
        max_length=150,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej. Juan Carlos Pérez',
            'autocomplete': 'name',
            'required': True,
        }),
    )

    def clean_numero_cuenta(self):
        return self.cleaned_data['numero_cuenta'].strip()

    def clean_nombre(self):
        return self.cleaned_data['nombre'].strip()


class CensoEstudianteForm(forms.ModelForm):
    class Meta:
        model = CensoEstudiante
        fields = ('clase', 'hora_tentativa')
        widgets = {
            'clase': forms.Select(attrs={'class': 'form-select'}),
            'hora_tentativa': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '7',
                'max': '18',
                'placeholder': '7 a 18',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clase'].empty_label = '--- Selecciona una clase ---'
        self.fields['hora_tentativa'].label = 'Horario tentativo (7:00 a 18:00)'
