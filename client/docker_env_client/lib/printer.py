class Printer:
    def print(self, msg: str, end='\n'):
        print(msg, end=end)


class NullPrinter(Printer):
    def print(self, msg: str, end='\n'):
        pass

