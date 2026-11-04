import io
import random

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from .excel_export import generar_excel_horario
from .forms import (
    AulaForm,
    CensoEstudianteForm,
    ClaseForm,
    DocenteForm,
    EstudianteIdentificacionForm,
    PreferenciaDocenteClaseForm,
    RegistrationForm,
)
from .genetic_algorithm import (
    AulaData,
    CensoEntry,
    ClaseData,
    DocenteData,
    GeneticScheduleOptimizer,
)
from .models import (
    Aula,
    CensoEstudiante,
    Clase,
    Docente,
    Estudiante,
    Horario,
    PreferenciaDocenteClase,
)


def index(request):
    total_docentes = Docente.objects.count()
    total_clases = Clase.objects.count()
    total_aulas = Aula.objects.count()
    total_estudiantes_censo = Estudiante.objects.count()
    total_horarios = Horario.objects.count()
    return render(request, 'index.html', {
        'total_docentes': total_docentes,
        'total_clases': total_clases,
        'total_aulas': total_aulas,
        'total_estudiantes_censo': total_estudiantes_censo,
        'total_horarios': total_horarios,
    })


# ─── Autenticación de Coordinador ──────────────────────────────────────────

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
            messages.success(request, f'Bienvenido(a), {user.email or user.username}.')
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
    messages.success(request, 'Sesión de coordinador cerrada correctamente.')
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
        messages.success(request, 'Cuenta de coordinador creada. Ya puedes iniciar sesión.')
        return redirect('login')

    if request.method == 'POST':
        messages.error(request, 'Revisa los datos del formulario.')
    return render(request, 'registrarUsuario.html', {'form': form})


# ─── Portal de Estudiantes y Censo ─────────────────────────────────────────

def estudiante_login(request):
    """Inicio de sesión e identificación de estudiantes con Cuenta y Nombre."""
    if request.session.get('estudiante_cuenta'):
        return redirect('estudiante_censo')

    form = EstudianteIdentificacionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cuenta = form.cleaned_data['numero_cuenta']
        nombre = form.cleaned_data['nombre']

        estudiante, created = Estudiante.objects.get_or_create(
            numero_cuenta=cuenta,
            defaults={'nombre': nombre},
        )
        if not created and estudiante.nombre != nombre:
            estudiante.nombre = nombre
            estudiante.save(update_fields=['nombre'])

        request.session['estudiante_cuenta'] = estudiante.numero_cuenta
        request.session['estudiante_nombre'] = estudiante.nombre

        if created:
            messages.success(request, f'¡Bienvenido(a) {nombre}! Tu registro ha sido creado. Ingresa tus clases para el censo.')
        else:
            messages.success(request, f'¡Hola de nuevo, {nombre}! Puedes revisar y actualizar tus clases del censo.')
        return redirect('estudiante_censo')

    return render(request, 'estudiante_login.html', {'form': form})


def estudiante_logout(request):
    """Cierra la sesión del estudiante."""
    request.session.pop('estudiante_cuenta', None)
    request.session.pop('estudiante_nombre', None)
    messages.success(request, 'Sesión de estudiante finalizada.')
    return redirect('index')


def estudiante_censo(request):
    """Panel del estudiante donde registra las clases que planea llevar y sus horas tentativas."""
    cuenta = request.session.get('estudiante_cuenta')
    if not cuenta:
        messages.info(request, 'Por favor identifícate con tu número de cuenta y nombre para ingresar al censo.')
        return redirect('estudiante_login')

    estudiante = get_object_or_404(Estudiante, pk=cuenta)
    mis_clases = CensoEstudiante.objects.filter(estudiante=estudiante).select_related('clase')

    form = CensoEstudianteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        censo_item = form.save(commit=False)
        censo_item.estudiante = estudiante

        existente = CensoEstudiante.objects.filter(
            estudiante=estudiante,
            clase=censo_item.clase,
        ).first()

        if existente:
            existente.hora_tentativa = censo_item.hora_tentativa
            existente.save(update_fields=['hora_tentativa'])
            messages.success(
                request,
                f'Horario tentativo de "{censo_item.clase.clase}" actualizado a las {censo_item.hora_tentativa}:00.',
            )
        else:
            censo_item.save()
            messages.success(
                request,
                f'Clase "{censo_item.clase.clase}" agregada a tu censo (horario sugerido: {censo_item.hora_tentativa}:00).',
            )
        return redirect('estudiante_censo')

    # Calcular estadísticas del censo del estudiante
    total_uv = sum(item.clase.uv for item in mis_clases)
    clases_ids = [item.clase_id for item in mis_clases]

    # Consultar si ya existe horario oficial generado para sus clases
    horario_oficial_mis_clases = Horario.objects.filter(
        idClase_id__in=clases_ids,
    ).select_related('idClase', 'idDocente', 'idAula').order_by('hora')

    return render(request, 'estudiante_censo.html', {
        'estudiante': estudiante,
        'mis_clases': mis_clases,
        'form': form,
        'total_uv': total_uv,
        'horario_oficial': horario_oficial_mis_clases,
    })


@require_POST
def estudiante_eliminar_clase_censo(request, pk):
    """Elimina una clase del censo del estudiante."""
    cuenta = request.session.get('estudiante_cuenta')
    if not cuenta:
        return redirect('estudiante_login')

    item = get_object_or_404(CensoEstudiante, pk=pk, estudiante_id=cuenta)
    nombre_clase = item.clase.clase
    item.delete()
    messages.success(request, f'Clase "{nombre_clase}" removida de tu censo.')
    return redirect('estudiante_censo')


# ─── Gestión de Censo para el Coordinador ──────────────────────────────────

@login_required
def censo_global(request):
    """Vista del coordinador para supervisar los censos estudiantiles recibidos."""
    estudiantes = Estudiante.objects.prefetch_related('censo__clase').annotate(
        total_clases=Count('censo'),
    ).order_by('-created_at')

    # Demanda agregada por clase
    demanda_clases = Clase.objects.annotate(
        demanda=Count('censo_estudiantes'),
    ).order_by('-demanda', 'clase')

    total_estudiantes = estudiantes.count()
    total_registros_censo = CensoEstudiante.objects.count()

    return render(request, 'censo_global.html', {
        'estudiantes': estudiantes,
        'demanda_clases': demanda_clases,
        'total_estudiantes': total_estudiantes,
        'total_registros_censo': total_registros_censo,
    })


@login_required
@require_POST
def censo_cargar_datos_prueba(request):
    """Genera datos de censo de muestra para varios estudiantes para pruebas de optimización."""
    clases_disponibles = list(Clase.objects.all())
    if not clases_disponibles:
        messages.error(request, 'Primero registra clases en el sistema para generar datos de censo.')
        return redirect('censo_global')

    estudiantes_muestra = [
        ('20211001001', 'Carlos Mendoza', ['001', '005', '006', '008']),
        ('20211002002', 'María José López', ['001', '002', '007', '013']),
        ('20221003003', 'Luis Fernando Torres', ['002', '003', '004', '005']),
        ('20221004004', 'Andrea Sofía Castro', ['006', '007', '010', '014']),
        ('20231005005', 'Kevin David Ramos', ['003', '004', '012', '013']),
        ('20231006006', 'Valeria Nicole Paz', ['005', '006', '014', '008']),
        ('20201007007', 'Gabriel Antonio Ruiz', ['001', '007', '010', '012']),
        ('20221008008', 'Daniela Alejandra Meza', ['002', '008', '013', '014']),
    ]

    clases_dict = {c.id: c for c in clases_disponibles}
    horas_preferidas_posibles = [7, 8, 9, 10, 11, 13, 14, 15, 16]

    creados_count = 0
    for cuenta, nombre, codigos in estudiantes_muestra:
        estudiante, _ = Estudiante.objects.get_or_create(
            numero_cuenta=cuenta,
            defaults={'nombre': nombre},
        )
        for cod in codigos:
            if cod in clases_dict:
                clase_obj = clases_dict[cod]
                hora_tentativa = random.choice(horas_preferidas_posibles)
                _, created = CensoEstudiante.objects.get_or_create(
                    estudiante=estudiante,
                    clase=clase_obj,
                    defaults={'hora_tentativa': hora_tentativa},
                )
                if created:
                    creados_count += 1

    messages.success(request, f'Se cargaron con éxito datos de censo de prueba ({creados_count} selecciones de materias registradas).')
    return redirect('censo_global')


# ─── Panel Principal de Coordinador ────────────────────────────────────────

@login_required
def home(request):
    docentes_count = Docente.objects.count()
    clases_count = Clase.objects.count()
    aulas_count = Aula.objects.count()
    estudiantes_censo_count = Estudiante.objects.count()
    horarios_count = Horario.objects.count()
    return render(request, 'home.html', {
        'docentes_count': docentes_count,
        'clases_count': clases_count,
        'aulas_count': aulas_count,
        'estudiantes_censo_count': estudiantes_censo_count,
        'horarios_count': horarios_count,
    })


# ─── CRUD Docentes ─────────────────────────────────────────────────────────

@login_required
def formDocente(request):
    lista = Docente.objects.annotate(
        _carga_academica_actual=Coalesce(
            Sum('asignaciones__idClase__uv'),
            Value(0),
        ),
    )
    return render(request, 'formDocente.html', {'lista': lista})


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


# ─── Preferencias de docente ───────────────────────────────────────────────

@login_required
def preferencias_docente(request, pk):
    """Lista y gestiona las clases que puede impartir un docente con su prioridad."""
    docente_obj = get_object_or_404(Docente, pk=pk)
    preferencias = docente_obj.preferencias_clases.select_related('clase').order_by('prioridad', 'clase__clase')
    form = PreferenciaDocenteClaseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pref = form.save(commit=False)
        pref.docente = docente_obj
        if PreferenciaDocenteClase.objects.filter(docente=docente_obj, clase=pref.clase).exists():
            messages.error(request, f'Ya existe una preferencia para "{pref.clase}" en este docente.')
        else:
            pref.save()
            messages.success(request, f'Preferencia "{pref.clase}" agregada con prioridad {pref.get_prioridad_display()}.')
        return redirect('preferencias_docente', pk=pk)
    return render(request, 'preferencias_docente.html', {
        'docente': docente_obj,
        'preferencias': preferencias,
        'form': form,
    })


@login_required
@require_POST
def delete_preferencia_docente(request, pk, pref_pk):
    docente_obj = get_object_or_404(Docente, pk=pk)
    pref = get_object_or_404(PreferenciaDocenteClase, pk=pref_pk, docente=docente_obj)
    pref.delete()
    messages.success(request, 'Preferencia eliminada.')
    return redirect('preferencias_docente', pk=pk)


# ─── CRUD Clases ───────────────────────────────────────────────────────────

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


# ─── CRUD Aulas ────────────────────────────────────────────────────────────

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


# ─── Algoritmo Genético de Generación de Horarios ──────────────────────────

@login_required
def generarHorario(request):
    """
    Ejecuta el Algoritmo Genético de optimización combinatoria multiobjetivo
    con estricto respeto a la jerarquía de prioridades:
    1. Traslapes de estudiantes (Censo)
    2. Horarios y disponibilidad de docentes y aulas
    3. Carga máxima de UV por docente
    4. Preferencias de clases por docente (Alta > Media > Baja)
    """
    clases_db = list(Clase.objects.all())
    docentes_db = list(Docente.objects.all())
    aulas_db = list(Aula.objects.all())

    if not clases_db:
        messages.warning(request, 'Primero registra al menos una clase.')
        return redirect('formClase')

    if not docentes_db or not aulas_db:
        messages.error(request, 'Registra al menos un docente y un aula para generar el horario.')
        return redirect('home')

    # Extraer preferencias
    preferencias_qs = PreferenciaDocenteClase.objects.all()
    preferencias_map = {
        (p.docente_id, p.clase_id): p.prioridad
        for p in preferencias_qs
    }

    # Extraer datos del Censo Estudiantil
    censo_qs = CensoEstudiante.objects.select_related('estudiante').all()
    censo_entries = [
        CensoEntry(
            estudiante_cuenta=c.estudiante_id,
            estudiante_nombre=c.estudiante.nombre,
            clase_id=c.clase_id,
            hora_tentativa=c.hora_tentativa,
        )
        for c in censo_qs
    ]

    # Modelos a estructuras de datos para el optimizador genético
    clases_data = [
        ClaseData(id=c.id, nombre=c.clase, uv=c.uv, matricula=c.cantidadEM)
        for c in clases_db
    ]
    docentes_data = [
        DocenteData(
            id=d.id,
            nombre_completo=f'{d.nombre} {d.apellido}',
            hora_inicio=d.hora_inicio,
            hora_fin=d.hora_fin,
            carga_maxima_uv=d.carga_maxima_uv,
        )
        for d in docentes_db
    ]
    aulas_data = [
        AulaData(id=a.idAula, nombre=a.nombreAula, capacidad=a.capacidad, tipo=a.tipo)
        for a in aulas_db
    ]

    # Ejecutar Algoritmo Genético
    optimizer = GeneticScheduleOptimizer(
        clases=clases_data,
        docentes=docentes_data,
        aulas=aulas_data,
        preferencias=preferencias_map,
        censo=censo_entries,
        horas_disponibles=list(range(7, 19)),
        pop_size=80,
        max_generations=120,
    )

    try:
        mejor_cromosoma, diagnostico = optimizer.optimize()
    except Exception as e:
        messages.error(request, f'Error al ejecutar el algoritmo genético: {e}')
        return redirect('filtrarHorario')

    # Mapear diccionarios para reconstrucción
    clases_map = {c.id: c for c in clases_db}
    docentes_map = {d.id: d for d in docentes_db}
    aulas_map = {a.idAula: a for a in aulas_db}

    # Validar que no se violen las restricciones únicas de base de datos
    asignaciones_a_guardar = []
    docentes_ocupados_db = set()
    aulas_ocupadas_db = set()
    clases_asignadas = set()
    clases_no_guardadas = []

    for gene in mejor_cromosoma.genes:
        clase_obj = clases_map.get(gene.clase_id)
        docente_obj = docentes_map.get(gene.docente_id)
        aula_obj = aulas_map.get(gene.aula_id)

        if not (clase_obj and docente_obj and aula_obj):
            continue

        doc_key = (docente_obj.pk, gene.hora)
        aula_key = (aula_obj.pk, gene.hora)

        if doc_key in docentes_ocupados_db or aula_key in aulas_ocupadas_db or clase_obj.pk in clases_asignadas:
            # Caso sin solución completa para esta clase debido a colisión física estricta
            clases_no_guardadas.append(clase_obj.clase)
            continue

        asignaciones_a_guardar.append(
            Horario(
                idClase=clase_obj,
                idDocente=docente_obj,
                idAula=aula_obj,
                hora=gene.hora,
            )
        )
        docentes_ocupados_db.add(doc_key)
        aulas_ocupadas_db.add(aula_key)
        clases_asignadas.add(clase_obj.pk)

    # Notificaciones según diagnósticos y persistencia
    clases_sin_asignar = [c.clase for c in clases_db if c.pk not in clases_asignadas]
    hay_impedimento_recursos = (
        bool(clases_sin_asignar)
        or diagnostico.get('exceso_uv_total', 0) > 0
        or diagnostico.get('violaciones_capacidad_aula', 0) > 0
    )

    if hay_impedimento_recursos:
        nombres = ', '.join(clases_sin_asignar) if clases_sin_asignar else 'materias en exceso de carga'
        messages.error(
            request,
            f'No se pudo asignar {len(clases_sin_asignar)} clase(s): {nombres}. '
            'No hay suficientes docentes disponibles, aulas con capacidad adecuada '
            'o espacios horarios/carga académica libres para completar la asignación.',
        )
    else:
        with transaction.atomic():
            Horario.objects.all().delete()
            Horario.objects.bulk_create(asignaciones_a_guardar)
        messages.success(request, 'Horario generado correctamente.')

    # Guardar diagnóstico en sesión para desplegar métricas en la vista
    request.session['ultimo_diagnostico_ga'] = diagnostico

    return _render_horario(
        request,
        Horario.objects.select_related('idClase', 'idDocente', 'idAula'),
    )


# ─── Consultas, Filtros y Renderizado de Horario ───────────────────────────

def _horario_filtrado(request):
    horario = Horario.objects.select_related('idClase', 'idDocente', 'idAula')
    hora = request.GET.get('hora', '').strip()
    if hora:
        try:
            hora_numero = int(hora)
            if 7 <= hora_numero <= 18:
                horario = horario.filter(hora=hora_numero)
            else:
                messages.error(request, 'La hora debe estar entre 7 y 18.')
                return horario.none()
        except ValueError:
            messages.error(request, 'La hora debe ser un número entero entre 7 y 18.')
            return horario.none()

    docente_id = request.GET.get('docente', '').strip()
    clase_id = request.GET.get('clase', '').strip()
    aula_id = request.GET.get('aula', '').strip()

    if docente_id:
        horario = horario.filter(idDocente_id=docente_id)
    if clase_id:
        horario = horario.filter(idClase_id=clase_id)
    if aula_id:
        horario = horario.filter(idAula_id=aula_id)

    return horario


def _render_horario(request, horario):
    diagnostico = request.session.get('ultimo_diagnostico_ga')
    docentes_filtro = Docente.objects.all()
    clases_filtro = Clase.objects.all()
    aulas_filtro = Aula.objects.all()

    return render(
        request,
        'horario.html',
        {
            'horario': horario,
            'horas': range(7, 19),
            'dias': range(5),
            'diagnostico': diagnostico,
            'docentes_filtro': docentes_filtro,
            'clases_filtro': clases_filtro,
            'aulas_filtro': aulas_filtro,
            'total_asignaciones': horario.count(),
        },
    )


from functools import wraps
from django.urls import reverse


def session_usuario_requerida(view_func):
    """Permite el acceso a Coordinadores autenticados o a Estudiantes con sesión activa."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated or request.session.get('estudiante_cuenta'):
            return view_func(request, *args, **kwargs)
        return redirect(f"{reverse('login')}?next={request.path}")
    return wrapper


@session_usuario_requerida
def filtrarHorario(request):
    return _render_horario(request, _horario_filtrado(request))


# ─── Exportación a Excel y PDF ─────────────────────────────────────────────

@session_usuario_requerida
def descargarHorarioExcel(request):
    """Descarga el horario completo o filtrado en formato Excel (.xlsx)."""
    horarios_qs = _horario_filtrado(request)

    filtros_activos = []
    if request.GET.get('hora'):
        filtros_activos.append(f"Hora: {request.GET.get('hora')}:00")
    if request.GET.get('docente'):
        docente = Docente.objects.filter(pk=request.GET.get('docente')).first()
        filtros_activos.append(f"Docente: {docente or request.GET.get('docente')}")
    if request.GET.get('clase'):
        clase = Clase.objects.filter(pk=request.GET.get('clase')).first()
        filtros_activos.append(f"Clase: {clase or request.GET.get('clase')}")
    if request.GET.get('aula'):
        aula = Aula.objects.filter(pk=request.GET.get('aula')).first()
        filtros_activos.append(f"Aula: {aula or request.GET.get('aula')}")

    filtros_str = ', '.join(filtros_activos) if filtros_activos else 'Todos los registros (sin filtros)'

    excel_buffer = generar_excel_horario(horarios_qs, filtros_str=filtros_str)
    response = HttpResponse(
        excel_buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="horario_academico.xlsx"'
    return response


@session_usuario_requerida
def descargarHorario(request):
    """Descarga el horario en formato PDF."""
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
