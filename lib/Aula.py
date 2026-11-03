class Aula:
    def __init__(self, idAula, nombreAula):
        self.idAula = idAula
        self.nombreAula = nombreAula
    
    def toJson(self):
        return {"idAula":self.idAula, "nombreAula": self.nombreAula}