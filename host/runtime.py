import traceback
from typing import Any

from host.abi import ABIManager
from host.context import Context
from host.error import WASMRuntimeError
from host.loader import Loader
from host.memory import MemoryManager
from host.typesys import TypeSystem
from host.proxy import PluginProxy
import json


class Runtime:
    def __init__(self):
        self._loader = Loader()
        self._abi = ABIManager()
        self._mem_mgr = MemoryManager()
        self._typesys = TypeSystem()
        self._contexts: dict[str, Context] = {}


    def _resolve_ctx(self, ctx: Context | None, fn_name: str = "function") -> Context:
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
        '''This calls ABIManager.get functions(), decodes the returned JSON string, and
            rigorously validates the metadata (e.g., ensuring correct type signatures like int
            or list[int]) using Runtime. validate metadata(). It maps these into ctx.functions,
            creating the routing table.'''
        fn_str = self._abi.get_functions(
            ctx.store,
            ctx.instance,
            self._mem_mgr,
            self._typesys
        )
        
        metadata = json.loads(fn_str)
        self._validate_metadata(ctx, metadata['functions'])

        fn_map: dict[str, list[dict[str, Any]]] = {}
        for fn in metadata['functions']:
            if fn["name"] not in fn_map:
                fn_map[fn["name"]] = []
            fn_map[fn["name"]].append(fn)
        ctx.functions = fn_map


    # Initialization of .wasm modules
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

        # Check if module exports all the functions(init, cleanup, malloc, free, call_functions, get_functions)
        self._abi.validate_exports(store, instance)

        # It safely invokes the plugin’s init export using the invoke() wrapper to prevent host crashes during setup
        self._abi.call_init(store, instance)
        
        # Quering of plugins via self._load_functions()
        self._load_functions(ctx)
        self._contexts[module_id] = ctx
        
        return PluginProxy(self, ctx)
    

    def unload_module(self, plugin: PluginProxy):
        ctx = self._resolve_ctx(plugin._ctx)
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

        for name, overloads in module_fns.items():
            for details in overloads:
                formatted_map += f"{name}: " + "{"
                formatted_map += f"\n    args: {details['args']},"
                formatted_map += f"\n    return: {details['return']}"
                formatted_map += "\n}\n"


        return formatted_map    
    
    #It handles function overloading based on argument type
    def _resolve_req(self, ctx: Context, func_name: str, args: list) -> int:
        module_id = ctx.module_id
        if not ctx.functions:
            raise WASMRuntimeError(f"{module_id} was not loaded or has no function metadata")
            
        module_fns = ctx.functions

        if func_name not in module_fns:
            raise WASMRuntimeError(f"Function {func_name} not found in module {module_id}")
            
        candidates = module_fns[func_name]
        matched_fn = None

        # Check each overloaded version of the function
        for candidate in candidates:
            expected_args = candidate['args']
                
            # 1. Check length
            if len(expected_args) != len(args):
                continue
                
            # 2. Check types
            types_match = True
            for expected, actual in zip(expected_args, args):
                if expected == "int" and not isinstance(actual, int):
                    types_match = False
                elif expected == "string" and not isinstance(actual, str):
                    types_match = False
                elif expected == "list[int]":
                    if not isinstance(actual, list) or not all(isinstance(x, int) for x in actual):
                        types_match = False
                
            if types_match:
                matched_fn = candidate
                break  # We found the correct overload!

        if not matched_fn:
            raise WASMRuntimeError(f"No overloaded version of {func_name} matched the provided arguments.")

        return {
            "function": matched_fn['id'], 
            "args": args, 
            'argspec': matched_fn['args']
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
            return f'[WASM Runtime Error] {e}'
            

    def run(self, path: str, func_name: str, *args):
        ctx = None
        try:
            plugin = self.load_module(path)
            ctx = plugin._ctx
            return self._execute(ctx, func_name, list(args))
        except Exception as e:
            return f'[WASM Runtime Error] {e}'
        finally:
            if ctx and ctx.module_id in self._contexts:
                self.unload_module(plugin)


    def _cleanup(self, ctx: Context):
        self._abi.call_cleanup(
            ctx.store,
            ctx.instance
        )