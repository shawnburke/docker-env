from threading import Thread, Event

counter = 0

class RepeatingTimer(Thread):
    def __init__(self, interval, function, name=None):
        super().__init__(target=self._tick)
        self.function = function
        self.running = False
        global counter
        counter = counter + 1
        self.name = name or f'Timer {counter}'
        self.interval = interval
        self.event = Event()

    def _tick(self):
        try:
            self.running = True
            while self.running:
                try: 
                    self.function()
                except Exception as e:
                    print(f'Error running timer {self.name} function: {e}')
                self.running = not self.event.wait(self.interval)
        finally:
            self.running = False
            
    def cancel(self):
        self.event.set()



