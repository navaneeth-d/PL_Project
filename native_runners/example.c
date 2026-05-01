#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>

typedef void *(*FuncPtr)(void *data);

#define HEAP_SIZE (64 * 1024)

static unsigned char HEAP[HEAP_SIZE];
static uint32_t HEAP_OFFSET = 0;

// ========================= BUMP ALLOCATOR =========================

static inline void *bump_alloc(uint32_t size)
{
    size = (size + 7u) & ~7u;

    if (HEAP_OFFSET + size > HEAP_SIZE)
        return NULL;

    void *ptr = HEAP + HEAP_OFFSET;
    HEAP_OFFSET += size;

    return ptr;
}

static inline void bump_reset(void)
{
    HEAP_OFFSET = 0;
}

void init(void)
{
    bump_reset();
}

void cleanup(void)
{
    bump_reset();
}

// ========================= RESPONSE =========================

static inline void *make_response(uint32_t count, uint32_t item_size, const void *data)
{
    uint32_t payload = count * item_size;
    uint32_t total = payload + 12;

    uint8_t *ptr = (uint8_t *)bump_alloc(total);
    if (!ptr)
        return NULL;

    ((uint32_t *)ptr)[0] = total;
    ((uint32_t *)ptr)[1] = count;
    ((uint32_t *)ptr)[2] = item_size;

    memcpy(ptr + 12, data, payload);

    return ptr;
}

// ========================= METADATA =========================

void *get_functions(void)
{
    static const char json[] =
        "{"
        "\"functions\":["
        "{\"id\":1,\"name\":\"sumarray\",\"args\":[\"list[int]\"],\"return\":\"int\"},"
        "{\"id\":2,\"name\":\"mul\",\"args\":[\"list[int]\"],\"return\":\"int\"},"
        "{\"id\":3,\"name\":\"sumab\",\"args\":[\"int\",\"int\"],\"return\":\"int\"},"
        "{\"id\":4,\"name\":\"greet\",\"args\":[\"string\"],\"return\":\"string\"},"
        "{\"id\":5,\"name\":\"noReturn\",\"args\":[],\"return\":\"null\"},"
        "{\"id\":6,\"name\":\"doubleArray\",\"args\":[\"list[int]\"],\"return\":\"list[int]\"},"
        "{\"id\":7,\"name\":\"greet\",\"args\":[\"string\",\"string\"],\"return\":\"string\"}"
        "]"
        "}";

    return make_response((uint32_t)(sizeof(json) - 1), 1, json);
}

// ========================= HELPERS =========================

static inline uint32_t read_u32(const void *p)
{
    return *(const uint32_t *)p;
}

// ========================= FUNCTIONS =========================

void *sumarray(void *data)
{
    uint8_t *p = (uint8_t *)data;

    uint32_t count = read_u32(p + 4);
    int32_t *arr = (int32_t *)(p + 8);

    int32_t sum = 0;

    for (uint32_t i = 0; i < count; ++i)
        sum += arr[i];

    return make_response(1, 4, &sum);
}

void *mul(void *data)
{
    uint8_t *p = (uint8_t *)data;

    uint32_t count = read_u32(p + 4);
    int32_t *arr = (int32_t *)(p + 8);

    int32_t product = 1;

    for (uint32_t i = 0; i < count; ++i)
        product *= arr[i];

    return make_response(1, 4, &product);
}

void *sumab(void *data)
{
    uint8_t *p = (uint8_t *)data;

    int32_t a = *(int32_t *)(p + 8);

    uint32_t offset = 8 + read_u32(p) * read_u32(p + 4);

    int32_t b = *(int32_t *)(p + offset + 8);

    int32_t sum = a + b;

    return make_response(1, 4, &sum);
}

void *greet(void *data)
{
    uint8_t *p = (uint8_t *)data;

    uint32_t len = read_u32(p) * read_u32(p + 4);
    char *name = (char *)(p + 8);

    static const char prefix[] = "Hello, ";
    const uint32_t prefix_len = 7;

    uint32_t out_len = prefix_len + len + 1;

    char *out = (char *)bump_alloc(out_len);
    if (!out)
        return NULL;

    memcpy(out, prefix, prefix_len);
    memcpy(out + prefix_len, name, len);

    out[prefix_len + len] = '!';

    return make_response(out_len, 1, out);
}

void *greet_full(void *data)
{
    uint8_t *p = (uint8_t *)data;

    uint32_t len1 = read_u32(p) * read_u32(p + 4);
    char *first = (char *)(p + 8);

    uint32_t offset = 8 + len1;

    uint32_t len2 = read_u32(p + offset) * read_u32(p + offset + 4);
    char *last = (char *)(p + offset + 8);

    static const char prefix[] = "Hello, ";
    const uint32_t prefix_len = 7;

    uint32_t out_len = prefix_len + len1 + 1 + len2 + 1;

    char *out = (char *)bump_alloc(out_len);
    if (!out)
        return NULL;

    uint32_t pos = 0;

    memcpy(out + pos, prefix, prefix_len);
    pos += prefix_len;

    memcpy(out + pos, first, len1);
    pos += len1;

    out[pos++] = ' ';

    memcpy(out + pos, last, len2);
    pos += len2;

    out[pos] = '!';

    return make_response(out_len, 1, out);
}

void *noReturn(void *data)
{
    (void)data;
    return NULL;
}

void *doubleArray(void *data)
{
    uint8_t *p = (uint8_t *)data;

    uint32_t count = read_u32(p + 4);

    int32_t *input = (int32_t *)(p + 8);

    uint32_t total = 12 + (count * 4);

    uint8_t *out = (uint8_t *)bump_alloc(total);
    if (!out)
        return NULL;

    ((uint32_t *)out)[0] = total;
    ((uint32_t *)out)[1] = count;
    ((uint32_t *)out)[2] = 4;

    int32_t *result = (int32_t *)(out + 12);

    for (uint32_t i = 0; i < count; ++i)
        result[i] = input[i] * 2;

    return out;
}

// ========================= DISPATCHER =========================

void *call_function(void *ptr, int len)
{
    (void)len;

    bump_reset();

    static FuncPtr funcs[] = {
        sumarray,
        mul,
        sumab,
        greet,
        noReturn,
        doubleArray,
        greet_full};

    uint8_t *p = (uint8_t *)ptr;

    uint32_t id = read_u32(p);

    if (id < 1 || id > 7)
    {
        static const char err[] = "Function not found";
        return make_response(sizeof(err) - 1, 1, err);
    }

    return funcs[id - 1](p + 8);
}