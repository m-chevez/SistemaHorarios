import io
import random

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from .forms import AulaForm, ClaseForm, DocenteForm, RegistrationForm
from .models import Aula, Clase, Docente, Horario


def index(request):
    return render(request, 'index.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user_model = get_user_model()
        account = user_model.objects.filter(email__iexact=email).first()
        username = account.get_username() if account else email
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Sesión iniciada correctamente.')
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('home')
        messages.error(request, 'El correo o la contraseña no son válidos.')

    return render(request, 'login.html', {'next': next_url})


def iniciar(request):
    return login_view(request)


@require_POST
def cerrar_sesion(request):
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('index')


def registrarUsuario(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        get_user_model().objects.create_user(
            username=email,
            email=email,
            password=form.cleaned_data['password'],
        )
        messages.success(request, 'Cuenta creada. Ya puedes iniciar sesión.')
        return redirect('login')

    if request.method == 'POST':
        messages.error(request, 'Revisa los datos del formulario.')
    return render(request, 'registrarUsuario.html', {'form': form})


@login_required
def home(request):
    return render(request, 'home.html')


@login_required
def formDocente(request):
    return render(request, 'formDocente.html', {'lista': Docente.objects.all()})


@login_required
def docente(request):
    return redirect('formDocente')


@login_required
def create_docente(request):
    return render(request, 'create.html', {'form': DocenteForm()})


@login_required
@require_POST
def insert_docente(request):
    form = DocenteForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Docente creado correctamente.')
        return redirect('formDocente')
    messages.error(request, 'No se pudo crear el docente. Revisa los datos.')
    return render(request, 'create.html', {'form': form}, status=400)


@login_required
def edit_docente(request):
    docente_obj = get_object_or_404(Docente, pk=request.GET.get('id'))
    form = DocenteForm(instance=docente_obj)
    form.fields['id'].disabled = True
    return render(
        request,
        'edit.html',
        {'docente': docente_obj, 'form': form},
    )


@login_required
@require_POST
def update_docente(request):
    docente_obj = get_object_or_404(Docente, pk=request.POST.get('id'))
    form = DocenteForm(request.POST, instance=docente_obj)
    form.fields['id'].disabled = True
    if form.is_valid():
        form.save()
        messages.success(request, 'Docente actualizado correctamente.')
        return redirect('formDocente')
    messages.error(request, 'No se pudo actualizar el docente. Revisa los datos.')
    return render(
        request,
        'edit.html',
        {'docente': docente_obj, 'form': form},
        status=400,
    )


@login_required
def remove_docente(request):
    docente_obj = get_object_or_404(Docente, pk=request.GET.get('id'))
    return render(request, 'remove.html', {'docente': docente_obj})


@login_required
@require_POST
def delete_docente(request):
    docente_obj = get_object_or_404(Docente, pk=request.POST.get('id'))
    docente_obj.delete()
    messages.success(request, 'Docente eliminado correctamente.')
    return redirect('formDocente')


@login_required
def formClase(request):
    return render(request, 'formClase.html', {'lista': Clase.objects.all()})


@login_required
def clase(request):
    return redirect('formClase')


@login_required
def create_clase(request):
    return render(request, 'createClase.html', {'form': ClaseForm()})


@login_required
@require_POST
def insert_clase(request):
    form = ClaseForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Clase creada correctamente.')
        return redirect('formClase')
    messages.error(request, 'No se pudo crear la clase. Revisa los datos.')
    return render(request, 'createClase.html', {'form': form}, status=400)


@login_required
def edit_clase(request):
    clase_obj = get_object_or_404(Clase, pk=request.GET.get('id'))
    form = ClaseForm(instance=clase_obj)
    form.fields['id'].disabled = True
    return render(
        request,
        'editClase.html',
        {'clase': clase_obj, 'form': form},
    )


@login_required
@require_POST
def update_clase(request):
    clase_obj = get_object_or_404(Clase, pk=request.POST.get('id'))
    form = ClaseForm(request.POST, instance=clase_obj)
    form.fields['id'].disabled = True
    if form.is_valid():
        form.save()
        messages.success(request, 'Clase actualizada correctamente.')
        return redirect('formClase')
    messages.error(request, 'No se pudo actualizar la clase. Revisa los datos.')
    return render(
        request,
        'editClase.html',
        {'clase': clase_obj, 'form': form},
        status=400,
    )


@login_required
def remove_clase(request):
    clase_obj = get_object_or_404(Clase, pk=request.GET.get('id'))
    return render(request, 'removeClase.html', {'clase': clase_obj})


@login_required
@require_POST
def delete_clase(request):
    clase_obj = get_object_or_404(Clase, pk=request.POST.get('id'))
    clase_obj.delete()
    messages.success(request, 'Clase eliminada correctamente.')
    return redirect('formClase')


@login_required
def aulas(request):
    return render(request, 'aulas.html', {'lista': Aula.objects.all()})


@login_required
def crear_aula(request):
    return render(request, 'aula_form.html', {'form': AulaForm()})


@login_required
@require_POST
def insertar_aula(request):
    form = AulaForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Aula creada correctamente.')
        return redirect('aulas')
    messages.error(request, 'No se pudo crear el aula. Revisa los datos.')
    return render(request, 'aula_form.html', {'form': form}, status=400)


@login_required
def editar_aula(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    form = AulaForm(instance=aula)
    form.fields['idAula'].disabled = True
    return render(
        request,
        'aula_form.html',
        {'aula': aula, 'form': form},
    )


@login_required
@require_POST
def actualizar_aula(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    form = AulaForm(request.POST, instance=aula)
    form.fields['idAula'].disabled = True
    if form.is_valid():
        form.save()
        messages.success(request, 'Aula actualizada correctamente.')
        return redirect('aulas')
    messages.error(request, 'No se pudo actualizar el aula. Revisa los datos.')
    return render(request, 'aula_form.html', {'aula': aula, 'form': form}, status=400)


@login_required
def eliminar_aula(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    return render(request, 'aula_confirm_delete.html', {'aula': aula})


@login_required
@require_POST
def confirmar_eliminar_aula(request, pk):
    aula = get_object_or_404(Aula, pk=pk)
    aula.delete()
    messages.success(request, 'Aula eliminada correctamente.')
    return redirect('aulas')


@login_required
def generarHorario(request):
    clases = list(Clase.objects.all())
    docentes = list(Docente.objects.all())
    aulas_disponibles = list(Aula.objects.all())

    if not clases:
        messages.warning(request, 'Primero registra al menos una clase.')
    elif not docentes or not aulas_disponibles:
        messages.error(request, 'Registra al menos un docente y un aula para generar el horario.')
    else:
        clases.sort(key=lambda clase_obj: (-clase_obj.cantidadEM, clase_obj.pk))
        asignaciones = []
        ocupacion = {}
        clases_sin_espacio = []
        for clase_obj in clases:
            for hora in range(7, 19):
                hora_ocupada = ocupacion.setdefault(
                    hora,
                    {'docentes': set(), 'aulas': set()},
                )
                docentes_disponibles = [
                    docente for docente in docentes
                    if docente.pk not in hora_ocupada['docentes']
                ]
                aulas_disponibles_para_clase = [
                    aula for aula in aulas_disponibles
                    if aula.pk not in hora_ocupada['aulas']
                    and aula.capacidad >= clase_obj.cantidadEM
                ]
                if docentes_disponibles and aulas_disponibles_para_clase:
                    docente = random.choice(docentes_disponibles)
                    aula = random.choice(aulas_disponibles_para_clase)
                    asignaciones.append(
                        Horario(
                            idClase=clase_obj,
                            idDocente=docente,
                            idAula=aula,
                            hora=hora,
                        ),
                    )
                    hora_ocupada['docentes'].add(docente.pk)
                    hora_ocupada['aulas'].add(aula.pk)
                    break
            else:
                clases_sin_espacio.append(clase_obj)

        if clases_sin_espacio:
            messages.error(
                request,
                'No hay suficientes docentes, espacios horarios o aulas con capacidad '
                f'adecuada para asignar {len(clases_sin_espacio)} clase(s).',
            )
        else:
            with transaction.atomic():
                Horario.objects.all().delete()
                Horario.objects.bulk_create(asignaciones)
            messages.success(request, 'Horario generado correctamente.')

    return _render_horario(request, Horario.objects.select_related(
        'idClase', 'idDocente', 'idAula',
    ))


def _horario_filtrado(request):
    horario = Horario.objects.select_related('idClase', 'idDocente', 'idAula')
    hora = request.GET.get('hora', '').strip()
    if hora:
        try:
            hora_numero = int(hora)
        except ValueError:
            messages.error(request, 'La hora debe ser un número entre 7 y 18.')
            return horario.none()
        if not 7 <= hora_numero <= 18:
            messages.error(request, 'La hora debe estar entre 7 y 18.')
            return horario.none()
        horario = horario.filter(hora=hora_numero)

    docente = request.GET.get('docente', '').strip()
    clase = request.GET.get('clase', '').strip()
    aula = request.GET.get('aula', '').strip()
    if docente:
        horario = horario.filter(idDocente_id=docente)
    if clase:
        horario = horario.filter(idClase_id=clase)
    if aula:
        horario = horario.filter(idAula_id=aula)
    return horario


@login_required
def filtrarHorario(request):
    return _render_horario(request, _horario_filtrado(request))


def _render_horario(request, horario):
    return render(
        request,
        'horario.html',
        {'horario': horario, 'horas': range(7, 19), 'dias': range(5)},
    )


@login_required
def descargarHorario(request):
    html_string = render_to_string(
        'horario_pdf.html',
        {
            'horario': _horario_filtrado(request),
            'horas': range(7, 19),
            'dias': range(5),
        },
        request=request,
    )
    result = io.BytesIO()
    pdf_status = pisa.CreatePDF(io.StringIO(html_string), dest=result)
    if pdf_status.err:
        messages.error(request, 'No se pudo generar el PDF del horario.')
        return redirect('filtrarHorario')
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="horario.pdf"'
    return response
