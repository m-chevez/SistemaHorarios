from django.contrib import admin
from django.urls import path

from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('iniciar', views.iniciar, name='iniciar'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registrarUsuario/', views.registrarUsuario, name='registrarUsuario'),
    path('home/', views.home, name='home'),
    path('formDocente/', views.formDocente, name='formDocente'),
    path('formClase/', views.formClase, name='formClase'),
    path('docente/', views.docente, name='docente'),
    path('docente/crear/', views.create_docente, name='create_docente'),
    path('docente/insert', views.insert_docente, name='insert_docente'),
    path('docente/edit/', views.edit_docente, name='edit_docente'),
    path('docente/update', views.update_docente, name='update_docente'),
    path('docente/remove/', views.remove_docente, name='remove_docente'),
    path('docente/delete', views.delete_docente, name='delete_docente'),
    path('clase/', views.clase, name='clase'),
    path('clase/crear/', views.create_clase, name='create_clase'),
    path('clase/insert', views.insert_clase, name='insert_clase'),
    path('clase/edit/', views.edit_clase, name='edit_clase'),
    path('clase/update', views.update_clase, name='update_clase'),
    path('clase/remove/', views.remove_clase, name='remove_clase'),
    path('clase/delete', views.delete_clase, name='delete_clase'),
    path('aulas/', views.aulas, name='aulas'),
    path('aulas/crear/', views.crear_aula, name='crear_aula'),
    path('aulas/insertar/', views.insertar_aula, name='insertar_aula'),
    path('aulas/<str:pk>/editar/', views.editar_aula, name='editar_aula'),
    path('aulas/<str:pk>/actualizar/', views.actualizar_aula, name='actualizar_aula'),
    path('aulas/<str:pk>/eliminar/', views.eliminar_aula, name='eliminar_aula'),
    path('aulas/<str:pk>/confirmar-eliminar/', views.confirmar_eliminar_aula, name='confirmar_eliminar_aula'),
    path('generarHorario/', views.generarHorario, name='generarHorario'),
    path('filtrarHorario/', views.filtrarHorario, name='filtrarHorario'),
    path('descargarHorario/', views.descargarHorario, name='descargarHorario'),
]
