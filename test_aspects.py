import json
from src.main import process_astro_request

payload = {
    'datetime': {'year': 2026, 'month': 2, 'day': 22, 'hour': 10, 'minute': 0, 'second': 0, 'utc_offset': 5.5}, 
    'location': {'latitude': 28.6139, 'longitude': 77.209, 'altitude': 0.0}, 
    'ayanamsa': 'LAHIRI'
}

r = process_astro_request(payload)

def ordinal(n):
    return f"{n}{({1:'st', 2:'nd', 3:'rd'}.get(n if n < 20 else n % 10, 'th'))}"

print("\n--- Planetary Aspects (Drishti) ---")
for p_name, p_data in r['positions'].items():
    if p_name == "Ascendant": continue
    p_house = p_data['house']
    for aspect in p_data.get('aspects', []):
        if aspect['aspected_planets']:
            a_num = aspect['aspect_number']
            t_house = aspect['target_house']
            for target_p in aspect['aspected_planets']:
                print(f"{p_name.lower()} is sitting in {ordinal(p_house)} house is aspecting {target_p.lower()} in {ordinal(t_house)} house with it's {ordinal(a_num)} aspect.")
