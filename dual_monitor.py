import pathlib
import json
import zstandard as zstd

def evaluate(folder, dict_path):
    files = [p for p in pathlib.Path(folder).iterdir() if p.is_file()]
    if not files:
        return None, None
    orig = sum(p.stat().st_size for p in files)
    d = zstd.ZstdCompressionDict(pathlib.Path(dict_path).read_bytes())
    c = zstd.ZstdCompressor(level=3, dict_data=d)
    comp = sum(len(c.compress(p.read_bytes())) for p in files)
    return orig, (1 - comp/orig)*100

reg = json.loads(pathlib.Path("registry.json").read_text())
# Get the latest dictionary (highest version number)
latest_file = sorted(reg.values(), key=lambda x: int(x.split('_v')[1].split('.')[0]) if '_v' in x else 0)[-1]

print(f"Evaluating using {latest_file}...\n")

g_orig, g_sav = evaluate("golden_set", latest_file)
r_orig, r_sav = evaluate("rolling_window", latest_file)

if g_sav is None or r_sav is None:
    print("Missing folders. Run setup first.")
else:
    print(f"Golden Set (Control):    {g_sav:.1f}% savings")
    print(f"Rolling Window (Live):   {r_sav:.1f}% savings")
    
    delta = g_sav - r_sav
    print(f"Delta (Control - Live):  {delta:.1f} percentage points\n")

    if g_sav < 20 and r_sav < 20:
        print("DIAGNOSIS: 🚨 DICTIONARY REGRESSION!")
        print("The dictionary itself is failing on data it used to know.")
        print("Action: Investigate the dictionary file or training pipeline.")
    elif delta > 5.0:  # If live traffic is >5% worse than the control group
        print("DIAGNOSIS: ⚠️ SCHEMA DRIFT detected!")
        print(f"The dictionary lost {delta:.1f}% efficiency on live data compared to the control group.")
        print("Action: Trigger retraining on the rolling window.")
    else:
        print("DIAGNOSIS: ✅ System Healthy. Live traffic matches control group baseline.")
