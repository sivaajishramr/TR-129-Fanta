"""
Scoring Engine - Calculates accessibility gap scores for transit stops
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')


def load_checklist():
    """Load the accessibility standards checklist"""
    with open(os.path.join(DATA_DIR, 'accessibility_checklist.json'), 'r') as f:
        return json.load(f)


def load_stops():
    """Load transit stop data"""
    with open(os.path.join(DATA_DIR, 'transit_stops.json'), 'r') as f:
        return json.load(f)


def load_grievances():
    """Load citizen grievances"""
    with open(os.path.join(DATA_DIR, 'grievances.json'), 'r') as f:
        return json.load(f)


def calculate_gap_score(stop, checklist):
    """
    Calculate the accessibility gap score for a single stop.
    
    Gap Score = (sum of weights of missing features) / max_score * 100
    Higher score = worse accessibility (more gaps)
    """
    criteria = checklist['criteria']
    max_score = checklist['max_score']
    missing_weight = 0
    present_weight = 0
    missing_features = []
    present_features = []

    for criterion in criteria:
        field = criterion['field']
        has_feature = stop['features'].get(field, False)
        
        if not has_feature:
            missing_weight += criterion['weight']
            missing_features.append({
                'id': criterion['id'],
                'name': criterion['name'],
                'weight': criterion['weight'],
                'description': criterion['description'],
                'source': criterion['source']
            })
        else:
            present_weight += criterion['weight']
            present_features.append({
                'id': criterion['id'],
                'name': criterion['name'],
                'weight': criterion['weight']
            })

    gap_score = round((missing_weight / max_score) * 100, 1)
    
    # Determine priority level
    if gap_score > 70:
        priority = 'critical'
        priority_label = '[!] Critical'
    elif gap_score > 40:
        priority = 'warning'
        priority_label = '[~] Warning'
    else:
        priority = 'good'
        priority_label = '[OK] Good'

    return {
        'gap_score': gap_score,
        'priority': priority,
        'priority_label': priority_label,
        'missing_features': missing_features,
        'present_features': present_features,
        'missing_count': len(missing_features),
        'present_count': len(present_features),
        'total_criteria': len(criteria)
    }


def calculate_priority_score(gap_score, grievance_count, daily_footfall):
    """
    Calculate overall priority score combining gap score, grievances, and footfall.
    
    Priority = gap_score * 0.5 + normalized_grievances * 0.3 + normalized_footfall * 0.2
    """
    # Normalize grievance count (assume max 10 per stop)
    norm_grievances = min(grievance_count / 10, 1.0) * 100
    
    # Normalize footfall (assume max 25000)
    norm_footfall = min(daily_footfall / 25000, 1.0) * 100
    
    priority_score = round(
        gap_score * 0.5 + norm_grievances * 0.3 + norm_footfall * 0.2, 1
    )
    
    return priority_score


def get_all_scores():
    """Calculate gap scores for all stops and return sorted by priority"""
    checklist = load_checklist()
    stops = load_stops()
    grievances = load_grievances()
    
    # Count grievances per stop
    grievance_counts = {}
    for g in grievances:
        sid = g['stop_id']
        grievance_counts[sid] = grievance_counts.get(sid, 0) + 1
    
    results = []
    total_gap = 0
    
    for stop in stops:
        score_data = calculate_gap_score(stop, checklist)
        g_count = grievance_counts.get(stop['id'], 0)
        priority_score = calculate_priority_score(
            score_data['gap_score'], g_count, stop.get('daily_footfall', 0)
        )
        
        total_gap += score_data['gap_score']
        
        results.append({
            'id': stop['id'],
            'name': stop['name'],
            'lat': stop['lat'],
            'lng': stop['lng'],
            'type': stop['type'],
            'district': stop.get('district', 'Tiruchirappalli'),
            'daily_footfall': stop.get('daily_footfall', 0),
            'last_audit_date': stop.get('last_audit_date', 'N/A'),
            'gap_score': score_data['gap_score'],
            'priority': score_data['priority'],
            'priority_label': score_data['priority_label'],
            'priority_score': priority_score,
            'missing_features': score_data['missing_features'],
            'present_features': score_data['present_features'],
            'missing_count': score_data['missing_count'],
            'present_count': score_data['present_count'],
            'total_criteria': score_data['total_criteria'],
            'grievance_count': g_count
        })
    
    # Sort by priority score (highest = most urgent)
    results.sort(key=lambda x: x['priority_score'], reverse=True)
    
    # Add rank
    for i, r in enumerate(results):
        r['rank'] = i + 1
    
    # Summary stats
    total_stops = len(results)
    critical_count = sum(1 for r in results if r['priority'] == 'critical')
    warning_count = sum(1 for r in results if r['priority'] == 'warning')
    good_count = sum(1 for r in results if r['priority'] == 'good')
    avg_gap = round(total_gap / total_stops, 1) if total_stops > 0 else 0
    coverage = 100.0  # We analyze all stops in our dataset
    
    summary = {
        'total_stops': total_stops,
        'analyzed_stops': total_stops,
        'coverage_percent': coverage,
        'critical_count': critical_count,
        'warning_count': warning_count,
        'good_count': good_count,
        'average_gap_score': avg_gap,
        'total_grievances': len(grievances),
        'city': 'All Districts',
        'state': 'Tamil Nadu'
    }
    
    return {
        'summary': summary,
        'stops': results
    }
