from host.abi import ABIManager
from host.loader import Loader
from host.memory import MemoryManager
from host.typesys import TypeSystem


class Runtime:
    def __init__(self):
        self.loader = Loader()
        self.abi = ABIManager()
        self.mem_mgr = MemoryManager()
        self.typesys = TypeSystem()

    def load_module(self, path: str) -> dict[str, any]:
        ctx = self.loader.load(path)

        store = ctx['store']
        instance = ctx['instance']

        self.abi.validate(store, instance)
        self.abi.call_init(store, instance)

        return ctx
    
    def get_functions(self, ctx: dict[str, any]) -> list[str]:
        return self.abi.get_functions(
            ctx["store"],
            ctx["instance"],
            self.mem_mgr,
            self.typesys
        )
    
    def call(self, ctx: dict[str, any], func_name: str, args: list) -> any:
        result = self.abi.call_function(
            ctx["store"],
            ctx["instance"],
            self.mem_mgr,
            self.typesys,
            func_name,
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