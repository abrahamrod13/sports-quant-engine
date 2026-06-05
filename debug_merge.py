# debug_merge.py
from mlb_data_fetcher import get_today_mlb_games
from odds_fetcher import get_fanduel_odds_full

print("=" * 60)
print("DEBUG MERGE - Comparando nombres")
print("=" * 60)

mlb_games = get_today_mlb_games()
odds = get_fanduel_odds_full('baseball_mlb')

print(f"\nJuegos MLB API: {len(mlb_games)}")
for idx, row in mlb_games.iterrows():
    print(f"  {row['match']}")

print(f"\nOdds FanDuel: {len(odds)}")
for idx, row in odds.iterrows():
    print(f"  {row['match']}")

print("\n" + "=" * 60)
print("BUSCANDO COINCIDENCIAS MANUALES")
print("=" * 60)

for _, game in mlb_games.iterrows():
    game_match = game['match'].lower()
    found = False
    for _, odd in odds.iterrows():
        odd_match = odd['match'].lower()
        if game_match == odd_match:
            print(f"✅ EXACTA: {game['match']}")
            found = True
            break
        elif game['home_team'].lower() in odd_match and game['away_team'].lower() in odd_match:
            print(f"🟢 PARCIAL: {game['match']} -> {odd['match']}")
            found = True
            break
    if not found:
        print(f"❌ NO MATCH: {game['match']}")