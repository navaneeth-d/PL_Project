from host.runtime import Runtime


def c():
    rt = Runtime()

    print("\n[Loading Module]")
    ctx = rt.load_module("plugins/build/trialforc.wasm")

    print("\n[Available Functions]")
    print(rt.get_functions(ctx))

    print("\n[Execution]")

    # ---- int result ----
    print("sum:", rt.call(ctx, "sum", [1, 2, 3, 4]))

    # ---- int result ----
    print("mul:", rt.call(ctx, "mul", [2, 3, 4]))

    # ---- string ----
    print("greet:", rt.call(ctx, "greet", []))

    # ---- array ----
    print("get_array:", rt.call(ctx, "get_array", []))

    # ---- mixed ----
    print("mixed:", rt.call(ctx, "mixed", []))

    print("\n[Cleanup]")
    rt.cleanup(ctx)

def rust():
    rt = Runtime()

    # ---------- load modules ----------
    print("\n[Loading Modules]")
    mul_ctx = rt.load_module("plugins/build/trialforrust.wasm")

    # ---------- inspect ----------
    print("\n[Available Functions]")
    print("Rust plugin:", rt.get_functions(mul_ctx))

    # ---------- execute ----------
    print("\n[Execution]")


    res = rt.call(mul_ctx, "mul", [2, 3, 4])
    print("mul result:", res)

    # ---------- batch ----------
    print("\n[Batch Execution]")
    batch_results = rt.batch_call(mul_ctx, [
        ("mul", [1, 2]),
        ("mul", [10, 20, 30])
    ])
    print("batch:", batch_results)

    # ---------- safe execution ----------
    print("\n[Safe Execution]")
    safe = rt.safe_execute(mul_ctx, "unknown_func", [])
    print("safe result:", safe)

    # ---------- cleanup ----------
    print("\n[Cleanup]")
    rt.cleanup(mul_ctx)


if __name__ == "__main__":
    choice = int(input("Run (1) C or (2) Rust plugin? "))
    if choice == 1:
        c()
    else:
        rust()