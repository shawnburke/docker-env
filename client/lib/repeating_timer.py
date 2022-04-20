from threading import Timer

class RepeatingTimer(Timer):
    def __init__(self, interval, function, name=None):
        super().__init__(interval, self._tick)
        self.function = function
        self.running = False
        self.name = name

    def _tick(self):
        self.function()

    def run(self):
        self.running = True
        while self.running:
            super().run()
    
    def cancel(self):
        self.running = False
        super().cancel()



