import requests
import sys
import os
import json

API_URL = "https://api.carbonintensity.org.uk/intensity"
THRESHOLD = 200  # gCO₂/kWh
BASELINE = 400   # baseline assumption (if job ran at peak)

# Detect trigger
event = os.environ.get("GITHUB_EVENT_NAME", "push")
job_type = os.environ.get("JOB_TYPE", "flexible").lower()

if event == "push":
    print(" Triggered by auto push → Defaulting to 'flexible'")
else:
    print(f" Triggered manually → Job type selected: {job_type}")

# Urgent jobs skip checks
if job_type == "urgent":
    print(" Job type = urgent → Skipping checks. Running job immediately.")
    score, savings = 100, "0 kg"
else:
    try:
        resp = requests.get(API_URL, timeout=10).json()
        data = resp["data"][0]
        forecast = data["intensity"]["forecast"]
        actual = data["intensity"]["actual"]
        index = data["intensity"]["index"]

        print(f" Forecast: {forecast} gCO₂/kWh")
        print(f" Actual:   {actual} gCO₂/kWh")
        print(f" Index:    {index}")
        print(f" Job type: {job_type}")

        # Handle None values for "actual"
        value = actual if actual is not None else forecast

        # Calculate GreenOps Score (simple scale)
        score = max(0, min(100, int((BASELINE - value) / BASELINE * 100)))

        # Estimate savings vs baseline
        saved = max(0, BASELINE - value)
        savings = f"{saved/1000:.2f} kg"  # assume 1 job = 1 kWh usage

        if value < THRESHOLD:
            print(" Carbon intensity is low now → running job")
            sys.exit_code = 0
        elif forecast < THRESHOLD:
            print(" Forecast shows lower intensity soon → delaying job")
            sys.exit_code = 1
        else:
            print(" High carbon intensity now and in forecast → delaying job")
            sys.exit_code = 1
    except Exception as e:
        print(" Error fetching carbon data:", e)
        score, savings = 0, "0 kg"
        sys.exit_code = 1

# Save sustainability data for HTML
with open("sustainability.json", "w") as f:
    json.dump({"score": score, "savings": savings}, f)

sys.exit(sys.exit_code)
