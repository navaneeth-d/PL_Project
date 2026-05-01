// native_rust_runner/src/main.rs

use std::time::Instant;

fn sumarray(values: &[i32]) -> i32 {
    values.iter().sum()
}

fn mul(values: &[i32]) -> i32 {
    values.iter().product()
}

fn sumab(a: i32, b: i32) -> i32 {
    a + b
}

fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

fn no_return() {}

fn double_array(values: &[i32]) -> Vec<i32> {
    values.iter().map(|x| x * 2).collect()
}

fn greet_full(first: &str, last: &str) -> String {
    format!("Hello, {} {}!", first, last)
}

const HEAVY_WARMUP: usize = 200;
const HEAVY_RUNS: usize = 2500;
const SUMARRAY_LEN: usize = 80;
const INPUT_ROWS: usize = 2500;

fn percentile(values: &[f64], p: f64) -> f64 {
    let mut sorted = values.to_vec();

    sorted.sort_by(|a, b| {
        a.partial_cmp(b).unwrap()
    });

    let idx = (
        (p / 100.0)
        * ((sorted.len() - 1) as f64)
    ).round() as usize;

    sorted[idx]
}

fn print_metrics(
    workload: &str,
    latencies: &[f64]
) {
    let total: f64 =
        latencies.iter().sum();

    println!(
        "\n{}\navg_ms={:.6}\np95_ms={:.6}\nthroughput={:.2}",
        workload,
        total / HEAVY_RUNS as f64,
        percentile(latencies, 95.0),
        HEAVY_RUNS as f64
            / (total / 1000.0)
    );
}

fn benchmark_sumarray() {

    let rows: Vec<Vec<i32>> =
        (0..INPUT_ROWS)
        .map(|i| {
            (0..SUMARRAY_LEN)
                .map(|j| (i % 5 + j) as i32)
                .collect()
        })
        .collect();

    for i in 0..HEAVY_WARMUP {
        sumarray(&rows[i]);
    }

    let mut latencies = Vec::new();

    for i in 0..HEAVY_RUNS {

        let row =
            &rows[i % INPUT_ROWS];

        let start =
            Instant::now();

        sumarray(row);

        latencies.push(
            start.elapsed()
                .as_secs_f64() * 1000.0
        );
    }

    print_metrics(
        "sumarray",
        &latencies
    );
}

fn benchmark_mul() {

    let rows: Vec<Vec<i32>> =
        (0..INPUT_ROWS)
        .map(|i| {
            (0..SUMARRAY_LEN)
                .map(|j| (((i + 1) % 7) + j) as i32)
                .collect()
        })
        .collect();

    for i in 0..HEAVY_WARMUP {
        mul(&rows[i]);
    }

    let mut latencies = Vec::new();

    for i in 0..HEAVY_RUNS {

        let row =
            &rows[i % INPUT_ROWS];

        let start =
            Instant::now();

        mul(row);

        latencies.push(
            start.elapsed()
                .as_secs_f64() * 1000.0
        );
    }

    print_metrics(
        "mul",
        &latencies
    );
}

fn benchmark_sumab() {

    let rows: Vec<(i32, i32)> =
        (0..INPUT_ROWS)
        .map(|i| {
            (
                (i % 101) as i32,
                ((i * 7) % 97) as i32
            )
        })
        .collect();

    for i in 0..HEAVY_WARMUP {

        let (a, b) =
            rows[i];

        sumab(a, b);
    }

    let mut latencies = Vec::new();

    for i in 0..HEAVY_RUNS {

        let (a, b) =
            rows[i % INPUT_ROWS];

        let start =
            Instant::now();

        sumab(a, b);

        latencies.push(
            start.elapsed()
                .as_secs_f64() * 1000.0
        );
    }

    print_metrics(
        "sumab",
        &latencies
    );
}

fn benchmark_greet() {

    let rows: Vec<String> =
        (0..INPUT_ROWS)
        .map(|i| {
            format!("user_{:04}", i)
        })
        .collect();

    for i in 0..HEAVY_WARMUP {
        greet(&rows[i]);
    }

    let mut latencies = Vec::new();

    for i in 0..HEAVY_RUNS {

        let row =
            &rows[i % INPUT_ROWS];

        let start =
            Instant::now();

        greet(row);

        latencies.push(
            start.elapsed()
                .as_secs_f64() * 1000.0
        );
    }

    print_metrics(
        "greet",
        &latencies
    );
}

fn benchmark_noreturn() {

    for _ in 0..HEAVY_WARMUP {
        no_return();
    }

    let mut latencies = Vec::new();

    for _ in 0..HEAVY_RUNS {

        let start =
            Instant::now();

        no_return();

        latencies.push(
            start.elapsed()
                .as_secs_f64() * 1000.0
        );
    }

    print_metrics(
        "noReturn",
        &latencies
    );
}

fn benchmark_double_array() {

    let rows: Vec<Vec<i32>> =
        (0..INPUT_ROWS)
        .map(|i| {
            (0..SUMARRAY_LEN)
                .map(|j| (i % 5 + j) as i32)
                .collect()
        })
        .collect();

    for i in 0..HEAVY_WARMUP {
        double_array(&rows[i]);
    }

    let mut latencies = Vec::new();

    for i in 0..HEAVY_RUNS {

        let row =
            &rows[i % INPUT_ROWS];

        let start =
            Instant::now();

        double_array(row);

        latencies.push(
            start.elapsed()
                .as_secs_f64() * 1000.0
        );
    }

    print_metrics(
        "doubleArray",
        &latencies
    );
}

fn benchmark_greet_full() {

    let rows: Vec<(String, String)> =
        (0..INPUT_ROWS)
        .map(|i| {
            (
                format!("first_{}", i),
                format!("last_{}", i)
            )
        })
        .collect();

    for i in 0..HEAVY_WARMUP {

        let (a, b) =
            &rows[i];

        greet_full(a, b);
    }

    let mut latencies = Vec::new();

    for i in 0..HEAVY_RUNS {

        let (a, b) =
            &rows[i % INPUT_ROWS];

        let start =
            Instant::now();

        greet_full(a, b);

        latencies.push(
            start.elapsed()
                .as_secs_f64() * 1000.0
        );
    }

    print_metrics(
        "greet_full",
        &latencies
    );
}

fn main() {

    benchmark_sumarray();

    benchmark_mul();

    benchmark_sumab();

    benchmark_greet();

    benchmark_noreturn();

    benchmark_double_array();

    benchmark_greet_full();
}