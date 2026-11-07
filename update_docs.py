import subprocess
import sys


def run_script(script_name):
    """Run a Python script and stop if it fails."""

    print(f"\nRunning {script_name}...", flush=True)

    subprocess.run(
        [sys.executable, script_name],
        check=True
    )


def main():
    print("Starting Unity documentation update...")

    # Step 1: Download documentation
    run_script("fetch_unity.py")

    # Step 2: Update the vector database
    run_script("ingest_unity.py")

    print("\nDocumentation update completed successfully!")


if __name__ == "__main__":
    main()