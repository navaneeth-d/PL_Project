#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define EXPORT(name) __attribute__((export_name(name)))

// ===== init / cleanup =====
EXPORT("init")
void init() {}
EXPORT("cleanup")
void cleanup() {}

// ===== helper =====
char *make_response(const char *json)
{
    int len = strlen(json);
    char *ptr = (char *)malloc(len + 4);
    memcpy(ptr, &len, 4);
    memcpy(ptr + 4, json, len);
    return ptr;
}

// ===== metadata =====
EXPORT("get_functions")
char *get_functions()
{
    return make_response(
        "{\"functions\": [\"sum\", \"mul\", \"greet\", \"get_array\", \"mixed\"]}");
}

// ===== helpers =====
int extract_sum(const char *input)
{
    int sum = 0, num = 0;
    for (int i = 0; input[i]; i++)
    {
        if (input[i] >= '0' && input[i] <= '9')
        {
            num = num * 10 + (input[i] - '0');
        }
        else
        {
            sum += num;
            num = 0;
        }
    }
    return sum + num;
}

int extract_mul(const char *input)
{
    int res = 1, num = 0, found = 0;
    for (int i = 0; input[i]; i++)
    {
        if (input[i] >= '0' && input[i] <= '9')
        {
            num = num * 10 + (input[i] - '0');
            found = 1;
        }
        else
        {
            if (found)
                res *= num;
            num = 0;
            found = 0;
        }
    }
    if (found)
        res *= num;
    return res;
}

// ===== dispatcher =====
EXPORT("call_function")
char *call_function(char *ptr, int len)
{
    char *json = ptr + 4;

    // ---- SUM ----
    if (strstr(json, "sum"))
    {
        int result = extract_sum(json);

        char buffer[64];
        sprintf(buffer, "{\"result\": %d}", result);
        return make_response(buffer);
    }

    // ---- MUL ----
    if (strstr(json, "mul"))
    {
        int result = extract_mul(json);

        char buffer[64];
        sprintf(buffer, "{\"result\": %d}", result);
        return make_response(buffer);
    }

    // ---- STRING ----
    if (strstr(json, "greet"))
    {
        return make_response("{\"result\": \"hello from C\"}");
    }

    // ---- ARRAY ----
    if (strstr(json, "get_array"))
    {
        return make_response("{\"result\": [1,2,3,4,5]}");
    }

    // ---- MIXED ----
    if (strstr(json, "mixed"))
    {
        return make_response(
            "{\"sum\": 10, \"msg\": \"done\", \"arr\": [7,8,9]}");
    }

    return make_response("{\"error\": \"unknown function\"}");
}