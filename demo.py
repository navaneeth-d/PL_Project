from host.runtime import Runtime


if __name__ == "__main__":

    rt = Runtime()

    # ── C PLUGIN ──────────────────────────────────────────
    c_plugin = rt.load_module("plugins/build/example_c.wasm")

    print("\n[C] Plugin Functions")
    print(rt.get_functions(c_plugin._ctx))


    print("\n[C] Sum of array [1, 2, 3, 4, 5]:")
    res = c_plugin.sumarray([1, 2, 3, 4, 5])
    print(f"Final sum: {res}")


    print("\n[C] Sum of 10 and 20:")
    res = c_plugin.sumab(10, 20)
    print(f"Final sum: {res}")


    print("\n[C] Greeting:")
    name = input('Enter ur name: ')
    res = c_plugin.greet(name)
    print(f"Greeting: {res}")


    print("\n[C] Function with no return:")
    res = c_plugin.noReturn()
    print(f"Result: {res}")

    print("\n[C] Function Returns array:")
    res = c_plugin.doubleArray([3, 1, 34, 932])
    print(f"Result: {res}")

    print("\n[C] Calling non-existent function:")
    res = c_plugin.doesNotExist()
    print(f"Result: {res}")

    rt.unload_module(c_plugin._ctx)

    print("\n[C] Calling function after unloading module:")
    res = c_plugin.sumab(10, 20)
    print(f"Result: {res}")

    print("\n[C] Running without loading the module:")
    res = rt.run('plugins/build/example_c.wasm', "sumab", 100, 20)
    print(f"Result: {res}")

   
    # ── RUST PLUGIN ──────────────────────────────────────────
    rust_plugin = rt.load_module("plugins/build/example_rust.wasm")

    print("\n[Rust] Plugin Functions")
    print(rt.get_functions(rust_plugin._ctx))

    print("\n[Rust] factorial(10):")
    res = rust_plugin.factorial(10)
    print(f"Result: {res}")

    print("\n[Rust] fibonacci(15):")
    res = rust_plugin.fibonacci(15)
    print(f"Result: {res}")

    print("\n[Rust] is_prime(97):")
    res = rust_plugin.is_prime(97)
    print(f"Result: {res}  (1 = prime, 0 = not prime)")

    print("\n[Rust] is_prime(100):")
    res = rust_plugin.is_prime(100)
    print(f"Result: {res}  (1 = prime, 0 = not prime)")

    print("\n[Rust] Greeting:")
    name = input('Enter your name for Rust: ')
    res = rust_plugin.greet(name)
    print(f"Greeting: {res}")

    print("\n[Rust] Function with no return:")
    res = rust_plugin.noReturn()
    print(f"Result: {res}")

    print("\n[Rust] Number of args passed (expected 2):")
    res = rust_plugin.num_of_args(1, 2)
    print(f"Result: {res}")

    rt.unload_module(rust_plugin._ctx)
