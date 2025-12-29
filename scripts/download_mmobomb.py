import requests
import json
import os

# Save path
output_path = os.path.join("data", "mmobomb_games_backup.json")

# MMOBomb API URL
url = "https://www.mmobomb.com/api1/games"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    games = response.json()  # Renamed from 'juegos'

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

    print(f"✅ Successfully saved {len(games)} games to {output_path}")

except Exception as e:
    print("❌ Error downloading games from MMOBomb:", e)