from host.runtime import Runtime


if __name__ == "__main__":

    rt = Runtime()

    ctx = rt.load_module("plugins/build/example.wasm")

    # ── C PLUGIN ──────────────────────────────────────────
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
   
    # ── RUST PLUGIN ──────────────────────────────────────────
    rust_ctx = rt.load_module("plugins/build/example_rust.wasm")

    print("\n[Rust] Plugin Functions")
    print(rt.get_functions(rust_ctx))

    print("\n[Rust] factorial(10):")
    res = rt.call(rust_ctx, "factorial", 10)
    print(f"Result: {res}")

    print("\n[Rust] fibonacci(15):")
    res = rt.call(rust_ctx, "fibonacci", 15)
    print(f"Result: {res}")

    print("\n[Rust] is_prime(97):")
    res = rt.call(rust_ctx, "is_prime", 97)
    print(f"Result: {res}  (1 = prime, 0 = not prime)")

    print("\n[Rust] is_prime(100):")
    res = rt.call(rust_ctx, "is_prime", 100)
    print(f"Result: {res}  (1 = prime, 0 = not prime)")

    print("\n[Rust] Greeting:")
    name = input('Enter your name for Rust: ')
    res = rt.call(rust_ctx, "greet", name)
    print(f"Greeting: {res}")

    print("\n[Rust] Function with no return:")
    res = rt.call(rust_ctx, "noReturn")
    print(f"Result: {res}")

    print("\n[Rust] Number of args passed (expected 3):")
    res = rt.call(rust_ctx, "num_of_args", "A", "B", "C")
    print(f"Result: {res}")


    rt.unload_module(rust_ctx)
