from wasmtime import Instance, Store
from host.error import WASMRuntimeError
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
    
        
    def _invoke(self, store: Store, instance: Instance, fn_name: str, *args):
        '''Use this fn for init and cleanup to avoid crashing the host if they fail'''
        try:
            fn = self.get_function(store, instance, fn_name)
            return fn(store, *args)
        except Exception as e:
            raise WASMRuntimeError(f"{fn_name} {e}")
        
        
    def validate_exports(self, store: Store, instance: Instance):
        exports = instance.exports(store)
        for fn in self.reqd_fns:
            if fn not in exports:
                raise WASMRuntimeError(f"Missing required function: {fn}")
            
            
    def validate_functions(self, store, instance, mem_mgr, typesys, fn_list):
        def _get_dummy_args(argspec):
            dummy_args = []
            for arg in argspec:
                if arg == 'list[int]':
                    dummy_args.append([1, 2, 3])
                elif arg == 'int':
                    dummy_args.append(42)
                elif arg == 'string':
                    dummy_args.append("test")
                else:
                    raise WASMRuntimeError(f"Unsupported argument type: {arg}")
            return dummy_args

        for fn in fn_list:
            id, name, argspec, rettype = fn['id'], fn['name'], fn['args'], fn['return']
            args = _get_dummy_args(argspec)
            ret = self.call_function(store, instance, mem_mgr, typesys, {
                "function": id,
                "argspec": argspec,
                "args": args
            })

            if rettype == 'int' and not isinstance(ret, int):
                raise WASMRuntimeError(f"Function {name} expected to return int but got {type(ret)}")
            elif rettype == 'string' and not isinstance(ret, str):
                raise WASMRuntimeError(f"Function {name} expected to return string but got {type(ret)}")
            elif rettype == 'list[int]' and not (isinstance(ret, list) and all(isinstance(x, int) for x in ret)):
                raise WASMRuntimeError(f"Function {name} expected to return list[int] but got {type(ret)}")
            elif rettype == 'null' and ret is not None:
                raise WASMRuntimeError(f"Function {name} expected to return null but got {type(ret)}")
        
    
    def get_function(self, store: Store, instance: Instance, name: str):
        exports = instance.exports(store)
        if name not in exports:
            raise WASMRuntimeError(f"Missing required function: {name}")
        return exports[name]
    

    def call_init(self, store: Store, instance: Instance):
        self._invoke(store, instance, "init")


    def call_cleanup(self, store: Store, instance: Instance):
        self._invoke(store, instance, "cleanup")


    def get_functions(self, store: Store, instance: Instance, memory_mgr: MemoryManager, typesys: TypeSystem):
        ptr = self._invoke(store, instance, "get_functions")
        if not ptr:
            raise WASMRuntimeError("Plugin returned NULL metadata pointer")
        try:
            return typesys.from_wasm(memory_mgr, store, instance, ptr)
        finally:
            if ptr:
                memory_mgr.free(store, instance, ptr)


    def call_function(self, store: Store, instance: Instance, mem_mgr: MemoryManager, typesys: TypeSystem, req: dict[str, any]):
        ptr, size = typesys.to_wasm(mem_mgr, store, instance, req)
        res_ptr = None
        try:
            res_ptr = self._invoke(store, instance, "call_function", ptr, size)
            if not res_ptr:
                return None
            try:
                return typesys.from_wasm(mem_mgr, store, instance, res_ptr)
            finally:
                if res_ptr:
                    mem_mgr.free(store, instance, res_ptr)
        finally:
            if ptr:
                mem_mgr.free(store, instance, ptr)
