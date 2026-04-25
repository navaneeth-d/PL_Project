import traceback
from typing import Any

from host.abi import ABIManager
from host.context import Context
from host.error import WASMRuntimeError
from host.loader import Loader
from host.memory import MemoryManager
from host.typesys import TypeSystem
import json

class PluginProxy:
    def __init__(self, runtime, module_id):
        self._runtime = runtime
        self._module_id = module_id
        
    def __getattr__(self, func_name):
        def wrapper(*args):
            return self._runtime.call(self._module_id, func_name, *args)
        return wrapper


class Runtime:
    def __init__(self):
        self._loader = Loader()
        self._abi = ABIManager()
        self._mem_mgr = MemoryManager()
        self._typesys = TypeSystem()
        self._contexts: dict[str, Context] = {}

    
    def __getattr__(self, name):
        def method(ctx: Context | None, *args):
            return self.call(ctx, name, *args)
        return method


    def _resolve_ctx(self, ctx: Context | None, fn_name: str) -> Context:
        if ctx is None:
            if len(self._contexts) == 0:
                raise WASMRuntimeError("No modules loaded")
            elif len(self._contexts) == 1:
                ctx = list(self._contexts.values())[0]
            else:
                raise WASMRuntimeError(f"Multiple modules loaded, context must be specified to call {fn_name}")
        if not isinstance(ctx, Context):
            raise WASMRuntimeError("Context object expected")
        
        if ctx.module_id not in self._contexts:
            raise WASMRuntimeError(f"Unknown module: {ctx}")
        return self._contexts[ctx.module_id]

    
    def _next_module_id(self, path: str) -> str:

        base_module_id = path
        if base_module_id not in self._contexts:
            return base_module_id

        idx = 2
        while f"{path}#{idx}" in self._contexts:
            idx += 1
        return f"{path}#{idx}"


    def _validate_metadata(self, ctx: Context, fns: list[dict[str, Any]]):
        for item in fns:
            if 'name' not in item or 'id' not in item or 'args' not in item or 'return' not in item:
                raise WASMRuntimeError(f"Function(s) in metadata is missing required fields")
            
            fn_name = item['name']

            if not isinstance(item['id'], int):
                raise WASMRuntimeError(f"Function {fn_name} has invalid id type")
            
            if not isinstance(item['args'], list):
                raise WASMRuntimeError(f"Function {fn_name} has invalid args type")
            
            if not item['return'] in ("int", "string", "null", "list[int]"):
                raise WASMRuntimeError(f"Function {fn_name} has invalid return type")
            
            for arg_type in item['args']:
                if arg_type not in ("int", "string", "list[int]"):
                    raise WASMRuntimeError(f"Function {fn_name} has invalid argument type: {arg_type}")
            
        self._abi.validate_function_calls(
            ctx.store,
            ctx.instance,
            self._mem_mgr, 
            self._typesys, 
            fns
        )


    def _load_functions(self, ctx: Context):
        fn_str = self._abi.get_functions(
            ctx.store,
            ctx.instance,
            self._mem_mgr,
            self._typesys
        )
        
        metadata = json.loads(fn_str)
        self._validate_metadata(ctx, metadata['functions'])

        fn_map: dict[str, dict[str, Any]] = {}
        for fn in metadata['functions']:
            fn_map[fn["name"]] = fn
        ctx.functions = fn_map


    def load_module(self, path: str):
        raw_ctx = self._loader.load(path)
        module_id = self._next_module_id(path)
        ctx = Context(
            module_id=module_id,
            store=raw_ctx['store'],
            instance=raw_ctx['instance'],
            functions={}
        )
        store = ctx.store
        instance = ctx.instance

        self._abi.validate_exports(store, instance)
        self._abi.call_init(store, instance)
        
        self._load_functions(ctx)
        self.contexts[module_id] = ctx
        
        return PluginProxy(self, module_id)
    

    def unload_module(self, ctx: Context):
        ctx = self._resolve_ctx(ctx)
        module_id = ctx.module_id
        self._cleanup(ctx)

        if module_id in self._contexts:
            del self._contexts[module_id]


    def get_modules(self):
        return list(self._contexts.values())
    

    def get_functions(self, ctx: Context):
        ctx = self._resolve_ctx(ctx)
        
        if not ctx.functions:
            raise WASMRuntimeError(f"{ctx.module_id} was not loaded or has no function metadata")

        module_fns = ctx.functions
        formatted_map = ""

        for name, details in module_fns.items():
            formatted_map += f"{name}: " + "{"
            formatted_map += f"\n    args: {details['args']},"
            formatted_map += f"\n    return: {details['return']}"
            formatted_map += "\n}\n"

        return formatted_map    
    

    def _resolve_req(self, ctx: Context, func_name: str, args: list) -> int:
        module_id = ctx.module_id
        if not ctx.functions:
            raise WASMRuntimeError(f"{module_id} was not loaded or has no function metadata")
        
        module_fns = ctx.functions

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

        return {
            "function": fn_details['id'], 
            "args": args, 
            'argspec': expected_args
        }
    
    
    def _execute(self, ctx: Context, func_name: str, args: list):
        req = self._resolve_req(ctx, func_name, args)
        return self._abi.call_function(
            ctx.store,
            ctx.instance,
            self._mem_mgr,
            self._typesys,
            req
        )
    

    def call(self, ctx: Context | None, func_name: str, *args):
        try:
            ctx = self._resolve_ctx(ctx)
            return self._execute(ctx, func_name, list(args))
        except Exception as e:
            print(traceback.format_exc())
            

    def run(self, path: str, func_name: str, *args):
        ctx = None
        try:
            ctx = self.load_module(path)
            ctx = self._resolve_ctx(ctx)
            return self._execute(ctx, func_name, list(args))
        except Exception as e:
            return f'[WASM Runtime Error] {e}'
        finally:
            if ctx and ctx.module_id in self._contexts:
                self.unload_module(ctx)


    def _cleanup(self, ctx: Context):
        self._abi.call_cleanup(
            ctx.store,
            ctx.instance
        )