import json
import random
import os

# Create a folder to hold our samples
os.makedirs("samples", exist_ok=True)

# A function to generate one fake API response
def generate_sample():
    return json.dumps({
        "request_id": f"req_{random.randint(1000, 9999)}",
        "timestamp": "2026-09-19T12:00:00Z",
        "status": random.choice(["success", "pending", "failed"]),
        "user": {
            "id": random.randint(1, 500),
            "role": random.choice(["admin", "user", "guest"]),
            "email_verified": random.choice([True, False])
        },
        "payload": {
            "items": [
                {"sku": f"ITEM-{random.randint(10,99)}", "qty": random.randint(1,5)} 
                for _ in range(random.randint(1, 3))
            ]
        }
    })

# Generate 500 samples and save them
print("Generating 500 samples...")
for i in range(500):
    filename = f"samples/sample_{i}.json"
    with open(filename, "w") as f:
        f.write(generate_sample())

print("Done! Check the 'samples' folder.")
