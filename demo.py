from host.runtime import Runtime

rt = Runtime()

ctx = rt.load_module("plugins/build/trialforc.wasm")

print(rt.get_functions(ctx))

res = rt.call(ctx, "sumarray", [[1, 2, 3, 4, 5]])
print(res)

res = rt.call(ctx, "mul", [[1, 2, 3, 4, 5]])
print(res)

res = rt.call(ctx, "sumab", [10, 20])
print(res)

name=input('Enter ur name: ')
res = rt.call(ctx, "greet", [name])
print(res)

res = rt.call(ctx, "noReturn", [])
print(res)