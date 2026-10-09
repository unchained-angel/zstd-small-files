import sys
import json
import pathlib
import zstandard as zstd

def main():
    force = "--force" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--force"]

    if len(args) != 2:
        print("Usage: python train_and_register.py <samples_dir> <output_dict.bin> [--force]")
        print("Example: python train_and_register.py samples_v3 dictionary_v3.bin")
        sys.exit(1)

    samples_dir = pathlib.Path(args[0])
    out_dict_path = pathlib.Path(args[1])

    if not samples_dir.is_dir():
        print(f"Error: {samples_dir} is not a directory")
        sys.exit(1)

    # SAFETY GUARD 1: refuse to overwrite an existing dictionary file
    if out_dict_path.exists() and not force:
        print(f"Error: output file {out_dict_path} already exists.")
        print("No changes were made. Use --force to overwrite an existing dictionary file.")
        sys.exit(1)

    # Load samples
    print(f"Loading samples from {samples_dir}...")
    samples = [p.read_bytes() for p in sorted(samples_dir.iterdir()) if p.is_file()]

    if len(samples) < 10:
        print(f"Error: Need at least 10 samples, found {len(samples)}")
        sys.exit(1)

    # Train the dictionary
    print(f"Training dictionary on {len(samples)} samples...")
    dictionary = zstd.train_dictionary(10 * 1024, samples)
    new_dict_bytes = dictionary.as_bytes()

    # Extract Dictionary ID by compressing a dummy payload
    cctx = zstd.ZstdCompressor(dict_data=dictionary)
    dummy_compressed = cctx.compress(b"dummy_payload_for_id_extraction")
    params = zstd.get_frame_parameters(dummy_compressed)
    dict_id = params.dict_id

    if dict_id == 0:
        print("Warning: Dictionary ID is 0. Training may have failed or dictionary is too small.")

    # Load existing registry
    reg_path = pathlib.Path("registry.json")
    registry = {}
    if reg_path.exists():
        registry = json.loads(reg_path.read_text())

    # SAFETY GUARD 2: refuse Dictionary ID collision
    existing_file = registry.get(str(dict_id))
    if existing_file and not force:
        print("ERROR: Dictionary ID collision.")
        print(f"Dictionary ID {dict_id} is already registered to: {existing_file}")
        print("No changes were made.")
        print("If you really intend to replace it, rerun with --force.")
        sys.exit(1)

    # Only now do we write anything
    out_dict_path.write_bytes(new_dict_bytes)
    registry[str(dict_id)] = out_dict_path.name
    reg_path.write_text(json.dumps(registry, indent=2) + "\n")

    print(f"Saved dictionary to {out_dict_path}")
    print(f"Successfully registered Dictionary ID {dict_id} -> {out_dict_path.name}")
    print("Updated registry.json:")
    print(json.dumps(registry, indent=2))

if __name__ == "__main__":
    main()
