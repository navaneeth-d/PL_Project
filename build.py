import os
import shutil
import subprocess
from pathlib import Path


class Builder:
    def __init__(self):
        self.base_dir = Path("plugins")
        self.build_dir = self.base_dir / "build"
        self.build_dir.mkdir(parents=True, exist_ok=True)

        # load emscripten environment once
        self.env = self.get_emscripten_env()

    # ---------- ENV SETUP ----------
    def get_emscripten_env(self):
        """
        Source emsdk_env.sh and capture environment variables
        """
        try:
            cmd = "bash -c 'source emsdk/emsdk_env.sh && env'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(result.stderr)

            env = os.environ.copy()

            for line in result.stdout.splitlines():
                key, _, value = line.partition("=")
                env[key] = value

            return env

        except Exception as e:
            print("Failed to load Emscripten environment")
            print(e)
            print("Make sure emsdk is installed and path is correct")
            return os.environ.copy()

    def run_cmd(self, cmd, cwd=None, env=None):
        print(f"\n>> {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env or self.env
        )
        if result.returncode != 0:
            print(result.stderr)
            raise Exception("Build failed")
        else:
            print(result.stdout)


    # ---------- C ----------
    def build_c(self, file_path):
        file_path = Path(file_path)
        output = self.build_dir / (file_path.stem + ".wasm")

        cmd = [
            "emcc",
            str(file_path),
            "-o", str(output),
            "--no-entry",
            "-s", "STANDALONE_WASM",
            "-s", "EXPORT_ALL=1",
            "-s", "EXPORTED_FUNCTIONS=_malloc,_free,_init,_cleanup,_call_function,_get_functions"
        ]

        self.run_cmd(cmd)
        print(f"[C] Built: {output}")

    
    # ---------- RUST ----------
    def build_rust(self, crate_dir):
        """
        Detect a Rust crate by the presence of Cargo.toml inside a plugins/ subdirectory.
        Run: cargo build --target wasm32-unknown-unknown --release
        Then copy the .wasm output into plugins/build/
        """
        crate_dir = Path(crate_dir)
        crate_name = crate_dir.name  # e.g. "example_rust"
        print(f"\n[Rust] Building crate: {crate_name}")
        cmd = [
            "cargo", "build",
            "--target", "wasm32-unknown-unknown",
            "--release"
        ]
        # Cargo needs to run from inside the crate directory
        # Use plain os.environ so cargo uses the system PATH (not emscripten's env)
        self.run_cmd(cmd, cwd=str(crate_dir), env=os.environ.copy())
        # Cargo outputs to: <crate>/target/wasm32-unknown-unknown/release/<name>.wasm
        wasm_src = (
            crate_dir
            / "target"
            / "wasm32-unknown-unknown"
            / "release"
            / f"{crate_name}.wasm"
        )
        wasm_dst = self.build_dir / f"{crate_name}.wasm"
        shutil.copy2(wasm_src, wasm_dst)
        print(f"[Rust] Built: {wasm_dst}")

    def build_all(self):
        for file in self.base_dir.iterdir():

            if file.name == "build":       # skip output dir
                continue

            if file.is_file() and file.suffix == ".c":
                self.build_c(file)

            if file.is_dir() and (file / "Cargo.toml").exists():   # ← Rust
                self.build_rust(file)




if __name__ == "__main__":
    builder = Builder()
    builder.build_all()