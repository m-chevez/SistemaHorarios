from django.contrib import admin
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from .models import Aula, Clase, Docente, Horario, PreferenciaDocenteClase


class PreferenciaInline(admin.TabularInline):
    model = PreferenciaDocenteClase
    extra = 1
    autocomplete_fields = ('clase',)


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'apellido',
        'carga_academica_actual',
        'carga_maxima_uv',
        'hora_inicio',
        'hora_fin',
    )
    search_fields = ('id', 'nombre', 'apellido')
    inlines = (PreferenciaInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _carga_academica_actual=Coalesce(
                Sum('asignaciones__idClase__uv'),
                Value(0),
            ),
        )


@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ('idAula', 'nombreAula', 'tipo', 'capacidad')
    list_filter = ('tipo',)
    search_fields = ('idAula', 'nombreAula')


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'clase', 'uv')
    search_fields = ('id', 'clase')


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('idClase', 'idDocente', 'idAula', 'hora')
    list_filter = ('hora',)
    search_fields = ('idClase__id', 'idClase__clase', 'idDocente__nombre')


@admin.register(PreferenciaDocenteClase)
class PreferenciaDocenteClaseAdmin(admin.ModelAdmin):
    list_display = ('docente', 'clase', 'prioridad')
    list_filter = ('prioridad',)
    search_fields = ('docente__nombre', 'docente__apellido', 'clase__clase')
    autocomplete_fields = ('clase',)
