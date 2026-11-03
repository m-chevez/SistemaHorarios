from lib.automovil import Automovil
class List:
    array = [Automovil(1,"Toyota","Corolla","2010"),Automovil(2,"Toyota","Corolla","2012"),Automovil(3,"Toyota","Corolla","2013")]

    def obtener(self):
        return self.array
    def obtener_by_id(self,id):
        for x in self.array:
            if(str(x.id) == id):
                return x
        return None
    def actualizar(self,id,marca, modelo, anio):
        for i in range(0,len(self.array)):
            if(str(self.array[i].id) == id):
                self.array[i].marca = marca
                self.array[i].modelo = modelo
                self.array[i].anio = anio
                return True
        return False
    
    def mostrar(self):
        for i in range(0,len(self.array)):
            print(str(i)+" - "+str(self.array[i]))
    def insertar(self,x):
        if(len(self.array)<=0):
            self.array.append(x)
        else:
            temp = self.array[0]
            self.array[0] = x
            for i in range(0,len(self.array)-1):
                temp2 = self.array[i+1]
                self.array[i+1] = temp
                temp = temp2
            self.array.append(temp)
            return self.array
    def eliminar(self,x):
        for i in range(0,len(self.array)-1):
            if (self.array[i]==x):
                for j in range(i,len(self.array)-1):
                    self.array[j]= self.array[j+1]
                self.array.pop()
        return self.array  