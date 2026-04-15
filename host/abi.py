from wasmtime import Instance, Store

from host.memory import MemoryManager
from host.typesys import TypeSystem


class ABIManager:
    def __init__(self):
        self.reqd_fns = (
            'init',
            'cleanup',
            'malloc',
            'free',
            'call_function',
            'get_functions'
        )
    
    def validate(self, store: Store, instance: Instance) -> None:
        exports = instance.exports(store)
        for fn in self.reqd_fns:
            if fn not in exports:
                raise Exception(f"Missing required function: {fn}")
    
    def get_function(self, store: Store, instance: Instance, name: str) -> callable:
        exports = instance.exports(store)
        if name not in exports:
            raise Exception(f"Missing required function: {name}")
        return exports[name]
    
    def call_init(self, store: Store, instance: Instance) -> None:
        fn = self.get_function(store, instance, "init")
        fn(store)

    def call_cleanup(self, store: Store, instance: Instance) -> None:
        fn = self.get_function(store, instance, "cleanup")
        fn(store)

    def get_functions(self, store: Store, instance: Instance, memory_mgr: MemoryManager, typesys: TypeSystem) -> list:
        fn = self.get_function(store, instance, "get_functions")
        ptr = fn(store)
        return typesys.from_wasm(memory_mgr, store, instance, ptr)

    def call_function(self, store: Store, instance: Instance, mem_mgr: MemoryManager, typesys: TypeSystem, fn_name: str, args: list) -> callable:
        req = {
            "function": fn_name,
            "args": args
        }
        ptr, size = typesys.to_wasm(mem_mgr, store, instance, req)
        call_fn = self.get_function(store, instance, "call_function")
        res_ptr = call_fn(store, ptr, size)
        return typesys.from_wasm(mem_mgr, store, instance, res_ptr)
    
    def safe_call(self, store: Store, instance: Instance, fn_name: str, *args) -> callable:
        '''Use this fn for init and cleanup to avoid crashing the host if they fail'''
        try:
            fn = self.get_function(store, instance, fn_name)
            return fn(store, *args)
        except Exception as e:
            raise Exception(f"WASM call failed: {e}")