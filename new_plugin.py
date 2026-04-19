from pathlib import Path
import re

def make_c_plugin(plugin_name: str) ->None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", plugin_name):
        raise ValueError("Plugin name must be a valid C identifier-style name")

    template = r"""/*
============================= CONTRACT / SCHEMA ==============================

Receive data layout:

    [func_id:4]
    [num_args:4]

    For each arg:
        [item_size:4]        // size of each element (e.g. int=4, char=1)
        [item_count:4]       // number of elements
        [data: ...]          // raw bytes


Return data layout:

    [total_length:4]         // total bytes including header
    [num_items:4]            // number of items
    [item_size:4]            // size of each item
    [data: ...]              // raw bytes

==============================================================================
*/

#include <stdlib.h>
#include <string.h>

#define EXPORT(name) __attribute__((export_name(name)))
typedef void *(*FuncPtr)(void *data, int num_args);

// !===== REQUIRED: lifecycle =====
EXPORT("init")
void init() {}

EXPORT("cleanup")
void cleanup() {}

// !===== REQUIRED: response helper (example implementation) =====
void *make_response(int count, int item_size, void *data)
{
    int total = 12 + (count * item_size);
    char *ptr = (char *)malloc(total);

    memcpy(ptr, &total, 4);
    memcpy(ptr + 4, &count, 4);
    memcpy(ptr + 8, &item_size, 4);
    memcpy(ptr + 12, data, count * item_size);

    return ptr;
}

// !===== REQUIRED: metadata =====
/*
Return JSON describing available functions.

Expected format:

{
  "functions": [
    {
      "id": int,
      "name": string,
      "args": string,
      "return": string
    }
  ]
}
*/
EXPORT("get_functions")
void *get_functions()
{
    // TODO: Replace with your own function metadata
    char *response = "{ \"functions\": \"[]\" }";
    return make_response(strlen(response), 1, response);
}

// !===== USER FUNCTIONS (examples, replace freely) =====
/*
Each function receives:
    data     → pointer to encoded arguments
    num_args → number of arguments

Must return:
    pointer to response buffer (see schema above)
*/
void *example_function(void *data, int num_args)
{
    // TODO: parse input using schema
    // TODO: compute result

    int result = 0; // example
    return make_response(1, 4, &result);
}

// !===== REQUIRED: dispatcher =====
/*
- Reads function ID
- Dispatches to correct function
- Must return valid response buffer
*/
EXPORT("call_function")
void *call_function(void *ptr, int len)
{
    FuncPtr funcs[] = {
        example_function // register your functions here
    };

    int id;
    memcpy(&id, ptr, 4);
    ptr += 4;

    int num_args;
    memcpy(&num_args, ptr, 4);
    ptr += 4;

    if (id < 1 || id > sizeof(funcs) / sizeof(funcs[0]))
    {
        char *error = "Function not found";
        return make_response(strlen(error), 1, error);
    }

    return funcs[id - 1](ptr, num_args);
}"""

    PLUGIN_DIR = Path("plugins")
    PLUGIN_DIR.mkdir(exist_ok=True)
    plugin_path = PLUGIN_DIR / f"{plugin_name}.c"
    with open(plugin_path, "w", encoding="utf-8") as f:
        f.write(template)

def make_rust_plugin(plugin_name: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", plugin_name):
        raise ValueError("Plugin name must be a valid Rust identifier-style name")

    lib_rs_template = r"""#![no_std]

use core::ptr;
use core::slice;

// --- Memory Management ---
const HEAP_SIZE: usize = 64 * 1024;
static mut HEAP: [u8; HEAP_SIZE] = [0u8; HEAP_SIZE];
static mut HEAP_PTR: usize = 0;

#[no_mangle]
pub extern "C" fn malloc(size: usize) -> *mut u8 {
    unsafe {
        let start = HEAP_PTR;
        HEAP_PTR += (size + 7) & !7;
        if HEAP_PTR > HEAP_SIZE { return ptr::null_mut(); }
        HEAP.as_mut_ptr().add(start)
    }
}

#[no_mangle]
pub extern "C" fn free(_ptr: *mut u8) {}

#[no_mangle]
pub extern "C" fn init() {}

#[no_mangle]
pub extern "C" fn cleanup() {}

// --- Helpers ---
fn create_response(count: i32, item_size: i32, payload: &[u8]) -> *mut u8 {
    let total_len = (12 + payload.len()) as i32;
    let ptr = malloc(total_len as usize);
    if ptr.is_null() { return ptr; }

    unsafe {
        let out = slice::from_raw_parts_mut(ptr, total_len as usize);
        out[0..4].copy_from_slice(&total_len.to_le_bytes());
        out[4..8].copy_from_slice(&count.to_le_bytes());
        out[8..12].copy_from_slice(&item_size.to_le_bytes());
        out[12..].copy_from_slice(payload);
    }
    ptr
}

// --- Plugin Logic ---
#[no_mangle]
pub extern "C" fn get_functions() -> *mut u8 {
    let json = br#"{"functions": [
        {"id": 1, "name": "example_function", "args": "[int]", "return": "int"}
    ]}"#;
    create_response(json.len() as i32, 1, json)
}

#[no_mangle]
pub extern "C" fn call_function(ptr: *mut u8, _len: i32) -> *mut u8 {
    if ptr.is_null() { return ptr; }

    unsafe {
        let header = slice::from_raw_parts(ptr, 8);
        let func_id = i32::from_le_bytes(header[0..4].try_into().unwrap_or([0; 4]));
        
        match func_id {
            1 => {
                // example_function implementation
                let arg_bytes = slice::from_raw_parts(ptr.add(16), 4);
                let n = i32::from_le_bytes(arg_bytes.try_into().unwrap_or([0; 4]));
                
                let result = n * 2; // Example: double the input
                create_response(1, 4, &result.to_le_bytes())
            }
            _ => {
                let msg = b"Function not found";
                create_response(msg.len() as i32, 1, msg)
            }
        }
    }
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! { loop {} }
"""

    cargo_toml_template = f"""[package]
name = "{plugin_name}"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[profile.release]
opt-level = "s"
lto = true
"""

    config_toml_template = """[target.wasm32-unknown-unknown]
rustflags = [
    "-C", "link-arg=--export=init",
    "-C", "link-arg=--export=cleanup",
    "-C", "link-arg=--export=malloc",
    "-C", "link-arg=--export=free",
    "-C", "link-arg=--export=get_functions",
    "-C", "link-arg=--export=call_function",
]
"""

    # Create directories
    PLUGIN_DIR = Path("plugins") / plugin_name
    src_dir = PLUGIN_DIR / "src"
    cargo_dir = PLUGIN_DIR / ".cargo"
    
    src_dir.mkdir(parents=True, exist_ok=True)
    cargo_dir.mkdir(parents=True, exist_ok=True)
    
    # Write files
    with open(PLUGIN_DIR / "Cargo.toml", "w", encoding="utf-8") as f:
        f.write(cargo_toml_template)
        
    with open(cargo_dir / "config.toml", "w", encoding="utf-8") as f:
        f.write(config_toml_template)
        
    with open(src_dir / "lib.rs", "w", encoding="utf-8") as f:
        f.write(lib_rs_template)


if __name__ == "__main__":
    lang = input("Enter language (C or Rust): ").strip().lower()
    
    if lang == "c":
        plugin_name = input("Enter plugin name (without extension [ .c ]): ")
        make_c_plugin(plugin_name)
        print(f"Plugin '{plugin_name}' created at 'plugins/{plugin_name}.c'")
    elif lang == "rust":
        plugin_name = input("Enter Rust plugin name: ")
        make_rust_plugin(plugin_name)
        print(f"Rust plugin '{plugin_name}' created at 'plugins/{plugin_name}/'")
    else:
        print("Invalid language selected. Please enter 'C' or 'Rust'.")