from lib.Clase import Clase
import json
class LibClase:

    def create(self, id, clase, uv, cantidadEM):

        clase = Clase(id, clase, int(uv), int(cantidadEM))
        file = open("data/clases.json")
        j = json.load(file)
        j = j + [clase.toJson()]
        file = open("data/clases.json","w")
        json.dump(j,file,ensure_ascii=False, indent=4)
        file.close()
        return True

    def get_clases(self):
        file = open("data/clases.json")
        j = json.load(file)
        list = []
        for x in j:
            list.append(Clase(x['id'], x['clase'], x['uv'], x['cantidadEM']))
        return list 
    
    def get_clase_by_id(self, id):
        file = open("data/clases.json")
        j = json.load(file)
        for x in j: 
            if(x['id']==id):
                return Clase(x['id'], x['clase'], x['uv'], x['cantidadEM'])
        return None
    
    def edit(self, id, clase, uv, cantidadEM):
        file = open("data/clases.json")
        j = json.load(file)
        for x in j: 
            if(x['id']==id):
                x['clase'] = clase
                x['uv'] = int(uv)
                x['cantidadEM'] = int(cantidadEM)
                file = open("data/clases.json","w")
                json.dump(j, file, ensure_ascii=False, indent=4)
                file.close()
                return True
        return False
    
    def remove(self, id):
        file = open("data/clases.json")
        j = json.load(file)
        index = 0
        for x in j: 
            if(x['id'] == id):

                for i in range(index, (len(j) - 1)):
                    j[i] = j[i + 1]
                j = j[:-1]

                file = open("data/clases.json","w")
                json.dump(j, file, ensure_ascii=False, indent=4)
                file.close()
                return True

            index += 1
        return False