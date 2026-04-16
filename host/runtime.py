from host.abi import ABIManager
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


    def load_functions(self, ctx: dict[str, any]) -> None:
        if self.fn_map:
            return
        
        fn_str = self.abi.get_functions(
            ctx["store"],
            ctx["instance"],
            self.mem_mgr,
            self.typesys
        )
        
        fn_json = json.loads(fn_str)
        
        for fn in fn_json['functions']:
            self.fn_map[fn["name"]] = fn


    def load_module(self, path: str) -> dict[str, any]:
        ctx = self.loader.load(path)

        store = ctx['store']
        instance = ctx['instance']

        self.abi.validate(store, instance)
        self.abi.call_init(store, instance)

        return ctx
    

    def get_functions(self, ctx: dict[str, any]) -> dict[str, any]:
        self.load_functions(ctx)
        formatted_map = ""

        for name, details in self.fn_map.items():
            formatted_map += f"{name}: " + "{"
            formatted_map += f"\n    args: {details['args']},"
            formatted_map += f"\n    return: {details['return']}"
            formatted_map += "\n}\n"

        return formatted_map    
    

    def call(self, ctx: dict[str, any], func_name: str, args: list) -> any:
        self.load_functions(ctx)

        if func_name not in self.fn_map:
            raise Exception(f"Function {func_name} not found in module")
        
        fn_id = self.fn_map[func_name]["id"]
        result = self.abi.call_function(
            ctx["store"],
            ctx["instance"],
            self.mem_mgr,
            self.typesys,
            fn_id,
            args
        )
        return result
    

    def run(self, path: str, func_name: str, args: list) -> any:
        ctx = self.load_module(path)
        result = self.call(ctx, func_name, args)
        self.cleanup(ctx)
        return result
    

    def cleanup(self, ctx: dict[str, any]) -> None:
        self.abi.call_cleanup(
            ctx["store"],
            ctx["instance"]
        )


    def safe_execute(self, ctx: dict[str, any], func_name: str, args: list) -> dict[str, any]:
        try:
            return self.call(ctx, func_name, args)
        except Exception as e:
            return {"error": str(e)}
    

    def batch_call(self, ctx: dict[str, any], calls: list[tuple[str, list]]) -> list:
        results = []
        for fn, args in calls:
            results.append(self.call(ctx, fn, args))
        return results