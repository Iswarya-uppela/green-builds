import requests
import sys
import os
import json

# Detect trigger source
event = os.environ.get("GITHUB_EVENT_NAME", "push")
job_type = os.environ.get("JOB_TYPE", "flexible").lower()

if event == "push":
    print("📌 Triggered by auto push → Defaulting to 'flexible'")
else:
    print(f"📌 Triggered manually → Job type selected: {job_type}")

# Urgent jobs skip checks
if job_type == "urgent":
    print("🚀 Job type = urgent → Skipping carbon intensity check. Running job immediately.")
    with open("savings.json", "w") as f:
        json.dump({"savings": "Urgent job → no CO₂ savings calculated."}, f)
    sys.exit(0)

# Flexible jobs check carbon intensity API
url = "https://api.carbonintensity.org.uk/intensity"
resp = requests.get(url).json()
data = resp["data"][0]

forecast = data["intensity"]["forecast"]
actual = data["intensity"]["actual"]
index = data["intensity"]["index"]

print(f"🔎 Forecast: {forecast} gCO₂/kWh")
print(f"📊 Actual:   {actual} gCO₂/kWh")
print(f"🌍 Index:    {index}")
print(f"⚡ Job type: {job_type}")

# Threshold for "green energy"
THRESHOLD = 200  

# Helper: convert CO₂ savings to equivalents
def co2_equivalents(saved_grams):
    km_car = round(saved_grams / 120, 2)   # ~120g CO₂/km (average petrol car)
    trees = round(saved_grams / 21, 2)     # ~21g CO₂ absorbed per tree per day
    return km_car, trees

savings_message = "No savings this run."

if actual and actual < THRESHOLD:
    print("✅ Carbon intensity is low now → running job")
    saved = forecast - actual if forecast and forecast > actual else 0
    if saved > 0:
        km, trees = co2_equivalents(saved)
        savings_message = f"Saved ~{saved} gCO₂ ≈ {km} km car travel or {trees} tree-days 🌳"
    with open("savings.json", "w") as f:
        json.dump({"savings": savings_message}, f)
    sys.exit(0)

elif forecast < THRESHOLD:
    print("⏳ Forecast shows lower intensity soon → delaying job")
    saved = (actual - forecast) if actual else 50  # fallback if actual missing
    km, trees = co2_equivalents(saved)
    savings_message = f"By waiting, we may save ~{saved} gCO₂ ≈ {km} km car travel or {trees} tree-days 🌳"
    with open("savings.json", "w") as f:
        json.dump({"savings": savings_message}, f)
    sys.exit(1)

else:
    print("⚠️ High carbon intensity now and in forecast → delaying job")
    with open("savings.json", "w") as f:
        json.dump({"savings": savings_message}, f)
    sys.exit(1)
