import json
import pathlib
import re
import sqlite3
import subprocess
import sys
import time

import zstandard as zstd


THRESHOLD = 0.30
REGISTRY_PATH = pathlib.Path("registry.json")
DB_PATH = pathlib.Path("metrics.db")
SAMPLES_DIR = pathlib.Path("samples_drift")


def version_number(filename):
    """
    Extract version number from filenames like dictionary_v4.bin.
    Returns -1 for non-versioned filenames.
    """
    match = re.search(r"_v(\d+)\.bin$", filename)
    if match:
        return int(match.group(1))
    return -1


def choose_current_dictionary(registry):
    """
    Choose the newest dictionary file from registry.json.
    """
    dictionary_files = sorted(
        set(registry.values()),
        key=version_number,
        reverse=True
    )

    for dictionary_file in dictionary_files:
        path = pathlib.Path(dictionary_file)
        if path.exists():
            return dictionary_file

    return None


def log_metrics(dictionary_file, dictionary_id, original_size, compressed_size, savings_percent):
    """
    Append one observation to metrics.db.
    """
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
            str(dictionary_id),
            original_size,
            compressed_size,
            savings_percent,
        ),
    )

    conn.commit()
    conn.close()


def main():
    if not SAMPLES_DIR.exists() or not list(SAMPLES_DIR.iterdir()):
        print("No drift samples found. Exiting.")
        return

    if not REGISTRY_PATH.exists():
        print("Error: registry.json not found.")
        return

    registry = json.loads(REGISTRY_PATH.read_text())

    current_dict_file = choose_current_dictionary(registry)

    if current_dict_file is None:
        print("Error: no existing dictionary file found in registry.json")
        return

    current_dict_id = "unknown"
    for registered_id, registered_file in registry.items():
        if registered_file == current_dict_file:
            current_dict_id = registered_id
            break

    dictionary_bytes = pathlib.Path(current_dict_file).read_bytes()
    dictionary = zstd.ZstdCompressionDict(dictionary_bytes)
    compressor = zstd.ZstdCompressor(level=3, dict_data=dictionary)

    samples = [
        path.read_bytes()
        for path in sorted(SAMPLES_DIR.iterdir())
        if path.is_file()
    ]

    total_original = 0
    total_compressed = 0

    for sample in samples:
        compressed = compressor.compress(sample)
        total_original += len(sample)
        total_compressed += len(compressed)

    if total_original == 0:
        savings = 0.0
    else:
        savings = 1 - total_compressed / total_original

    savings_percent = round(savings * 100, 2)

    print(f"Current dict ({current_dict_file}) savings on drift data: {savings_percent}%")

    # Log the observation
    log_metrics(
        current_dict_file,
        current_dict_id,
        total_original,
        total_compressed,
        savings_percent,
    )

    print(f"Metrics logged to {DB_PATH}")

    if savings < THRESHOLD:
        print("SCHEMA DRIFT DETECTED! Savings dropped below threshold.")

        latest_version = max(
            [version_number(filename) for filename in registry.values()] + [0]
        )

        next_version = latest_version + 1
        new_dict_name = f"dictionary_v{next_version}.bin"

        print(f"Automatically training {new_dict_name}...")

        result = subprocess.run(
            [
                sys.executable,
                "train_and_register.py",
                str(SAMPLES_DIR),
                new_dict_name,
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)

        if result.returncode != 0:
            print("Error during auto-retrain:")
            print(result.stderr)
        else:
            print("Retraining complete.")
            print("Run drift_monitor.py again to verify the new dictionary.")
    else:
        print("Dictionary is still effective. No retrain needed.")


if __name__ == "__main__":
    main()
