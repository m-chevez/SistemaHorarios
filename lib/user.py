class User: 
    def __init__(self,email,password):
        self.email = email
        self.password = password
    
    def toJson(self):
        return {'email':self.email, 'password':self.password}