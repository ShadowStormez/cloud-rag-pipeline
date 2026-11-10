import subprocess
import sys


def run_script(script_name):
    """Run a Python script and stop if it fails."""
    print(f"\nRunning {script_name}...", flush=True)

    subprocess.run(
        [sys.executable, script_name],
        check=True,
    )


def main():
    print("Starting multi-engine documentation update...")

    # Fetch documentation from all supported engines
    run_script("fetch_unity.py")
    run_script("fetch_engine_docs.py")

    # Incrementally update the shared Chroma database
    run_script("ingest_unity.py")
    run_script("ingest_engine_docs.py")

    print("\nMulti-engine documentation update completed!")


if __name__ == "__main__":
    main()