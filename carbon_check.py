import requests, sys, os, json, random
from datetime import datetime

API_URL = "https://api.carbonintensity.org.uk/intensity"
THRESHOLD = 200  # gCO₂/kWh

event = os.environ.get("GITHUB_EVENT_NAME", "push")
job_type = os.environ.get("JOB_TYPE", "flexible").lower()

if event == "push":
    print(" Triggered by auto push → Defaulting to 'flexible'")
else:
    print(f" Triggered manually → Job type selected: {job_type}")

# Urgent jobs skip checks
if job_type == "urgent":
    print(" Urgent job → Skipping carbon check. Running immediately.")
    # Still produce sustainability.json with neutral values
    data = {"score": 50, "savings": "N/A (urgent run)"}
    with open("sustainability.json", "w") as f:
        json.dump(data, f, indent=2)
    sys.exit(0)

try:
    resp = requests.get(API_URL, timeout=10)
    data = resp.json()["data"][0]

    forecast = data["intensity"]["forecast"]
    actual = data["intensity"].get("actual")
    index = data["intensity"]["index"]

    print(f" Forecast: {forecast} gCO₂/kWh")
    print(f" Actual:   {actual} gCO₂/kWh")
    print(f" Index:    {index}")
    print(f" Job type: {job_type}")

    # Fallback if actual is missing
    current_value = actual if actual is not None else forecast

    # Calculate sustainability metrics
    if current_value < THRESHOLD:
        score = random.randint(80, 100)  # good score
        savings = f"{THRESHOLD - current_value} gCO₂ avoided"
        print(" Carbon intensity is low now → running job")
        status = 0
    elif forecast < THRESHOLD:
        score = random.randint(60, 79)
        savings = f"{THRESHOLD - forecast} gCO₂ possible if delayed"
        print(" Forecast shows greener energy soon → delaying job")
        status = 1
    else:
        score = random.randint(30, 59)
        savings = "No savings possible (high intensity)"
        print(" High carbon intensity now and in forecast → delaying job")
        status = 1

    # Save sustainability impact
    impact = {"score": score, "savings": savings, "timestamp": datetime.utcnow().isoformat()}
    with open("sustainability.json", "w") as f:
        json.dump(impact, f, indent=2)

    sys.exit(status)

except Exception as e:
    print("⚠️ Error fetching carbon data:", e)
    # Write fallback JSON
    with open("sustainability.json", "w") as f:
        json.dump({"score": 0, "savings": "Error fetching data"}, f, indent=2)
    sys.exit(1)
