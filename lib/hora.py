class Hora:
    def __init__(self, idHora, idClase, idDocente):
        self.idHora = id
        self.idClase = idClase
        self.idDocente = idDocente

    def toJson(self):
        return {"idHora": self.idHora, "idClase": self.idClase, "idDocente": self.idDocente}
    