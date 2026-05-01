# C benchmark

gcc \
-O3 \
-flto \
-march=native \
-fno-strict-aliasing \
benchmark.c \
example.c \
-o native_c_benchmark

./native_c_benchmark


# Rust benchmark
cd native_rust_runner

cargo build --release

./target/release/native_rust_runner