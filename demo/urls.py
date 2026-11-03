"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('iniciar', views.iniciar, name='iniciar'),
    path('login/', views.login, name='login'),
    path('registrarUsuario/', views.registrarUsuario, name='registrarUsuario'),
    path('registrarUsuario/crear_usuario', views.crear_usuario, name='crear_usuario'),
    path('home/', views.home, name='home'),
    path('formDocente/', views.formDocente, name = 'formDocente'),
    path('formClase/', views.formClase, name = 'formClase'),

    # URLS del formulario docente
    path('docente/', views.docente, name='docente'),
    path('docente/crear/', views.create_docente, name='create_docente'),
    path('docente/insert', views.insert_docente, name='insert_docente'),

    path('docente/edit/', views.edit_docente, name='edit_docente'),
    path('docente/update', views.update_docente, name='insert_docente'),

    path('docente/remove/', views.remove_docente, name='remove_docente'),
    path('docente/delete', views.delete_docente, name='delete_docente'),

    # URLS del formulario clases
    path('clase/', views.clase, name='docente'),
    path('clase/crear/', views.create_clase, name='create_clase'),
    path('clase/insert', views.insert_clase, name='insert_clase'),

    path('clase/edit/', views.edit_clase, name='edit_clase'),
    path('clase/update', views.update_clase, name='update_clase'),

    path('clase/remove', views.remove_clase, name='remove_clase'),
    path('clase/delete', views.delete_clase, name='delete_clase'),

    # URLS para la generacion del Horario
    path('generarHorario/', views.generarHorario, name='generarHorario'),
    path('filtrarHorario/', views.filtrarHorario, name='filtrarHorario'),
    path('descargarHorario/', views.descargarHorario, name='descargarHorario'),


    # path('persona/remove/', views.create_persona, name='create_persona'),
    # path('persona/delete', views.insert_persona, name='insert_persona'),
    
    # path('listar/', views.listar, name='listar'),

    # path('crear/', views.crear, name='crear'),
    # path('insert', views.insert, name='insert'),

    # path('editar', views.editar, name='editar'),
    # path('update', views.update, name='update'),

    # path('eliminar/', views.eliminar, name='eliminar'),
     ##path('delete', views.eliminar, name='eliminar'),
]
