from lib.Docente import Docente
import json
class LibDocente:

    def create(self, id, nombre, apellido):

        docente = Docente(id, nombre, apellido)
        file = open("data/docentes.json")
        j = json.load(file)
        j = j + [docente.toJson()]
        file = open("data/docentes.json","w")
        json.dump(j,file,ensure_ascii=False, indent=4)
        file.close()
        return True

    def get_docentes(self):
        file = open("data/docentes.json")
        j = json.load(file)
        list = []
        for x in j:
            list.append(Docente(x['id'],x['nombre'],x['apellido']))
        return list 
    
    def get_docente_by_id(self, id):
        file = open("data/docentes.json")
        j = json.load(file)
        for x in j: 
            if(x['id']==id):
                return Docente(x['id'],x['nombre'],x['apellido'])
        return None
    
    def edit(self, id, nombre, apellido):
        file = open("data/docentes.json")
        j = json.load(file)
        for x in j: 
            if(x['id']==id):
                x['nombre'] = nombre
                x['apellido']= apellido
                file = open("data/docentes.json","w")
                json.dump(j, file, ensure_ascii=False, indent=4)
                file.close()
                return True
        return False
    
    def remove(self, id):
        file = open("data/docentes.json")
        j = json.load(file)
        index = 0
        for x in j: 
            if(x['id'] == id):
                for i in range(index, (len(j) - 1)):
                    j[i] = j[i + 1]
                j = j[:-1]

                file = open("data/docentes.json","w")
                json.dump(j, file, ensure_ascii=False, indent=4)
                file.close()
                return True

            index += 1
        return False


        






