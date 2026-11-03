import importlib
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from lib.cola import List
from lib.automovil import Automovil
from lib.userlib  import LibUser
from lib.libDocente import LibDocente
from lib.libClase import LibClase
from lib.libHorario import LibHorario
# Librerias para la creación del pdf
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import io

lista = List()
def index(request):
    #resp = lista.obtener()
    return render(request,"index.html")
    #return HttpResponse("Hola mundo")
    #return render(request,"index.html",{"lista":lista.obtener()})
def login(request):
    return render(request,"login.html")

def registrarUsuario(request):
    return render(request, "registrarUsuario.html")

def crear_usuario(request):
    email = request.POST['email']
    password = request.POST['password']
    libUser = LibUser()
    resp = libUser.registrarUsuario(email, password)

    if(resp):
        return redirect("/login")
    else:
        return redirect("/registrarUsuario")

def formDocente(request):
    libDocente = LibDocente()
    lista = libDocente.get_docentes()

    return render(request,"formDocente.html",{"lista":lista})

def formClase(request):
    libClase = LibClase()
    lista = libClase.get_clases()

    return render(request,"formClase.html",{"lista":lista})

# CRUD de Docentes
def docente(request):
    return render(request,"create.html")

def create_docente(request):
    return render(request,"create.html")
def insert_docente(request):
    id = request.POST['id']
    nombre = request.POST['nombre']
    apellido = request.POST['apellido']
    libDocente = LibDocente()
    resp = libDocente.create(id, nombre, apellido)
    if(resp):
        return redirect("/formDocente")
    else:
        return redirect("/docente/crear")


def edit_docente(request):
    id = request.GET['id']
    libDocente = LibDocente()
    docente = libDocente.get_docente_by_id(id)
    return render(request,"edit.html",{'docente':docente})
    
def update_docente(request):
    id = request.POST['id']
    nombre = request.POST['nombre']
    apellido = request.POST['apellido']
    libDocente = LibDocente()
    resp = libDocente.edit(id, nombre, apellido)
    if(resp):
        return redirect("/formDocente")
    else:
        return redirect("/docente/edit?id=" + id)

def remove_docente(request):
    id = request.GET['id']
    libDocente = LibDocente()
    docente = libDocente.get_docente_by_id(id)
    return render(request,"remove.html",{'docente':docente})

def delete_docente(request):
    id = request.POST['id']
    libDocente = LibDocente()
    # docente = libDocente.get_docente_by_id(id)
    # Eliminar el docente
    libDocente.remove(id)
    
    return redirect("/formDocente")


# CRUD de clases
def clase(request):
    return render(request,"createClase.html")

def create_clase(request):
    return render(request,"createClase.html")
def insert_clase(request):
    id = request.POST['id']
    clase = request.POST['clase']
    uv = request.POST['uv']
    cantidadEM = request.POST['cantidadEM']
    libClase = LibClase()
    resp = libClase.create(id, clase, uv,cantidadEM)
    if(resp):
        return redirect("/formClase")
    else:
        return redirect("/clase/crear")


def edit_clase(request):
    id = request.GET['id']
    libClase = LibClase()
    clase = libClase.get_clase_by_id(id)
    return render(request,"editClase.html",{'clase':clase})
def update_clase(request):
    id = request.POST['id']
    clase = request.POST['clase']
    uv = request.POST['uv']
    cantidadEM = request.POST['cantidadEM']
    libClase = LibClase()
    resp = libClase.edit(id, clase, uv, cantidadEM)
    if(resp):
        return redirect("/formClase")
    else:
        return redirect("/clase/edit?id=" + id)


def remove_clase(request):
    id = request.GET['id']
    libClase = LibClase()
    clase = libClase.get_clase_by_id(id)
    return render(request,"removeClase.html",{'clase':clase})

def delete_clase(request):
    id = request.POST['id']
    libClase = LibClase()
    # docente = libDocente.get_docente_by_id(id)
    # Eliminar el docente
    libClase.remove(id)
    
    return redirect("/formClase")

# GENERAR HORARIO
def generarHorario(request):
    libHorario = LibHorario()
    libHorario.crearHorario()
    horario = libHorario.get_Horario()
    
    horas = range(7, 19)  # De 7 a.m. a 6 p.m.
    dias = range(5)  # Lunes a Viernes

    return render(request, "horario.html", {'horario': horario, 'horas': horas, 'dias': dias})

# FILTRAR HORARIO
def filtrarHorario(request):
    libHorario = LibHorario()
    horario = libHorario.get_Horario()

    # Obtener filtros desde la solicitud GET
    hora_filter = request.GET.get('hora')
    docente_filter = request.GET.get('docente')
    clase_filter = request.GET.get('clase')
    aula_filter = request.GET.get('aula')

    # Filtrar la lista de horarios
    filtered_horario = []
    for slot in horario:
        if hora_filter and slot.hora != int(hora_filter):
            continue
        if docente_filter and slot.idDocente.id != docente_filter:
            continue
        if clase_filter and slot.idClase.id != clase_filter:
            continue
        if aula_filter and slot.idAula.idAula != aula_filter:
            continue
        filtered_horario.append(slot)

    horas = range(7, 19)  
    dias = range(5)  
    
    return render(request, "horario.html", {'horario': filtered_horario, 'horas': horas, 'dias': dias})

# DESCARGAR EL PDF
def descargarHorario(request):
    
    libHorario = LibHorario()
    horario = libHorario.get_Horario()

    # Obtener filtros desde la solicitud GET
    hora_filter = request.GET.get('hora')
    docente_filter = request.GET.get('docente')
    clase_filter = request.GET.get('clase')
    aula_filter = request.GET.get('aula')

    # Filtrar la lista de horarios
    filtered_horario = []
    for slot in horario:
        if hora_filter and slot.hora != int(hora_filter):
            continue
        if docente_filter and slot.idDocente.id != docente_filter:
            continue
        if clase_filter and slot.idClase.id != clase_filter:
            continue
        if aula_filter and slot.idAula.idAula != aula_filter:
            continue
        filtered_horario.append(slot)

    # Renderizar el HTML para el horario filtrado
    html_string = render_to_string('horario_pdf.html', {'horario': filtered_horario, 'horas': range(7, 19), 'dias': range(5)})

    # Crear un objeto PDF
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.StringIO(html_string), dest=result)

    # Crear una respuesta HTTP con el archivo PDF
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="horario.pdf"'
    return response


def iniciar(request):
    libUser = LibUser()
    email = request.POST['email']
    password = request.POST['password']
    resp = libUser.login(email, password)
    if(resp):
        return redirect("/home")
    else: 
        return redirect("/login")
        
def home(request):
    return render(request,"home.html")




# def insert(request):
#     marca= request.POST["marca"]
#     modelo= request.POST["modelo"]
#     anio= request.POST["anio"]
#     lista.insertar(Automovil(len(lista.array)+1, request.POST["marca"],modelo, anio))
#     return render(request,"msj.html")

# def update(request):
#     marca= request.POST["marca"]
#     modelo= request.POST["modelo"]
#     anio= request.POST["anio"]
#     id = request.POST["id"]
#     lista.actualizar(id, marca,modelo, anio)
#     return render(request,"msj.html")

# def listar(request):
#     return render(request,"home.html",{"nombre":"Listar"})
# def crear(request):
#     saludo = "hola"
#     return render(request,"crear.html",{"msg":saludo})
# def editar(request):
#     id= request.GET["id"]
#     automovil = lista.obtener_by_id(id)
#     return render(request,"editar.html",{"automovil":automovil})

# def eliminar(request):
#     return render(request,"crear.html",{"nombre":"María"})