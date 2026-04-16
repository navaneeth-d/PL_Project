/*
Schemas:

    Receive data:
        [func_id:4]
        [num_args:4]

        For each arg:
            [size of each element:any]       # e.g. int=4 int_array=4 string=1
            [number of elements:any]         # number of elements (not bytes)
            [data: ...]                      # raw bytes


    Return data:
        [total_length:4]    # total length of the response (including this header)
        [num_items:4]       # number of items in the response (e.g. number of strings)
        [item_length:4]     # length of this item in bytes
        [item_data: ...]    # raw bytes of the item
*/

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define EXPORT(name) __attribute__((export_name(name)))
typedef void *(*FuncPtr)(void *data, int num_args);

// ===== init / cleanup =====
EXPORT("init")
void init() {}
EXPORT("cleanup")
void cleanup() {}

// ===== helper =====
// This is only for demonstration purposes. You are free to write your own memory allocation code to return the data
void *make_response(int count_of_items, int each_item_size, void *result)
{
    int len = each_item_size * count_of_items + 12;
    char *ptr = (char *)malloc(len);
    memcpy(ptr, &len, 4);
    memcpy(ptr + 4, &count_of_items, 4);
    memcpy(ptr + 8, &each_item_size, 4);
    memcpy(ptr + 12, result, each_item_size * count_of_items);
    return ptr;
}

// ===== metadata =====
EXPORT("get_functions")
void *get_functions()
{
    char *response = "{"
                     "\"functions\": ["
                     "{\"id\": 1, \"name\": \"sumarray\", \"args\": \"[list[int]]\", \"return\": \"int\"},"
                     "{\"id\": 2, \"name\": \"mul\", \"args\": \"[list[int]]\", \"return\": \"int\"},"
                     "{\"id\": 3, \"name\": \"sumab\", \"args\": \"[int, int]\", \"return\": \"int\"},"
                     "{\"id\": 4, \"name\": \"greet\", \"args\": \"[string]\", \"return\": \"string\"},"
                     "{\"id\": 5, \"name\": \"noReturn\", \"args\": \"[]\", \"return\": \"null\"}"
                     "]"
                     "}";
    return make_response(strlen(response), 1, response);
}

// ===== helpers =====
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

    char *name = (char *)malloc(size * num_elements);
    memcpy(name, data + 8, size * num_elements);

    char greeting[100];
    snprintf(greeting, sizeof(greeting), "Hello, %s!", name);

    void *res = make_response(strlen(greeting), 1, greeting);
    free(name);
    return res;
}

void *noReturn(void *data, int num_args)
{
    return NULL;
}

int number_of_args(void *data)
{
    int num_args;
    memcpy(&num_args, data, 4);
    return num_args;
}

// ===== dispatcher =====
EXPORT("call_function")
void *call_function(void *ptr, int len)
{
    FuncPtr funcs[] = {sumarray, mul, sumab, greet, noReturn};
    int id;
    memcpy(&id, ptr, 4);
    ptr += 4;
    len -= 4;

    int num_args = number_of_args(ptr);
    ptr += 4;
    len -= 4;

    if (id < 1 || id > 5)
    {
        char *error = "Function not found";
        return make_response(strlen(error), 1, error);
    }

    return funcs[id - 1](ptr, num_args);
}