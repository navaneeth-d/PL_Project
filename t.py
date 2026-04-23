from host.context import Context
from host.runtime import Runtime

rt = Runtime()

ctx = rt.load_module("plugins/build/example_c.wasm")
print(rt.sum( 1, 2))
print(rt.noReturn(ctx))