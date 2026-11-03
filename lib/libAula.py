from lib.Aula import Aula
import json

class LibAula:
    def get_aula_by_id(self, id):
        file = open("data/aulas.json")
        j = json.load(file)
        for x in j: 
            if(x['idAula'] == id):
                return Aula(x['idAula'], x['nombreAula'])
        return None
    
    def get_aulas(self):
        file = open("data/aulas.json")
        j = json.load(file)
        list = []
        for x in j:
            list.append(Aula(x['idAula'], x['nombreAula']))
        return list 

    def cantidadDeAulas(self):
        file = open("data/aulas.json")
        j = json.load(file)

        return len(j)