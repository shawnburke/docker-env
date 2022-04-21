from threading import Thread, Event

from sqlalchemy import true

class RepeatingTimer(Thread):
    def __init__(self, interval, function, name=None):
        super().__init__(target=self._tick)
        self.function = function
        self.running = False
        self.name = name
        self.interval = interval
        self.event = Event()

    def _tick(self):
        try:
            self.running = True
            while self.running:
                self.function()
                self.running = not self.event.wait(self.interval)
        finally:
            self.running = False
            
    def cancel(self):
        self.event.set()



