from host.abi import ABIManager
from host.error import WASMRuntimeError
from host.loader import Loader
from host.memory import MemoryManager
from host.typesys import TypeSystem
import json


class Runtime:
    def __init__(self):
        self.loader = Loader()
        self.abi = ABIManager()
        self.mem_mgr = MemoryManager()
        self.typesys = TypeSystem()
        self.fn_map = {}
        self.contexts = {}


    def _resolve_ctx(self, ctx: str | dict[str, any]) -> dict[str, any]:
        if isinstance(ctx, dict):
            return ctx
        if isinstance(ctx, str) and ctx in self.contexts:
            return self.contexts[ctx]
        raise WASMRuntimeError(f"Unknown module id: {ctx}")


    def _next_module_id(self, path: str) -> str:
        if path not in self.contexts:
            return path

        idx = 2
        while f"{path}#{idx}" in self.contexts:
            idx += 1
        return f"{path}#{idx}"


    def _load_functions(self, ctx: dict[str, any]):
        module_id = ctx['module_id']
        if module_id in self.fn_map:
            return
        
        fn_str = self.abi.get_functions(
            ctx["store"],
            ctx["instance"],
            self.mem_mgr,
            self.typesys
        )
        
        fn_json = json.loads(fn_str)
        self.fn_map[module_id] = {}
        
        for fn in fn_json['functions']:
            self.fn_map[module_id][fn["name"]] = fn


    def load_module(self, path: str):
        ctx = self.loader.load(path)
        module_id = self._next_module_id(path)
        ctx['module_id'] = module_id

        store = ctx['store']
        instance = ctx['instance']

        self.abi.validate(store, instance)
        self.abi.call_init(store, instance)
        self._load_functions(ctx)

        self.contexts[module_id] = ctx

        return module_id
    

    def unload_module(self, ctx: str):
        ctx = self._resolve_ctx(ctx)
        self._cleanup(ctx)
        module_id = ctx['module_id']
        if module_id in self.fn_map:
            del self.fn_map[module_id]
        if module_id in self.contexts:
            del self.contexts[module_id]


    def get_modules(self):
        return list(self.fn_map.keys())
    

    def get_functions(self, ctx: str):
        ctx = self._resolve_ctx(ctx)
        
        module_id = ctx['module_id']
        if module_id not in self.fn_map:
            raise WASMRuntimeError(f"Function metadata not loaded for module {module_id}")
        module_fns = self.fn_map[module_id]
        formatted_map = ""

        for name, details in module_fns.items():
            formatted_map += f"{name}: " + "{"
            formatted_map += f"\n    args: {details['args']},"
            formatted_map += f"\n    return: {details['return']}"
            formatted_map += "\n}\n"

        return formatted_map    
    
    
    def _execute(self, ctx: dict[str, any], func_name: str, args: list):
        module_id = ctx['module_id']
        if module_id not in self.fn_map:
            raise WASMRuntimeError(f"Function metadata not loaded for module {module_id}")
        module_fns = self.fn_map[module_id]

        if func_name not in module_fns:
            raise WASMRuntimeError(f"Function {func_name} not found in module {module_id}")
        
        fn_id = module_fns[func_name]["id"]

        return self.abi.call_function(
            ctx["store"],
            ctx["instance"],
            self.mem_mgr,
            self.typesys,
            fn_id,
            args
        )
    

    def call(self, ctx: str, func_name: str, *args):
        try:
            ctx = self._resolve_ctx(ctx)
            return self._execute(ctx, func_name, list(args))
        except Exception as e:
            return f"[WASM Runtime Error] {e}"

    def run(self, path: str, func_name: str, *args):
        module_id = None
        try:
            module_id = self.load_module(path)
            ctx = self._resolve_ctx(module_id)
            return self._execute(ctx, func_name, list(args))
        except Exception as e:
            return f'[WASM Runtime Error] {e}'
        finally:
            if module_id and module_id in self.contexts:
                self.unload_module(module_id)


    def _cleanup(self, ctx: dict[str, any]):
        self.abi.call_cleanup(
            ctx["store"],
            ctx["instance"]
        )