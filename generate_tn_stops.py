"""
Generate bus stops for ALL 38 districts of Tamil Nadu.
- Adds 'district' field to all existing Trichy stops
- Creates 2-3 realistic stops per district with real coordinates
- Generates matching grievances for each new stop
"""
import json
import random
from datetime import datetime, timedelta

# All 38 TN districts with major bus stand coords and population rank
TN_DISTRICTS = {
    "Tiruchirappalli": {"lat": 10.805, "lng": 78.686, "pop": 1},  # Already exists
    "Chennai": {"lat": 13.0827, "lng": 80.2707, "pop": 1},
    "Coimbatore": {"lat": 11.0168, "lng": 76.9558, "pop": 2},
    "Madurai": {"lat": 9.9252, "lng": 78.1198, "pop": 3},
    "Salem": {"lat": 11.6643, "lng": 78.1460, "pop": 4},
    "Tirunelveli": {"lat": 8.7139, "lng": 77.7567, "pop": 5},
    "Erode": {"lat": 11.3410, "lng": 77.7172, "pop": 6},
    "Vellore": {"lat": 12.9165, "lng": 79.1325, "pop": 7},
    "Thanjavur": {"lat": 10.7870, "lng": 79.1378, "pop": 8},
    "Dindigul": {"lat": 10.3624, "lng": 77.9695, "pop": 9},
    "Kanchipuram": {"lat": 12.8342, "lng": 79.7036, "pop": 10},
    "Cuddalore": {"lat": 11.7480, "lng": 79.7714, "pop": 11},
    "Villupuram": {"lat": 11.9401, "lng": 79.4861, "pop": 12},
    "Tiruvannamalai": {"lat": 12.2253, "lng": 79.0747, "pop": 13},
    "Nagapattinam": {"lat": 10.7672, "lng": 79.8449, "pop": 14},
    "Theni": {"lat": 10.0104, "lng": 77.4768, "pop": 15},
    "Virudhunagar": {"lat": 9.5851, "lng": 77.9526, "pop": 16},
    "Namakkal": {"lat": 11.2189, "lng": 78.1674, "pop": 17},
    "Karur": {"lat": 10.9601, "lng": 78.0766, "pop": 18},
    "Sivagangai": {"lat": 10.0373, "lng": 78.8867, "pop": 19},
    "Ramanathapuram": {"lat": 9.3712, "lng": 78.8308, "pop": 20},
    "Thoothukudi": {"lat": 8.7642, "lng": 78.1348, "pop": 21},
    "Tiruppur": {"lat": 11.1085, "lng": 77.3411, "pop": 22},
    "Pudukkottai": {"lat": 10.3833, "lng": 78.8001, "pop": 23},
    "Dharmapuri": {"lat": 12.1211, "lng": 78.1582, "pop": 24},
    "Krishnagiri": {"lat": 12.5186, "lng": 78.2138, "pop": 25},
    "Perambalur": {"lat": 11.2320, "lng": 78.8807, "pop": 26},
    "Ariyalur": {"lat": 11.1428, "lng": 79.0778, "pop": 27},
    "Nilgiris": {"lat": 11.4102, "lng": 76.6950, "pop": 28},
    "Ranipet": {"lat": 12.9224, "lng": 79.3327, "pop": 29},
    "Tirupathur": {"lat": 12.4955, "lng": 78.5730, "pop": 30},
    "Chengalpattu": {"lat": 12.6819, "lng": 79.9888, "pop": 31},
    "Kallakurichi": {"lat": 11.7380, "lng": 78.9609, "pop": 32},
    "Tenkasi": {"lat": 8.9604, "lng": 77.3152, "pop": 33},
    "Mayiladuthurai": {"lat": 11.1014, "lng": 79.6556, "pop": 34},
    "Kanyakumari": {"lat": 8.0883, "lng": 77.5385, "pop": 35},
}

# Stops per district (name template, type, footfall range)
STOP_TEMPLATES = [
    ("{district} Central Bus Stand", "bus_terminal", (8000, 25000)),
    ("{district} New Bus Stand", "bus_stand", (4000, 12000)),
    ("{district} Town Bus Stop", "bus_stop", (2000, 6000)),
]

# Grievance templates for new stops
GRIEVANCE_TEMPLATES = [
    "No wheelchair ramp at {stop}. Disabled passengers cannot board buses safely.",
    "No tactile path or braille signage at {stop}. Visually impaired people are completely ignored.",
    "No audio announcement system at {stop}. Blind passengers miss their buses regularly.",
    "{stop} has no accessible toilet. Disabled passengers have no facilities available.",
    "Staff at {stop} are not trained to assist disabled passengers. No help available.",
    "The bus shelter at {stop} has no seating for elderly or disabled passengers.",
    "Broken pavement near {stop} makes wheelchair access impossible.",
    "No LED display board at {stop}. Deaf passengers cannot get route information.",
]

def generate_features():
    """Generate random accessibility features - most stops lack features"""
    features = {}
    feature_names = ['ramp', 'tactile_path', 'audio_signal', 'wheelchair_space', 
                     'braille_signage', 'elevator', 'accessible_toilet', 'staff_assistance']
    
    # Weighted: most features are missing
    for f in feature_names:
        features[f] = random.random() < 0.2  # 20% chance of having feature
    return features

def generate_audit_date():
    """Generate a random audit date in the past 18 months"""
    days_ago = random.randint(30, 540)
    return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

def main():
    # Load existing stops
    with open('data/transit_stops.json', 'r') as f:
        stops = json.load(f)
    
    # Add district field to existing Trichy stops
    for stop in stops:
        stop['district'] = 'Tiruchirappalli'
    
    # Load existing grievances
    with open('data/grievances.json', 'r') as f:
        grievances = json.load(f)
    
    # Add district to existing grievances
    existing_stop_ids = {s['id'] for s in stops}
    for g in grievances:
        g['district'] = 'Tiruchirappalli'
    
    # Track next IDs
    next_stop_id = len(stops) + 1
    next_grv_id = len(grievances) + 1
    
    # Generate stops for each new district
    for district, info in TN_DISTRICTS.items():
        if district == "Tiruchirappalli":
            continue  # Already have these
        
        random.seed(hash(district))
        
        # Add 2-3 stops per district
        num_stops = random.choice([2, 3])
        templates = random.sample(STOP_TEMPLATES, num_stops)
        
        for i, (name_tmpl, stop_type, footfall_range) in enumerate(templates):
            stop_id = f"S{next_stop_id:03d}"
            
            # Offset coordinates slightly for each stop
            lat_offset = random.uniform(-0.03, 0.03)
            lng_offset = random.uniform(-0.03, 0.03)
            
            stop = {
                "id": stop_id,
                "name": name_tmpl.format(district=district),
                "lat": round(info['lat'] + lat_offset, 4),
                "lng": round(info['lng'] + lng_offset, 4),
                "type": stop_type,
                "daily_footfall": random.randint(*footfall_range),
                "features": generate_features(),
                "last_audit_date": generate_audit_date(),
                "district": district
            }
            stops.append(stop)
            
            # Generate 1-2 grievances per new stop
            num_grv = random.randint(1, 2)
            selected_templates = random.sample(GRIEVANCE_TEMPLATES, num_grv)
            
            for grv_tmpl in selected_templates:
                grv_id = f"G{next_grv_id:03d}"
                days_ago = random.randint(30, 365)
                grv_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                
                grievances.append({
                    "id": grv_id,
                    "stop_id": stop_id,
                    "text": grv_tmpl.format(stop=stop['name']),
                    "date": grv_date,
                    "category": None,
                    "district": district
                })
                next_grv_id += 1
            
            next_stop_id += 1
    
    # Save updated data
    with open('data/transit_stops.json', 'w') as f:
        json.dump(stops, f, indent=2)
    
    with open('data/grievances.json', 'w') as f:
        json.dump(grievances, f, indent=2)
    
    # Print summary
    districts = set(s.get('district', 'Unknown') for s in stops)
    print(f"\nData Generation Complete!")
    print(f"   Total Stops: {len(stops)}")
    print(f"   Total Grievances: {len(grievances)}")
    print(f"   Districts: {len(districts)}")
    print(f"\n   Districts covered:")
    for d in sorted(districts):
        d_stops = [s for s in stops if s.get('district') == d]
        d_grvs = [g for g in grievances if g.get('district') == d]
        print(f"     - {d}: {len(d_stops)} stops, {len(d_grvs)} grievances")

if __name__ == '__main__':
    main()
