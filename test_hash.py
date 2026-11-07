import hashlib
from pathlib import Path

# Read our existing Unity documentation
file_path = Path("data/unity/Rigidbody2D.txt")
content = file_path.read_bytes()

# Generate a SHA-256 hash
file_hash = hashlib.sha256(content).hexdigest()

print(f"File: {file_path}")
print(f"SHA-256: {file_hash}")