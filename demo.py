from host.runtime import Runtime


if __name__ == "__main__":

    rt = Runtime()

<<<<<<< HEAD
=======
    c_plugin = rt.load_module("plugins/build/example.wasm")

>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    # ── C PLUGIN ──────────────────────────────────────────
    ctx = rt.load_module("plugins/build/example_c.wasm")

    print("\n[C] Plugin Functions")
    print(rt.get_functions(c_plugin._module_id))


    print("\n[C] Sum of array [1, 2, 3, 4, 5]:")
<<<<<<< HEAD
    res = rt.sumarray(ctx, [1, 2, 3, 4, 5])
=======
    res = c_plugin.sumarray([1, 2, 3, 4, 5])
>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    print(f"Final sum: {res}")


    print("\n[C] Sum of 10 and 20:")
<<<<<<< HEAD
    res = rt.sumab(ctx, 10, 20)
=======
    res = c_plugin.sumab(10, 20)
>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    print(f"Final sum: {res}")


    print("\n[C] Greeting:")
    name = input('Enter ur name: ')
<<<<<<< HEAD
    res = rt.greet(ctx, name)
=======
    res = c_plugin.greet(name)
>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    print(f"Greeting: {res}")


    print("\n[C] Function with no return:")
<<<<<<< HEAD
    res = rt.noReturn(ctx)
    print(f"Result: {res}")

    print("\n[C] Function Returns array:")
    res = rt.doubleArray(ctx, [3, 1, 34, 932])
    print(f"Result: {res}")

    print("\n[C] Calling non-existent function:")
    res = rt.doesNotExist(ctx)
=======
    res = c_plugin.noReturn()
    print(f"Result: {res}")

    print("\n[C] Calling non-existent function:")
    res = c_plugin.doesNotExist()
>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    print(f"Result: {res}")

    rt.unload_module(c_plugin._module_id)

    print("\n[C] Calling function after unloading module:")
<<<<<<< HEAD
    res = rt.sumab(ctx, 10, 20)
=======
    res = rt.call(c_plugin._module_id, "sumab", 10, 20)
>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    print(f"Result: {res}")

    print("\n[C] Running without loading the module:")
    res = rt.run('plugins/build/example.wasm', "sumab", 100, 20)
    print(f"Result: {res}")

   
    # ── RUST PLUGIN ──────────────────────────────────────────
    rust_plugin = rt.load_module("plugins/build/example_rust.wasm")

    print("\n[Rust] Plugin Functions")
    print(rt.get_functions(rust_plugin._module_id))

    print("\n[Rust] factorial(10):")
<<<<<<< HEAD
    res = rt.factorial(rust_ctx, 10)
    print(f"Result: {res}")

    print("\n[Rust] fibonacci(15):")
    res = rt.fibonacci(rust_ctx, 15)
    print(f"Result: {res}")

    print("\n[Rust] is_prime(97):")
    res = rt.is_prime(rust_ctx, 97)
    print(f"Result: {res}  (1 = prime, 0 = not prime)")

    print("\n[Rust] is_prime(100):")
    res = rt.is_prime(rust_ctx, 100)
=======
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
>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    print(f"Result: {res}  (1 = prime, 0 = not prime)")

    print("\n[Rust] Greeting:")
    name = input('Enter your name for Rust: ')
<<<<<<< HEAD
    res = rt.greet(rust_ctx, name)
    print(f"Greeting: {res}")

    print("\n[Rust] Function with no return:")
    res = rt.noReturn(rust_ctx)
    print(f"Result: {res}")

    print("\n[Rust] Number of args passed (expected 2):")
    res = rt.num_of_args(rust_ctx, 1, 2)
=======
    res = rust_plugin.greet(name)
    print(f"Greeting: {res}")

    print("\n[Rust] Function with no return:")
    res = rust_plugin.noReturn()
    print(f"Result: {res}")

    print("\n[Rust] Number of args passed (expected 3):")
    res = rust_plugin.num_of_args("A", "B", "C")
>>>>>>> d65e460 (Added Pluginproxy to runtime.py)
    print(f"Result: {res}")


    rt.unload_module(rust_plugin._module_id)
