from wasmtime import Instance, Store
import pickle


class Context:
    def __init__(self, module_id: str, store: Store, instance: Instance, functions: dict[str, any]):
        self.module_id = module_id
        self.store = store
        self.instance = instance
        self.functions = functions
            

    def __str__(self):
        return self.module_id


    def __repr__(self):
        return self.module_id
    