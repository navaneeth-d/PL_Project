import traceback

from host.abi import ABIManager
from host.error import WASMRuntimeError
from host.loader import Loader
from host.memory import MemoryManager
from host.typesys import TypeSystem
import json


class Runtime:
    def __init__(self):
        self._loader = Loader()
        self._abi = ABIManager()
        self._mem_mgr = MemoryManager()
        self._typesys = TypeSystem()
        self._fn_map = {}
        self._contexts = {}


    def _resolve_ctx(self, ctx: str) -> dict[str, any]:
        if isinstance(ctx, str) and ctx in self._contexts:
            return self._contexts[ctx]
        raise WASMRuntimeError(f"Unknown module id: {ctx}")


    def _encode_module_id(self, path: str) -> str:
        import base64
        return base64.b64encode(path.encode('utf-8')).decode('utf-8')

    
    def _next_module_id(self, path: str) -> str:
        if path not in self._contexts:
            return self._encode_module_id(path)

        idx = 2
        while f"{path}#{idx}" in self._contexts:
            idx += 1
        return self._encode_module_id(f"{path}#{idx}")


    def _validate_functions(self, fn_map: dict[str, dict[str, any]]):
        for item in fn_map:
            if 'name' not in item or 'id' not in item or 'args' not in item or 'return' not in item:
                raise WASMRuntimeError(f"Function(s) in metadata is missing required fields")
            
            fn_name = item['name']

            if not isinstance(item['id'], int):
                raise WASMRuntimeError(f"Function {fn_name} has invalid id type")
            
            if not isinstance(item['args'], list):
                raise WASMRuntimeError(f"Function {fn_name} has invalid args type")
            
            if not item['return'] in ("int", "string", "null", "list[int]"):
                raise WASMRuntimeError(f"Function {fn_name} has invalid return type")


    def _load_functions(self, ctx: dict[str, any]):
        module_id = ctx['module_id']
        if module_id in self._fn_map:
            return
        
        fn_str = self._abi.get_functions(
            ctx["store"],
            ctx["instance"],
            self._mem_mgr,
            self._typesys
        )
        
        fn_json = json.loads(fn_str)

        self._validate_functions(fn_json['functions'])
        self._abi.validate_functions(ctx['store'], ctx['instance'], self._mem_mgr, self._typesys, fn_json['functions'])

        self._fn_map[module_id] = {}
        
        for fn in fn_json['functions']:
            self._fn_map[module_id][fn["name"]] = fn


    def load_module(self, path: str):
        ctx = self._loader.load(path)
        module_id = self._next_module_id(path)
        ctx['module_id'] = module_id

        store = ctx['store']
        instance = ctx['instance']

        self._abi.validate_exports(store, instance)
        self._abi.call_init(store, instance)
        
        self._load_functions(ctx)
        
        self._contexts[module_id] = ctx

        return module_id
    

    def unload_module(self, ctx: str):
        ctx = self._resolve_ctx(ctx)
        self._cleanup(ctx)
        module_id = ctx['module_id']
        if module_id in self._fn_map:
            del self._fn_map[module_id]
        if module_id in self._contexts:
            del self._contexts[module_id]


    def get_modules(self):
        return list(self._fn_map.keys())
    

    def get_functions(self, ctx: str):
        ctx = self._resolve_ctx(ctx)
        
        module_id = ctx['module_id']
        if module_id not in self._fn_map:
            raise WASMRuntimeError(f"{module_id} was not loaded or has no function metadata")
        
        module_fns = self._fn_map[module_id]
        formatted_map = ""

        for name, details in module_fns.items():
            formatted_map += f"{name}: " + "{"
            formatted_map += f"\n    args: {details['args']},"
            formatted_map += f"\n    return: {details['return']}"
            formatted_map += "\n}\n"

        return formatted_map    
    

    def _resolve_req(self, ctx: dict[str, any], func_name: str, args: list) -> int:
        module_id = ctx['module_id']
        if module_id not in self._fn_map:
            raise WASMRuntimeError(f"{module_id} was not loaded or has no function metadata")
        module_fns = self._fn_map[module_id]

        if func_name not in module_fns:
            raise WASMRuntimeError(f"Function {func_name} not found in module {module_id}")
        
        fn_details = module_fns[func_name]
        expected_args = fn_details['args']

        if len(expected_args) != len(args):
            raise WASMRuntimeError(f"Function {func_name} expects {len(expected_args)} arguments but got {len(args)}")
        
        for i, (expected, actual) in enumerate(zip(expected_args, args)):
            if expected == "int":
                if not isinstance(actual, int):
                    raise WASMRuntimeError(f"Argument {i+1} of function {func_name} expects an integer")
            
            elif expected == "string":
                if not isinstance(actual, str):
                    raise WASMRuntimeError(f"Argument {i+1} of function {func_name} expects a string")
            
            elif expected == "list[int]":
                if isinstance(actual, list):
                    if not all(isinstance(x, int) for x in actual):
                        raise WASMRuntimeError(f"Argument {i+1} of function {func_name} expects a list of integers")
                else: 
                    raise WASMRuntimeError(f"Argument {i+1} of function {func_name} expects a list")
            else:
                raise WASMRuntimeError(f"Argument {i+1} of function {func_name} has an unsupported type")

        return {"function": fn_details['id'], "args": args, 'argspec': expected_args}
    
    
    def _execute(self, ctx: dict[str, any], func_name: str, args: list):
        req = self._resolve_req(ctx, func_name, args)

        return self._abi.call_function(
            ctx["store"],
            ctx["instance"],
            self._mem_mgr,
            self._typesys,
            req
        )
    

    def call(self, ctx: str, func_name: str, *args):
        try:
            ctx = self._resolve_ctx(ctx)
            return self._execute(ctx, func_name, list(args))
        except Exception as e:
            print(traceback.format_exc())

    def run(self, path: str, func_name: str, *args):
        module_id = None
        try:
            module_id = self.load_module(path)
            ctx = self._resolve_ctx(module_id)
            return self._execute(ctx, func_name, list(args))
        except Exception as e:
            return f'[WASM Runtime Error] {e}'
        finally:
            if module_id and module_id in self._contexts:
                self.unload_module(module_id)


    def _cleanup(self, ctx: dict[str, any]):
        self._abi.call_cleanup(
            ctx["store"],
            ctx["instance"]
        )