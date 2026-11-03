class Clase: 
    def __init__(self, id, clase, uv, cantidadEM):
        self.id = id
        self.clase = clase
        self.uv = uv
        self.cantidadEM = cantidadEM

    
    def toJson(self):
        return {"id":self.id, "clase":self.clase, "uv": self.uv, "cantidadEM":self.cantidadEM}