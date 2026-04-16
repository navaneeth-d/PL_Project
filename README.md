# WebAssembly-Based Language Interoperability Framework

## Overview

This project implements a **Python-based framework for cross-language interoperability using WebAssembly (WASM)**. It enables programs written in different languages (such as C/C++) to be compiled into WASM modules and executed through a unified runtime.

The system abstracts away language-specific differences and provides a **generic, extensible interface** for invoking functions across modules using a common ABI.

---

## Key Idea

Instead of directly calling functions with fixed signatures, this framework uses a **single generic entry point (`call_function`)** per module. Communication between the host (Python) and WASM modules is done using:

* Linear memory (shared buffer)
* Byte-level data exchange
* Binary argument/result encoding

This allows the system to support **dynamic function dispatch and arbitrary data types**.

---

## Features

* Multi-language plugin architecture (C/C++)
* Unified runtime for loading and executing modules
* Generic ABI for function invocation
* Dynamic function discovery (`get_functions`)
* Runtime name-to-ID function mapping for dispatch
* Support for multiple data types:
  * Integers
  * Strings
  * Arrays
  * Null returns
* Safe execution support
* Modular architecture (loader, runtime, ABI, memory manager, type system)

---

## Project Structure

```directory
.
├── build.py              # Compiles plugins to WASM (C/C++ path present)
├── demo.py               # Entry point for running the framework
├── new_plugin.py         # Auto-generate plugin template
├── plugins/              # Source plugins (C, C++)
│   ├── example.c
│   └── build/            # Generated WASM modules
├── host/
│   ├── runtime.py        # High-level execution interface
│   ├── loader.py         # WASM module loader
│   ├── abi.py            # ABI validation and invocation
│   ├── memory.py         # WASM memory management
│   ├── error.py          # Custom error class
│   └── typesys.py        # Binary encoding / decoding
```

---

## Setup

### 1. Install python dependencies

```sh
pip install -r requirements.txt
```

### 2. Install Emscripten (for C/C++ → WASM)

```sh
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk

# Install latest version
./emsdk install latest

# Activate it
./emsdk activate latest
```

---

## How It Works

### 1. Compilation

Source files are compiled into WASM modules:

* C/C++ → via Emscripten

```sh
python build.py
```

---

### 2. Loading Modules

Modules are loaded using the runtime:

```python
ctx = rt.load_module("plugins/build/module.wasm")
```

---

### 3. Function Discovery

Each module exposes available functions:

```python
rt.get_functions(ctx)
```

---

### 4. Function Execution

All calls go through a single entry point:

```python
rt.call(ctx, "sumarray", [1, 2, 3, 4, 5])
rt.call(ctx, "sumab", 10, 20)
```

Internally:

1. Function metadata is loaded and mapped by name
2. Function name is resolved to function ID
3. Arguments are encoded into a binary payload
4. Written into WASM memory
5. `call_function` is invoked
6. Binary result is decoded into Python values

---

## ABI Contract

Each WASM module must export the following functions:

* `init()` – initialize module
* `cleanup()` – cleanup resources
* `malloc(size)` – allocate memory
* `free(ptr)` – free memory
* `call_function(ptr, len)` – main dispatcher
* `get_functions()` – return function metadata including IDs and signatures

Input payload format (host → module):

1. `function_id` (4 bytes)
2. `num_args` (4 bytes)
3. For each argument:

    * `item_size` (4 bytes)
    * `item_count` (4 bytes)
    * raw argument bytes

Return payload format (module → host):

1. `total_length` (4 bytes)
2. `item_count` (4 bytes)
3. `item_size` (4 bytes)
4. raw result bytes

---

## Limitations

* Current binary protocol supports only int, string, int array, and null patterns used by the sample plugins
* No static type safety (runtime errors possible)
* Plugin and host protocol versions must stay aligned
* Memory leaks possible if not handled carefully
* Limited debugging visibility inside WASM
* Not optimized for high-performance workloads

---

## Future Improvements

* Extend binary protocol with richer and versioned type descriptors
* Introduce typed ABI for stronger guarantees
* Automatic wrapper/code generation for plugins
* Proper memory management (no leaks)
* Secure sandboxing and execution limits
* Parallel execution support

---

## Technologies Used

* WebAssembly
* Wasmtime (runtime)
* Emscripten (C/C++ → WASM)
* Python (core framework)

---

## Conclusion

This project demonstrates how WebAssembly can be used as a **universal compilation target** to enable interoperability between different programming languages.

It highlights the trade-off between:

* flexibility and generality
* vs performance and type safety

and provides a solid foundation for building more advanced runtime systems.

---
