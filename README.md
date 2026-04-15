# WebAssembly-Based Language Interoperability Framework

## Overview

This project implements a **Python-based framework for cross-language interoperability using WebAssembly (WASM)**. It enables programs written in different languages (such as C/C++ and Rust) to be compiled into WASM modules and executed through a unified runtime.

The system abstracts away language-specific differences and provides a **generic, extensible interface** for invoking functions across modules using a common ABI.

---

## Key Idea

Instead of directly calling functions with fixed signatures, this framework uses a **single generic entry point (`call_function`)** per module. Communication between the host (Python) and WASM modules is done using:

* Linear memory (shared buffer)
* Byte-level data exchange
* JSON-based serialization

This allows the system to support **dynamic function dispatch and arbitrary data types**.

---

## Features

* Multi-language support (C/C++, Rust → WASM)
* Unified runtime for loading and executing modules
* Generic ABI for function invocation
* Dynamic function discovery (`get_functions`)
* Support for multiple data types:

  * Integers
  * Strings
  * Arrays
  * Nested objects
* Batch execution and safe execution support
* Modular architecture (loader, runtime, ABI, memory manager, type system)

---

## Project Structure

```directory
.
├── build.py              # Compiles C/C++ and Rust to WASM
├── main.py               # Entry point for running the framework
├── plugins/              # Source plugins (C, C++, Rust)
│   ├── multi.c
│   ├── rust.rs
│   └── build/            # Generated WASM modules
├── host/
│   ├── runtime.py        # High-level execution interface
│   ├── loader.py         # WASM module loader
│   ├── abi.py            # ABI validation and invocation
│   ├── memory.py         # WASM memory management
│   └── typesys.py        # Serialization / deserialization
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

### 3. Install rust

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

---

## How It Works

### 1. Compilation

Source files are compiled into WASM modules:

* C/C++ → via Emscripten
* Rust → via rustc (wasm32 target)

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
rt.call(ctx, "sum", [1, 2, 3])
```

Internally:

1. Arguments are serialized to JSON
2. Written into WASM memory
3. `call_function` is invoked
4. Result is returned as JSON
5. Deserialized into Python

---

## ABI Contract

Each WASM module must export the following functions:

* `init()` – initialize module
* `cleanup()` – cleanup resources
* `malloc(size)` – allocate memory
* `free(ptr)` – free memory
* `call_function(ptr, len)` – main dispatcher
* `get_functions()` – return available functions

---

## Limitations

* Performance overhead due to JSON serialization
* No static type safety (runtime errors possible)
* Manual parsing in plugins (basic implementation)
* Memory leaks possible if not handled carefully
* Limited debugging visibility inside WASM
* Not optimized for high-performance workloads

---

## Future Improvements

* Replace JSON with binary serialization (for speed)
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
* Rust (wasm32 target)
* Python (core framework)

---

## Conclusion

This project demonstrates how WebAssembly can be used as a **universal compilation target** to enable interoperability between different programming languages.

It highlights the trade-off between:

* flexibility and generality
* vs performance and type safety

and provides a solid foundation for building more advanced runtime systems.

---
