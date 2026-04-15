from wasmtime import Engine, Linker, Module, Store


class Loader():
    def __init__(self):
        self.engine = Engine()
        self.linker = Linker(self.engine)

    def load_module(self, path: str):
        module = Module.from_file(self.engine, path)
        return module
    
    def create_store(self):
        return Store(self.engine)
    
    def instantiate(self, store, module):
        instance = self.linker.instantiate(store, module)
        return instance
    
    def load(self, path: str):
        module = self.load_module(path)
        store = self.create_store()

        instance = self.instantiate(store, module)
        return {
            'store': store,
            'instance': instance,
            'module': module
        }