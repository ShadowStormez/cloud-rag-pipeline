import argparse
import subprocess
import sys
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run resumable documentation download batches."
    )

    parser.add_argument("--engine", choices=["unity", "godot"], required=True)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--batches", type=int, default=5)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--execute", action="store_true")

    args = parser.parse_args()

    if args.batch_size < 1 or args.batches < 1:
        parser.error("Batch size and batch count must be positive")

    if args.delay < 0:
        parser.error("Delay must not be negative")

    command = [
        sys.executable,
        "download_discovered_docs.py",
        "--engine", args.engine,
        "--max-pages", str(args.batch_size),
        "--delay", str(args.delay),
    ]

    print(f"Engine: {args.engine}", flush=True)
    print(f"Batch size: {args.batch_size}", flush=True)
    print(f"Maximum batches: {args.batches}", flush=True)
    print(f"Maximum URL attempts: {args.batch_size * args.batches}", flush=True)

    if not args.execute:
        print("DRY RUN: No downloads will occur.")
        print("Command:", " ".join(command))
        return

    for batch in range(1, args.batches + 1):
        discovery_path = (
            Path("data/discovery") / f"{args.engine}_progress.json"
        )
        output_dir = Path("data/automatic") / args.engine

        discovered = json.loads(
            discovery_path.read_text(encoding="utf-8")
        )["discovered_urls"]

        manifest_path = output_dir / "sources.json"
        sources = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else {}
        )

        failed_path = output_dir / "failed_urls.json"
        failed = (
            set(json.loads(failed_path.read_text(encoding="utf-8")))
            if failed_path.exists()
            else set()
        )

        completed = {
            url
            for filename, url in sources.items()
            if (output_dir / filename).is_file()
        }

        remaining = sum(
            url not in completed and url not in failed
            for url in set(discovered)
        )

        print(f"\nRemaining eligible URLs: {remaining}", flush=True)

        if remaining == 0:
            print("No pending URLs. Stopping.")
            break

        print(f"Starting batch {batch}/{args.batches}", flush=True)
        subprocess.run(command, check=True)

    print("\nBulk download session finished.")


if __name__ == "__main__":
    main()