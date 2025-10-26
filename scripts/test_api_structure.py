#!/usr/bin/env python3
"""
Script för att testa och inspektera Svenska Spels API när kupong är öppen.

Kör detta script när Stryktipset öppnar (ca 20:00 svensk tid på fredagar)
för att se den verkliga API-strukturen.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


async def test_api():
    """Testa Svenska Spels API och visa strukturen."""
    print("\n" + "="*70)
    print("SVENSKA SPEL API STRUCTURE TEST")
    print("="*70)

    endpoint = "https://api.spela.svenskaspel.se/draw/1/stryktipset/draws"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://spela.svenskaspel.se/stryktipset',
    }

    print(f"\n📡 Hämtar från: {endpoint}")
    print(f"📋 Headers: {json.dumps(headers, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, headers=headers)
            print(f"\n✓ Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Spara rådata
                with open('api_response_raw.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"💾 Rådata sparad i: api_response_raw.json")

                # Visa struktur
                print("\n" + "="*70)
                print("API RESPONSE STRUCTURE")
                print("="*70)

                draws = data.get("draws", [])
                print(f"\n📊 Antal draws: {len(draws)}")

                if not draws:
                    print("\n⚠️  Inga draws tillgängliga ännu!")
                    print("Kupong har inte öppnat. Försök igen efter ca 20:00 på fredag.")
                else:
                    # Visa första draw
                    draw = draws[0]
                    print(f"\n🎯 FÖRSTA DRAW:")
                    print(f"   Top-level keys: {list(draw.keys())}")

                    # Visa mer detaljer
                    for key, value in draw.items():
                        if isinstance(value, list):
                            print(f"\n   📋 {key}: (list med {len(value)} element)")
                            if value:
                                print(f"      Första element keys: {list(value[0].keys()) if isinstance(value[0], dict) else type(value[0])}")
                                print(f"      Första element: {json.dumps(value[0], indent=10, ensure_ascii=False)[:200]}...")
                        elif isinstance(value, dict):
                            print(f"\n   📦 {key}: (dict)")
                            print(f"      Keys: {list(value.keys())}")
                        else:
                            print(f"   • {key}: {value}")

                    # Specialkoll för events/matches
                    events_key = None
                    for possible_key in ['events', 'matches', 'games', 'rows']:
                        if possible_key in draw:
                            events_key = possible_key
                            break

                    if events_key:
                        events = draw[events_key]
                        print(f"\n🎮 MATCH/EVENT DATA (key: '{events_key}'):")
                        print(f"   Antal matcher: {len(events)}")

                        if events:
                            print(f"\n   📝 FÖRSTA MATCHEN:")
                            first_event = events[0]
                            print(f"      Keys: {list(first_event.keys())}")
                            print(json.dumps(first_event, indent=6, ensure_ascii=False))

                            # Spara första eventet separat
                            with open('api_first_event.json', 'w', encoding='utf-8') as f:
                                json.dump(first_event, f, indent=2, ensure_ascii=False)
                            print(f"\n   💾 Första event sparad i: api_first_event.json")

                    # Kolla efter distribution/streckprocent
                    print(f"\n🎲 DISTRIBUTION/STRECKPROCENT:")
                    if 'distribution' in draw:
                        print(f"   Distribution finns på draw-nivå!")
                        print(f"   Keys: {list(draw['distribution'].keys())}")
                    elif events_key and draw[events_key]:
                        first_event = draw[events_key][0]
                        if 'distribution' in first_event:
                            print(f"   Distribution finns på event-nivå!")
                            print(f"   Keys: {list(first_event['distribution'].keys())}")
                            print(f"   Exempel: {first_event['distribution']}")
                        else:
                            print(f"   ⚠️ Hittade inte 'distribution' i event")
                            print(f"   Möjliga keys för streckprocent: {[k for k in first_event.keys() if 'perc' in k.lower() or 'distr' in k.lower() or 'odds' in k.lower()]}")

                print("\n" + "="*70)
                print("SAMMANFATTNING")
                print("="*70)
                print(f"✓ API fungerar!")
                print(f"✓ {len(draws)} draw(s) tillgängliga")
                if draws:
                    events_count = len(draws[0].get(events_key or 'events', []))
                    print(f"✓ {events_count} matcher i första draw")
                print(f"\n📝 Nästa steg:")
                print(f"   1. Granska api_response_raw.json")
                print(f"   2. Granska api_first_event.json")
                print(f"   3. Uppdatera _parse_api_response() i src/scrapers/svenska_spel.py")
                print(f"   4. Uppdatera _parse_event() baserat på faktisk struktur")

            else:
                print(f"✗ Oväntat status: {response.status_code}")
                print(f"Response: {response.text[:500]}")

    except httpx.TimeoutException:
        print("\n✗ Timeout - API svarar inte inom 30 sekunder")
    except httpx.HTTPStatusError as e:
        print(f"\n✗ HTTP error: {e}")
    except Exception as e:
        print(f"\n✗ Fel: {type(e).__name__}: {e}")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_api())
