// native_c_benchmark.c
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define HEAVY_WARMUP 1000
#define HEAVY_RUNS 10000
#define SUMARRAY_LEN 1000
#define INPUT_ROWS 1000

extern void *sumarray(void *);
extern void *mul(void *);
extern void *sumab(void *);
extern void *greet(void *);
extern void *noReturn(void *);
extern void *doubleArray(void *);

typedef struct
{
    int size;
    int count;
    int data[SUMARRAY_LEN];
} ArrayInput;

typedef struct
{
    int size;
    int count;
    int value;
} IntInput;

typedef struct
{
    int size;
    int count;
    char data[128];
} StringInput;

typedef struct
{
    IntInput a;
    IntInput b;
} SumABInput;

static double now_ms()
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);

    return (ts.tv_sec * 1000.0) +
           (ts.tv_nsec / 1000000.0);
}

static int cmp_double(const void *a, const void *b)
{
    double x = *(double *)a;
    double y = *(double *)b;

    return (x > y) - (x < y);
}

static double percentile(double *arr, int n, double p)
{

    double *copy = malloc(sizeof(double) * n);

    memcpy(copy, arr, sizeof(double) * n);

    qsort(copy, n, sizeof(double), cmp_double);

    int idx = (int)round(
        (p / 100.0) * (n - 1));

    double v = copy[idx];

    free(copy);

    return v;
}

static void benchmark_sumarray()
{

    double latencies[HEAVY_RUNS];

    ArrayInput rows[INPUT_ROWS];

    for (int i = 0; i < INPUT_ROWS; i++)
    {

        rows[i].size = 4;
        rows[i].count = SUMARRAY_LEN;

        for (int j = 0; j < SUMARRAY_LEN; j++)
        {
            rows[i].data[j] =
                (i % 5) + j;
        }
    }

    for (int i = 0; i < HEAVY_WARMUP; i++)
    {
        sumarray(&rows[i]);
    }

    for (int i = 0; i < HEAVY_RUNS; i++)
    {

        double start = now_ms();

        sumarray(
            &rows[i % INPUT_ROWS]);

        double end = now_ms();

        latencies[i] =
            end - start;
    }

    double total = 0;

    for (int i = 0; i < HEAVY_RUNS; i++)
    {
        total += latencies[i];
    }

    printf(
        "sumarray\n"
        "avg_ms=%.6f\n"
        "p95_ms=%.6f\n"
        "throughput=%.2f\n\n",

        total / HEAVY_RUNS,

        percentile(
            latencies,
            HEAVY_RUNS,
            95),

        HEAVY_RUNS /
            (total / 1000.0));
}

static void benchmark_mul()
{

    double latencies[HEAVY_RUNS];

    ArrayInput rows[INPUT_ROWS];

    for (int i = 0; i < INPUT_ROWS; i++)
    {

        rows[i].size = 4;
        rows[i].count = SUMARRAY_LEN;

        for (int j = 0; j < SUMARRAY_LEN; j++)
        {
            rows[i].data[j] =
                ((i + 1) % 7) + j;
        }
    }

    for (int i = 0; i < HEAVY_WARMUP; i++)
    {
        mul(&rows[i]);
    }

    for (int i = 0; i < HEAVY_RUNS; i++)
    {

        double start = now_ms();

        mul(
            &rows[i % INPUT_ROWS]);

        double end = now_ms();

        latencies[i] =
            end - start;
    }

    double total = 0;

    for (int i = 0; i < HEAVY_RUNS; i++)
    {
        total += latencies[i];
    }

    printf(
        "mul\n"
        "avg_ms=%.6f\n"
        "p95_ms=%.6f\n"
        "throughput=%.2f\n\n",

        total / HEAVY_RUNS,

        percentile(
            latencies,
            HEAVY_RUNS,
            95),

        HEAVY_RUNS /
            (total / 1000.0));
}

static void benchmark_sumab()
{

    double latencies[HEAVY_RUNS];

    SumABInput rows[INPUT_ROWS];

    for (int i = 0; i < INPUT_ROWS; i++)
    {

        rows[i].a.size = 4;
        rows[i].a.count = 1;
        rows[i].a.value = i % 101;

        rows[i].b.size = 4;
        rows[i].b.count = 1;
        rows[i].b.value =
            (i * 7) % 97;
    }

    for (int i = 0; i < HEAVY_WARMUP; i++)
    {
        sumab(&rows[i]);
    }

    for (int i = 0; i < HEAVY_RUNS; i++)
    {

        double start = now_ms();

        sumab(
            &rows[i % INPUT_ROWS]);

        double end = now_ms();

        latencies[i] =
            end - start;
    }

    double total = 0;

    for (int i = 0; i < HEAVY_RUNS; i++)
    {
        total += latencies[i];
    }

    printf(
        "sumab\n"
        "avg_ms=%.6f\n"
        "p95_ms=%.6f\n"
        "throughput=%.2f\n\n",

        total / HEAVY_RUNS,

        percentile(
            latencies,
            HEAVY_RUNS,
            95),

        HEAVY_RUNS /
            (total / 1000.0));
}

static void benchmark_greet()
{

    double latencies[HEAVY_RUNS];

    StringInput rows[INPUT_ROWS];

    for (int i = 0; i < INPUT_ROWS; i++)
    {

        snprintf(
            rows[i].data,
            sizeof(rows[i].data),
            "user_%04d",
            i);

        rows[i].size = 1;

        rows[i].count =
            strlen(rows[i].data);
    }

    for (int i = 0; i < HEAVY_WARMUP; i++)
    {
        greet(&rows[i]);
    }

    for (int i = 0; i < HEAVY_RUNS; i++)
    {

        double start = now_ms();

        greet(
            &rows[i % INPUT_ROWS]);

        double end = now_ms();

        latencies[i] =
            end - start;
    }

    double total = 0;

    for (int i = 0; i < HEAVY_RUNS; i++)
    {
        total += latencies[i];
    }

    printf(
        "greet\n"
        "avg_ms=%.6f\n"
        "p95_ms=%.6f\n"
        "throughput=%.2f\n\n",

        total / HEAVY_RUNS,

        percentile(
            latencies,
            HEAVY_RUNS,
            95),

        HEAVY_RUNS /
            (total / 1000.0));
}

static void benchmark_noreturn()
{

    double latencies[HEAVY_RUNS];

    for (int i = 0; i < HEAVY_WARMUP; i++)
    {
        noReturn(NULL);
    }

    for (int i = 0; i < HEAVY_RUNS; i++)
    {

        double start = now_ms();

        noReturn(NULL);

        double end = now_ms();

        latencies[i] =
            end - start;
    }

    double total = 0;

    for (int i = 0; i < HEAVY_RUNS; i++)
    {
        total += latencies[i];
    }

    printf(
        "noReturn\n"
        "avg_ms=%.6f\n"
        "p95_ms=%.6f\n"
        "throughput=%.2f\n\n",

        total / HEAVY_RUNS,

        percentile(
            latencies,
            HEAVY_RUNS,
            95),

        HEAVY_RUNS /
            (total / 1000.0));
}

static void benchmark_doubleArray()
{

    double latencies[HEAVY_RUNS];

    ArrayInput rows[INPUT_ROWS];

    for (int i = 0; i < INPUT_ROWS; i++)
    {

        rows[i].size = 4;
        rows[i].count = SUMARRAY_LEN;

        for (int j = 0; j < SUMARRAY_LEN; j++)
        {
            rows[i].data[j] =
                ((i + 2) % 11) + j;
        }
    }

    for (int i = 0; i < HEAVY_WARMUP; i++)
    {
        doubleArray(&rows[i]);
    }

    for (int i = 0; i < HEAVY_RUNS; i++)
    {

        double start = now_ms();

        doubleArray(
            &rows[i % INPUT_ROWS]);

        double end = now_ms();

        latencies[i] =
            end - start;
    }

    double total = 0;

    for (int i = 0; i < HEAVY_RUNS; i++)
    {
        total += latencies[i];
    }

    printf(
        "doubleArray\n"
        "avg_ms=%.6f\n"
        "p95_ms=%.6f\n"
        "throughput=%.2f\n\n",

        total / HEAVY_RUNS,

        percentile(
            latencies,
            HEAVY_RUNS,
            95),

        HEAVY_RUNS /
            (total / 1000.0));
}

int main()
{

    benchmark_sumarray();

    benchmark_mul();

    benchmark_sumab();

    benchmark_greet();

    benchmark_noreturn();

    benchmark_doubleArray();

    return 0;
}