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


if __name__ == "__main__":
    plugin_name = input("Enter plugin name (without extension [ .c ]) ")
    make_c_plugin(plugin_name)
    print(f"Plugin '{plugin_name}' created at 'plugins/{plugin_name}.c'")