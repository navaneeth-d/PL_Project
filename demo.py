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


    print("\n[C] Calling greet with ONE string:")
    name = input('Enter ur name: ')
    res = c_plugin.greet(name)
    print(f"Greeting: {res}")

    print("\n[C] Calling greet with TWO strings:")
    first_name = input('Enter your first name: ')
    last_name = input('Enter your last name: ')
    res_full = c_plugin.greet(first_name, last_name)
    print(f"Full Greeting: {res_full}")



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

    print("\n[Rust] Sum of array [1, 2, 3, 4, 5]:")
    res = rust_plugin.sumarray([1, 2, 3, 4, 5])
    print(f"Final sum: {res}")

    print("\n[Rust] Sum of 10 and 20:")
    res = rust_plugin.sumab(10, 20)
    print(f"Final sum: {res}")

    print("\n[Rust] Calling greet with ONE string:")
    name = input('Enter your name for Rust: ')
    res = rust_plugin.greet(name)
    print(f"Greeting: {res}")

    print("\n[Rust] Calling greet with TWO string:")
    firstname = input('Enter your first name for Rust: ')
    lastname = input('Enter your last name for Rust: ')
    res = rust_plugin.greet(firstname, lastname)
    print(f"Greeting: {res}")

    print("\n[Rust] Function with no return:")
    res = rust_plugin.noReturn()
    print(f"Result: {res}")

    print("\n[Rust] Function Returns array:")
    res = rust_plugin.doubleArray([3, 1, 34, 932])
    print(f"Result: {res}")

    print("\n[Rust] Calling non-existent function:")
    res = rust_plugin.doesNotExist()
    print(f"Result: {res}")

    rt.unload_module(rust_plugin._ctx)

    print("\n[Rust] Calling function after unloading module:")
    res = rust_plugin.sumab(10, 20)
    print(f"Result: {res}")

    print("\n[Rust] Running without loading the module:")
    res = rt.run('plugins/build/example_rust.wasm', "sumab", 100, 20)
    print(f"Result: {res}")
