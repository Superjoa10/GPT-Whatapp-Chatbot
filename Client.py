class Client_obj():
    def __init__(self, number, counter_limit):
        self.number = number
        self.counter = 0 # counter instance
        self.counter_limit = counter_limit
        self.type_ = str() #Type of conversation to have with GPT
        self.validation = self.counter_check() #Variable for when timer hits time_limit
        self.access = True #  Acess granted or denied



    def __repr__(self):
        return self.number

    def counter_check(self): #Re-use thrueout the code so you, call after self.counter +=1
        print('Counter checked: Nº', self.counter)
        if self.counter >= self.counter_limit:
            return False
        else: 
            return True
        
    def change_type(self, choice):
        self.type_ = choice
        print(self.type_)

        