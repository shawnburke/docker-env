
class Container:
    def __init__(self, contents=None):
        self.types = {}
        for k, v in contents.items():
            self.register(k, v)

    def register(self, t, impl):
        self.types[t] = (impl, not isinstance(impl, type))

    def create(self, t, *args, **kwargs):
        entry = self.types.get(t)
        if entry is None:
            raise ValueError(f'No type {t.name} in container')

        if entry[1]:
            raise ValueError(f'{t.name} is singleton, use get')

        return entry[0](*args, **kwargs)

    def get(self, t):
        entry = self.types.get(t)
        if entry is None:
            raise ValueError(f'No type {t.__name__} in container')
        
        if not entry[1]:
            raise ValueError(f'Entry {t.__name__} is not an instance')
        return entry[0]


        
