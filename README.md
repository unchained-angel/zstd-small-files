# Self-Healing Zstd Dictionary Compression for Small JSON APIs

A production-grade compression microservice that solves the small file overhead problem for JSON APIs using trained Zstandard dictionaries, versioned registries, and automated schema drift detection.

---

## The Problem

Small JSON API responses under 10 KB suffer from two major issues:

1. **Compression overhead.** Standard compression algorithms carry frame headers that consume a significant percentage of tiny files, often resulting in minimal or negative savings.
2. **Schema drift.** As APIs evolve, field names change. Trained dictionaries silently lose effectiveness, potentially compressing data worse than doing nothing at all.

---

## Findings

We tested this system using disjoint holdout benchmarks and real-world API data from the GitHub API.

| Dictionary Version | Training Data | Savings on Real Data | Status |
| :--- | :--- | :--- | :--- |
| v1 through v4 | Synthetic e-commerce | ~52% | Mismatched -- worse than vanilla |
| v5 | Real GitHub data | 82.7% | Memorization ceiling |
| v6 | Disjoint JSONPlaceholder | 75.3% | Honest generalization |

### Key Insights

**The Mismatched Dictionary Trap.** A dictionary trained on the wrong schema achieved only 52% savings, which was worse than vanilla Zstd at 64.6%. A mismatched dictionary is worse than no dictionary.

**Generalization.** Even when trained on completely different endpoints, the dictionary generalized well at 75.3% savings. This proves it learned the structural grammar of JSON rather than memorizing specific strings.

**The Brotli Tooling Gap.** Brotli is excellent for static assets, but its Python bindings lack accessible dictionary support. Zstd is the superior choice for dynamic microservices.

---

## Architecture

The system consists of five components:

**Versioned Registry.** A JSON-based registry maps Dictionary IDs to file versions, allowing clients to automatically route to the correct dictionary.

**Dual-Signal Drift Monitor.** Uses a frozen Golden Set as a control group and a Rolling Window of live traffic. The delta between the two distinguishes schema drift from dictionary regression.

**Compression Engine.** Dictionary-based Zstd compression with automatic selection of the latest dictionary version.

**HTTP Distribution.** Server endpoint serves dictionaries to clients with ETag caching and immutable cache headers.

**Production Hygiene.** Atomic I/O writes prevent registry corruption. HTTP 304 responses minimize bandwidth on repeated downloads.

---

## Installation and Usage

### Install the Library

Clone the repository and install in editable mode:

    git clone https://github.com/YOUR_USERNAME/zstd-small-files.git
    cd zstd-small-files
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .

### Train a Dictionary

    zstd-train samples_train dictionary_v6.bin

### Monitor Schema Drift

    python dual_monitor.py

### Serve Dictionaries via HTTP

    uvicorn server:app --reload --reload-include "*.json"

Clients download dictionaries via:

    GET /dictionaries/{dictionary_id}

---

## Lessons Learned

**Disjoint holdouts.** Never benchmark on training data. Use disjoint sources to measure true generalization.

**Control groups.** Use a frozen Golden Set to separate system regression from environmental drift.

**Atomic I/O.** Always use os.replace to prevent file corruption during writes.

**Cache control.** Use ETag and immutable cache headers to save bandwidth on static artifacts.

**Relative thresholds.** Monitor live traffic relative to a control baseline, not against a hardcoded absolute number.

---

## License

MIT License. Free to use in any project.
