from host.runtime import Runtime


if __name__ == "__main__":

    rt = Runtime()

    ctx = rt.load_module("plugins/build/example.wasm")

    print("\n[C] Plugin Functions")
    print(rt.get_functions(ctx))


    print("\n[C] Sum of array [1, 2, 3, 4, 5]:")
    res = rt.call(ctx, "sumarray", [1, 2, 3, 4, 5])
    print(f"Final sum: {res}")


    print("\n[C] Sum of 10 and 20:")
    res = rt.call(ctx, "sumab", 10, 20)
    print(f"Final sum: {res}")


    print("\n[C] Greeting:")
    name = input('Enter ur name: ')
    res = rt.call(ctx, "greet", name)
    print(f"Greeting: {res}")


    print("\n[C] Function with no return:")
    res = rt.call(ctx, "noReturn")
    print(f"Result: {res}")

    print("\n[C] Calling non-existent function:")
    res = rt.call(ctx, "doesNotExist")
    print(f"Result: {res}")

    rt.unload_module(ctx)

    print("\n[C] Calling function after unloading module:")
    res = rt.call(ctx, "sumab", 10, 20)
    print(f"Result: {res}")

    print("\n[C] Running without loading the module:")
    res = rt.run('plugins/build/example.wasm', "sumab", 100, 20)
    print(f"Result: {res}")
