from lib.Aula import Aula
from lib.Clase import Clase
from lib.Docente import Docente
from lib.Horario import Horario
from lib.libAula import LibAula
from lib.libDocente import LibDocente
from lib.libClase import LibClase

import json

import random

class LibHorario:

    def crearHorario(self):
        ### Eliminar el horario viejo

        file = open("data/horario.json")
        j = json.load(file)
        j = []
        
        file = open("data/horario.json","w")
        json.dump(j, file,ensure_ascii = False, indent = 4)
        file.close()
        ###

        file = open("data/clases.json")
        j = json.load(file)

        for x in j:
            self.agregarClaseH(x['id'])

    def agregarClaseH(self, idClase):        
        file = open("data/horario.json")
        j = json.load(file)
        docente = self.seleccionarDocente()
        aula = self.seleccionarAula()
        
        if len(j) == 0:
            j = j + [Horario(idClase, docente.id, aula.idAula, 7).toJson()]
        else:
            hora = int(j[-1]['hora'])
            agregado = False
            libAula = LibAula()
            cantAulas = libAula.cantidadDeAulas()
            docente = self.seleccionarDocente()
            aula = self.seleccionarAula()
            c = 0
            for y in j:
                if y['hora'] == hora:
                    c +=1
            
            if cantAulas == c:
                j = j + [Horario(idClase, docente.id, aula.idAula, hora + 1).toJson()]
            else:

                file = open("data/horario.json")
                j = json.load(file)
                lDocente = []
                lAula = []
                for d in j:
                    if d['hora'] == hora:
                        lDocente.append(d['idDocente'])
                        lAula.append(d['idAula'])

                
                print(lDocente)
                print(lAula)
                docente = self.seleccionarDocente(lDocente)
                aula = self.seleccionarAula(lAula)
                
                j = j + [Horario(idClase, docente, aula, hora).toJson()]
        
        
        file = open("data/horario.json","w")
        json.dump(j, file,ensure_ascii=False, indent=4)
        file.close()

        

    def seleccionarDocente(self, lDocente = None):
        file = open("data/docentes.json")
        j = json.load(file)
        if lDocente is None:
            indiceRamdon = random.randint(0, len(j) - 1)
            docente = Docente(j[indiceRamdon]['id'], j[indiceRamdon]['nombre'], j[indiceRamdon]['apellido'])
        else:

            lista = []
            for docente in j:
                if docente['id'] not in lDocente:
                    lista.append(docente)
            
            
            indiceRamdon = random.randint(0, len(lista) - 1)
            docente = lista[indiceRamdon]['id']
        
                        
            print("-----")
            print(lista)

        return docente

    def seleccionarAula(self, lAula = None):
        file = open("data/aulas.json")
        j = json.load(file)
        if lAula is None:
            indiceRamdon = random.randint(0, len(j) - 1)
            aula = Aula(j[indiceRamdon]['idAula'], j[indiceRamdon]['nombreAula'])
        else:
            lista = []
            
            for aula in j:
                if aula['idAula'] not in lAula:
                    lista.append(aula)
            
            
            indiceRamdon = random.randint(0, len(lista) - 1)
            aula = lista[indiceRamdon]['idAula']

        return aula

    def get_Horario(self):
        libClase = LibClase()
        libDocente = LibDocente()
        libAula = LibAula()

        file = open("data/horario.json")
        j = json.load(file)

        archivoClase = open("data/clases.json")
        c = json.load(archivoClase)

        list = []
        for x in j:
            list.append(Horario(libClase.get_clase_by_id(x['idClase']), libDocente.get_docente_by_id(x['idDocente']),
                                libAula.get_aula_by_id(x['idAula']), x['hora']))
        return list 

    

