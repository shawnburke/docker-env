from threading import Timer

class RepeatingTimer(Timer):
    def __init__(self, interval, function):
        super().__init__(interval, self._tick)
        self.function = function
        self.running = False

    def _tick(self):
        self.function()

    def run(self):
        self.running = True
        while self.running:
            super().run()
    
    def cancel(self):
        self.running = False
        super().cancel()



