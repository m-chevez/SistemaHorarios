class Horario:
    def __init__(self, idClase, idDocente, idAula, hora):
        self.idClase = idClase
        self.idDocente = idDocente
        self.idAula = idAula
        self.hora = hora
    
    def toJson(self):
        return {"idClase":self.idClase, "idDocente": self.idDocente, "idAula":self.idAula, "hora": self.hora}