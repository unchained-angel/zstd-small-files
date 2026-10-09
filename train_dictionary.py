import pathlib
import zstandard as zstd

# Folder containing the small JSON sample files
samples_dir = pathlib.Path("samples")

# Load every .json sample as raw bytes
samples = []

for path in sorted(samples_dir.glob("*.json")):
    samples.append(path.read_bytes())

print(f"Loaded {len(samples)} samples")

# Dictionary size in bytes.
# 10 KB is a good starting point for small JSON files.
dictionary_size = 10 * 1024

print(f"Training dictionary of size {dictionary_size} bytes...")

# Train the dictionary
dictionary = zstd.train_dictionary(dictionary_size, samples)

# Save the dictionary to a binary file
dictionary_path = pathlib.Path("dictionary.bin")
dictionary_path.write_bytes(dictionary.as_bytes())

print(f"Saved dictionary to {dictionary_path}")
print(f"Dictionary file size: {dictionary_path.stat().st_size} bytes")
