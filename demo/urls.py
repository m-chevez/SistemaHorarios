from django.contrib import admin
from django.urls import path

from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),

    # Autenticación Coordinador
    path('login/', views.login_view, name='login'),
    path('iniciar', views.iniciar, name='iniciar'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registrarUsuario/', views.registrarUsuario, name='registrarUsuario'),
    path('home/', views.home, name='home'),

    # Portal Estudiante y Censo
    path('estudiante/login/', views.estudiante_login, name='estudiante_login'),
    path('estudiante/logout/', views.estudiante_logout, name='estudiante_logout'),
    path('estudiante/censo/', views.estudiante_censo, name='estudiante_censo'),
    path('estudiante/censo/<int:pk>/eliminar/', views.estudiante_eliminar_clase_censo, name='estudiante_eliminar_censo'),

    # Censo para el Coordinador
    path('censo/', views.censo_global, name='censo_global'),
    path('censo/cargar-muestra/', views.censo_cargar_datos_prueba, name='censo_cargar_muestra'),

    # Docentes
    path('formDocente/', views.formDocente, name='formDocente'),
    path('docente/', views.docente, name='docente'),
    path('docente/crear/', views.create_docente, name='create_docente'),
    path('docente/insert', views.insert_docente, name='insert_docente'),
    path('docente/edit/', views.edit_docente, name='edit_docente'),
    path('docente/update', views.update_docente, name='update_docente'),
    path('docente/remove/', views.remove_docente, name='remove_docente'),
    path('docente/delete', views.delete_docente, name='delete_docente'),
    path('docente/<str:pk>/preferencias/', views.preferencias_docente, name='preferencias_docente'),
    path('docente/<str:pk>/preferencias/<int:pref_pk>/eliminar/', views.delete_preferencia_docente, name='delete_preferencia_docente'),

    # Clases
    path('formClase/', views.formClase, name='formClase'),
    path('clase/', views.clase, name='clase'),
    path('clase/crear/', views.create_clase, name='create_clase'),
    path('clase/insert', views.insert_clase, name='insert_clase'),
    path('clase/edit/', views.edit_clase, name='edit_clase'),
    path('clase/update', views.update_clase, name='update_clase'),
    path('clase/remove/', views.remove_clase, name='remove_clase'),
    path('clase/delete', views.delete_clase, name='delete_clase'),

    # Aulas
    path('aulas/', views.aulas, name='aulas'),
    path('aulas/crear/', views.crear_aula, name='crear_aula'),
    path('aulas/insertar/', views.insertar_aula, name='insertar_aula'),
    path('aulas/<str:pk>/editar/', views.editar_aula, name='editar_aula'),
    path('aulas/<str:pk>/actualizar/', views.actualizar_aula, name='actualizar_aula'),
    path('aulas/<str:pk>/eliminar/', views.eliminar_aula, name='eliminar_aula'),
    path('aulas/<str:pk>/confirmar-eliminar/', views.confirmar_eliminar_aula, name='confirmar_eliminar_aula'),

    # Generación y Reportes de Horarios
    path('generarHorario/', views.generarHorario, name='generarHorario'),
    path('filtrarHorario/', views.filtrarHorario, name='filtrarHorario'),
    path('descargarHorario/', views.descargarHorario, name='descargarHorario'),
    path('descargarHorarioExcel/', views.descargarHorarioExcel, name='descargarHorarioExcel'),
]
