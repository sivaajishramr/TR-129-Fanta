import json
import random

new_districts = [
    ("Ariyalur", 11.1385, 79.0747),
    ("Chengalpattu", 12.6841, 79.9836),
    ("Cuddalore", 11.7480, 79.7714),
    ("Dharmapuri", 12.1211, 78.1582),
    ("Dindigul", 10.3673, 77.9803),
    ("Kallakurichi", 11.7377, 78.9624),
    ("Kanchipuram", 12.8342, 79.7036),
    ("Karur", 10.9598, 78.0766),
    ("Krishnagiri", 12.5276, 78.2185),
    ("Mayiladuthurai", 11.1018, 79.6521),
    ("Nagapattinam", 10.7672, 79.8449),
    ("Namakkal", 11.2189, 78.1674),
    ("Ooty (Nilgiris)", 11.4085, 76.6997),
    ("Perambalur", 11.2335, 78.8624),
    ("Pudukkottai", 10.3807, 78.8205),
    ("Ramanathapuram", 9.3639, 78.8321),
    ("Ranipet", 12.9275, 79.3330),
    ("Sivaganga", 9.8433, 78.4809),
    ("Tenkasi", 8.9594, 77.3161),
    ("Theni", 10.0104, 77.4768),
    ("Thoothukudi", 8.7642, 78.1348),
    ("Tirupathur", 12.4939, 78.5663),
    ("Tiruppur", 11.1085, 77.3411),
    ("Tiruvallur", 13.1416, 79.9071),
    ("Tiruvannamalai", 12.2253, 79.0747),
    ("Tiruvarur", 10.7661, 79.6385),
    ("Villupuram", 11.9401, 79.4861),
    ("Virudhunagar", 9.5855, 77.9614)
]

with open('data/transit_stops.json', 'r') as f:
    stops = json.load(f)

max_id = max([int(s['id'][1:]) for s in stops])

for i, (name, lat, lng) in enumerate(new_districts):
    new_id = f"S{max_id + i + 1:03d}"
    
    # Random realistic accessibility for new stops
    ramp = random.choice([True, False, False])
    staff = random.choice([True, False])
    
    stop_name = f"{name} New Bus Stand" if "Ooty" not in name else "Ooty Central Bus Stand"
    
    stop = {
        "id": new_id,
        "name": stop_name,
        "lat": lat,
        "lng": lng,
        "type": "bus_stand",
        "daily_footfall": random.randint(4000, 20000),
        "features": {
            "ramp": ramp,
            "tactile_path": False,
            "audio_signal": False,
            "wheelchair_space": False,
            "braille_signage": False,
            "elevator": False,
            "accessible_toilet": False,
            "staff_assistance": staff
        },
        "last_audit_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    }
    stops.append(stop)

with open('data/transit_stops.json', 'w') as f:
    json.dump(stops, f, indent=2)

print(f"Added {len(new_districts)} new districts. Total stops now: {len(stops)}")
