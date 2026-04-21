/*
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
#include <stdio.h>

#define EXPORT(name) __attribute__((export_name(name)))
typedef void *(*FuncPtr)(void *data, int num_args);

// !===== REQUIRED: lifecycle =====
EXPORT("init")
void init() {}

EXPORT("cleanup")
void cleanup() {}

// ===== response helper (example implementation) =====
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
    char *response = "{"
                     "\"functions\": ["
                     "{\"id\": 1, \"name\": \"sumarray\", \"args\": [\"list[int]\"], \"return\": \"int\"},"
                     "{\"id\": 2, \"name\": \"mul\", \"args\": [\"list[int]\"], \"return\": \"int\"},"
                     "{\"id\": 3, \"name\": \"sumab\", \"args\": [\"int\", \"int\"], \"return\": \"int\"},"
                     "{\"id\": 4, \"name\": \"greet\", \"args\": [\"string\"], \"return\": \"string\"},"
                     "{\"id\": 5, \"name\": \"noReturn\", \"args\": [], \"return\": \"null\"},"
                     "{\"id\": 6, \"name\": \"doubleArray\", \"args\": [\"list[int]\"], \"return\": \"list[int]\"}"
                     "]"
                     "}";
    return make_response(strlen(response), 1, response);
}

// !===== USER FUNCTIONS =====
/*
Each function receives:
    data     → pointer to encoded arguments
    num_args → number of arguments

Must return:
    pointer to response buffer (see schema above)
*/
void *sumarray(void *data, int num_args)
{
    int sum = 0;
    int size, num_elements;
    int offset = 4;
    memcpy(&size, data, 4);
    memcpy(&num_elements, data + offset, 4);
    for (int j = 0; j < num_elements; j++)
    {
        int arg;
        offset += size;
        memcpy(&arg, data + offset, size);
        sum += arg;
    }
    return make_response(1, 4, &sum);
}

void *mul(void *data, int num_args)
{
    int product = 1;
    int size, num_elements;
    int offset = 4;
    memcpy(&size, data, 4);
    memcpy(&num_elements, data + offset, 4);
    for (int j = 0; j < num_elements; j++)
    {
        int arg;
        offset += size;
        memcpy(&arg, data + offset, size);
        product *= arg;
    }
    return make_response(1, 4, &product);
}

void *sumab(void *data, int num_args)
{
    int sum = 0;
    int size, num_elements;

    memcpy(&size, data, 4);
    memcpy(&num_elements, data + 4, 4);

    int a;
    memcpy(&a, data + 8, size);
    sum += a;

    memcpy(&size, data + 12, 4);
    memcpy(&num_elements, data + 16, 4);

    int b;
    memcpy(&b, data + 20, size);
    sum += b;
    return make_response(1, 4, &sum);
}

void *greet(void *data, int num_args)
{
    int size, num_elements;
    memcpy(&size, data, 4);
    memcpy(&num_elements, data + 4, 4);

    char *name = (char *)malloc((size * num_elements) + 1);
    memcpy(name, data + 8, size * num_elements);
    name[size * num_elements] = '\0';

    char *greeting = (char *)malloc(size * num_elements + 8);
    snprintf(greeting, size * num_elements + 8, "Hello, %s!", name);

    void *res = make_response(strlen(greeting), 1, greeting);
    free(name);
    free(greeting);
    return res;
}

void *noReturn(void *data, int num_args)
{
    return NULL;
}

void *doubleArray(void *data, int num_args)
{
    int size, num_elements;
    memcpy(&size, data, 4);
    memcpy(&num_elements, data + 4, 4);

    int arr[num_elements];
    memcpy(arr, data + 8, size * num_elements);

    for (int i = 0; i < num_elements; i++)
    {
        arr[i] *= 2;
    }
    return make_response(num_elements, size, arr);
}

int number_of_args(void *data)
{
    int num_args;
    memcpy(&num_args, data, 4);
    return num_args;
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
    FuncPtr funcs[] = {sumarray, mul, sumab, greet, noReturn, doubleArray};
    int id;
    memcpy(&id, ptr, 4);
    ptr += 4;
    len -= 4;

    int num_args = number_of_args(ptr);
    ptr += 4;
    len -= 4;

    if (id < 1 || id > 6)
    {
        char *error = "Function not found";
        return make_response(strlen(error), 1, error);
    }

    return funcs[id - 1](ptr, num_args);
}