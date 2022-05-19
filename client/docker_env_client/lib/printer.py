class Printer:
    def print(self, msg: str, end='\n'):
        print(msg, end=end)


class NullPrinter(Printer):

    def __init__(self):
        self.value = ""

    def print(self, msg: str, end='\n'):
        self.value = f'{self.value}{msg}{end}'
        

