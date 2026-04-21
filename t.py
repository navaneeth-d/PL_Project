from host.runtime import Runtime

rt = Runtime()

ctx = rt.load_module("plugins/build/example_c.wasm")

print(rt._fn_map[ctx])