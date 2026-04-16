"""
Tensor'26 - Inclusive Public Transport Accessibility Auditor
Backend API Server (Flask)
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
import time

from services.scoring_engine import get_all_scores, load_checklist
from services.nlp_engine import cluster_grievances

app = Flask(__name__, static_folder='../Frontend', static_url_path='')
CORS(app)


@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Accessibility Auditor API',
        'version': '1.0.0'
    })


@app.route('/api/stops')
def get_stops():
    """Get all transit stops with accessibility gap scores"""
    try:
        data = get_all_scores()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/grievances')
def get_grievances():
    """Get clustered grievance analysis"""
    try:
        data = cluster_grievances()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report')
def get_report():
    """Get full audit report data"""
    try:
        start_time = time.time()
        
        scores_data = get_all_scores()
        grievance_data = cluster_grievances()
        checklist = load_checklist()
        
        generation_time = round(time.time() - start_time, 2)
        
        report = {
            'title': 'Public Transport Accessibility Audit Report',
            'city': 'Tiruchirappalli (Trichy)',
            'state': 'Tamil Nadu',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'generation_time_seconds': generation_time,
            'summary': scores_data['summary'],
            'stops': scores_data['stops'],
            'grievance_analysis': {
                'total_grievances': grievance_data['total_grievances'],
                'silhouette_score': grievance_data['silhouette_score'],
                'silhouette_quality': grievance_data['silhouette_quality'],
                'clusters': grievance_data['clusters']
            },
            'checklist': checklist,
            'top_priority_stops': scores_data['stops'][:10],
            'sdg_alignment': {
                'sdg_10': 'Reduced Inequalities - Ensuring equal access to public transport for persons with disabilities',
                'sdg_11': 'Sustainable Cities - Making urban transport inclusive, safe, and accessible'
            }
        }
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/checklist')
def get_checklist():
    """Get the accessibility standards checklist"""
    try:
        checklist = load_checklist()
        return jsonify({
            'success': True,
            'data': checklist
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trends')
def get_trends():
    """Get 12-month historical trend data"""
    try:
        import json
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical_trends.json')
        with open(file_path, 'r') as f:
            trends_data = json.load(f)
            
        return jsonify({
            'success': True,
            'data': trends_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stops/<stop_id>/details')
def get_stop_details(stop_id):
    """Get rich deep-analytics metadata for a specific stop"""
    try:
        from services.scoring_engine import load_stops, load_grievances
        from services.nlp_engine import classify_grievance, CLUSTER_DEFINITIONS
        import random
        
        # Prevention suggestions mapped to each category
        SUGGESTIONS = {
            'ramp_wheelchair': [
                'Install ramps with 1:12 slope ratio at all entry/exit points',
                'Add anti-skid strips on ramp surfaces for wet weather safety',
                'Widen doorways to minimum 900mm for wheelchair clearance',
                'Deploy portable ramps for buses without low-floor access'
            ],
            'audio_visual': [
                'Install audio announcement systems for bus arrivals and departures',
                'Add LED display boards showing route numbers and destinations',
                'Deploy text-to-speech kiosks for visually impaired passengers',
                'Install beeping signals at pedestrian crossings near the stop'
            ],
            'signage_braille': [
                'Install Braille route maps at all boarding points',
                'Add tactile floor markers guiding to ticket counters and platforms',
                'Place high-contrast signage with large fonts at eye level',
                'Deploy QR-code based audio guide stickers on signboards'
            ],
            'toilet_facilities': [
                'Ensure accessible toilets are unlocked, clean, and well-maintained',
                'Install grab bars and emergency pull cords in all restrooms',
                'Add sheltered seating with backrests in the waiting area',
                'Provide drinking water stations at wheelchair-accessible height'
            ],
            'staff_assistance': [
                'Conduct quarterly disability awareness training for all staff',
                'Assign dedicated accessibility help-desk at peak hours',
                'Display staff assistance contact numbers at visible locations',
                'Establish a buddy-system for assisting passengers with disabilities'
            ],
            'infrastructure': [
                'Repair potholes and uneven surfaces on the approach road',
                'Install adequate LED lighting for safe night-time navigation',
                'Remove parked vehicles and obstructions from accessible pathways',
                'Add tactile ground surface indicators (TGSI) on all walkways'
            ]
        }
        
        stops = load_stops()
        all_grievances = load_grievances()
        
        stop = next((s for s in stops if s['id'] == stop_id), None)
        if not stop:
            return jsonify({'success': False, 'error': 'Stop not found'}), 404
            
        # Filter grievances
        raw_grievances = [g for g in all_grievances if g['stop_id'] == stop_id]
        
        # Process them through NLP classifier
        stop_grievances = []
        category_counts = {cid: 0 for cid in CLUSTER_DEFINITIONS.keys()}
        
        for g in raw_grievances:
            cluster_id, confidence, _ = classify_grievance(g['text'])
            category_counts[cluster_id] += 1
            
            # Pick a relevant suggestion for this grievance
            suggestions_pool = SUGGESTIONS.get(cluster_id, [])
            suggestion = random.choice(suggestions_pool) if suggestions_pool else 'Conduct a detailed accessibility audit for this issue.'
            
            stop_grievances.append({
                **g,
                'cluster_label': CLUSTER_DEFINITIONS[cluster_id]['label'],
                'cluster_color': CLUSTER_DEFINITIONS[cluster_id]['color'],
                'suggestion': suggestion
            })
            
        # Build categorical breakdown
        breakdown = []
        for cid, count in category_counts.items():
            breakdown.append({
                'id': cid,
                'label': CLUSTER_DEFINITIONS[cid]['label'],
                'color': CLUSTER_DEFINITIONS[cid]['color'],
                'count': count
            })
            
        return jsonify({
            'success': True,
            'data': {
                'stop_info': stop,
                'last_audit_date': stop.get('last_audit_date', 'N/A'),
                'grievances': stop_grievances,
                'breakdown': breakdown
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    print("\n[*] Accessibility Auditor API Server Starting...")
    print("[*] City: Tiruchirappalli (Trichy), Tamil Nadu")
    print("[*] Frontend: http://localhost:5000")
    print("[*] API: http://localhost:5000/api/stops")
    print("[*] Grievances: http://localhost:5000/api/grievances")
    print("[*] Report: http://localhost:5000/api/report\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
