import json
import pathlib
import random
import re
import sqlite3
import time

import zstandard as zstd


REGISTRY_PATH = pathlib.Path("registry.json")
DB_PATH = pathlib.Path("metrics.db")


def choose_current_dictionary(registry):
    """
    Choose the newest dictionary file from registry.json.

    Prefers files like:
        dictionary_v1.bin
        dictionary_v2.bin
        dictionary_v4.bin

    Falls back to dictionary.bin if no versioned dictionary exists.
    """
    dictionary_files = sorted(set(registry.values()), key=version_number, reverse=True)

    for dictionary_file in dictionary_files:
        path = pathlib.Path(dictionary_file)
        if path.exists():
            return dictionary_file

    return None


def version_number(filename):
    """
    Extract version number from filenames like dictionary_v4.bin.
    Returns -1 for non-versioned filenames.
    """
    match = re.search(r"_v(\d+)\.bin$", filename)
    if match:
        return int(match.group(1))
    return -1


def generate_fresh_sample():
    """Generate a fresh small JSON API response."""
    return json.dumps({
        "request_id": f"metric_{random.randint(10000, 99999)}",
        "timestamp": "2026-10-01T12:00:00Z",
        "status": random.choice(["success", "pending", "failed", "timeout"]),
        "user": {
            "id": random.randint(1, 10000),
            "role": random.choice(["admin", "user", "guest", "moderator"]),
            "email_verified": random.choice([True, False])
        },
        "payload": {
            "items": [
                {
                    "sku": f"PROD-{random.randint(100, 999)}",
                    "qty": random.randint(1, 20),
                    "price": round(random.uniform(1.0, 500.0), 2)
                }
                for _ in range(random.randint(1, 5))
            ],
            "currency": random.choice(["USD", "EUR", "GBP"])
        }
    }).encode("utf-8")


def main():
    if not REGISTRY_PATH.exists():
        print("Error: registry.json not found.")
        return

    registry = json.loads(REGISTRY_PATH.read_text())

    dictionary_file = choose_current_dictionary(registry)

    if dictionary_file is None:
        print("Error: no existing dictionary file found in registry.json")
        return

    dictionary_path = pathlib.Path(dictionary_file)

    # Find the dictionary ID mapped to this file
    dictionary_id = "unknown"
    for registered_id, registered_file in registry.items():
        if registered_file == dictionary_file:
            dictionary_id = registered_id
            break

    dictionary_bytes = dictionary_path.read_bytes()
    dictionary = zstd.ZstdCompressionDict(dictionary_bytes)

    compressor = zstd.ZstdCompressor(level=3, dict_data=dictionary)

    # Generate fresh test data
    samples = [generate_fresh_sample() for _ in range(20)]

    total_original = 0
    total_compressed = 0

    for sample in samples:
        compressed = compressor.compress(sample)
        total_original += len(sample)
        total_compressed += len(compressed)

    if total_original == 0:
        savings = 0.0
    else:
        savings = (1 - total_compressed / total_original) * 100

    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            timestamp REAL,
            dictionary_file TEXT,
            dictionary_id TEXT,
            original_size INTEGER,
            compressed_size INTEGER,
            savings_percent REAL
        )
        """
    )

    conn.execute(
        """
        INSERT INTO metrics (
            timestamp,
            dictionary_file,
            dictionary_id,
            original_size,
            compressed_size,
            savings_percent
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            time.time(),
            dictionary_file,
            dictionary_id,
            total_original,
            total_compressed,
            round(savings, 1),
        ),
    )

    conn.commit()
    conn.close()

    print(f"Dictionary used: {dictionary_file}")
    print(f"Dictionary ID: {dictionary_id}")
    print(f"Original size: {total_original} bytes")
    print(f"Compressed size: {total_compressed} bytes")
    print(f"Savings: {savings:.1f}%")
    print(f"Metrics logged to {DB_PATH}")


if __name__ == "__main__":
    main()
