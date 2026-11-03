from lib.user import User
import json
class LibUser:
    def login(self, email, password):
        file = open('data/users.json')
        j = json.load(file)
        for x in j:
            if x['email']== email and x['password']==password:
                return True
        return False
    
    def registrarUsuario(self, email, password):
        file = open('data/users.json')
        j = json.load(file)

        j = j + [User(email, password).toJson()]

        file = open("data/users.json","w")
        json.dump(j,file,ensure_ascii=False, indent=4)
        file.close()

        return True

