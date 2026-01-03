import requests
import json
import os

# Construct the absolute path to the destination file in /data
output_path = os.path.join(os.path.dirname(__file__), "..", "data", "freetogame_games_backup.json")
output_path = os.path.abspath(output_path)

# FreeToGame API URL
url = "https://www.freetogame.com/api/games"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    games = response.json()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)

    print(f"✅ Data successfully saved to: {output_path}")

except requests.RequestException as e:
    print("❌ Error connecting to FreeToGame API:", e)