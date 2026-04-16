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


# Real Trichy contractor mapping
TRICHY_CONTRACTORS = {
    'cleaning': {'name': 'S.R. Vedhaah', 'type': 'Sanitation & Cleaning', 'detail': 'Primary private agency for city-wide sanitation across all 65 wards'},
    'housekeeping': {'name': 'VDoDay House Keeping', 'type': 'Facility Management', 'detail': 'Corporate & government facility management contractor'},
    'waste': {'name': 'Eco Wise', 'type': 'Waste Management', 'detail': 'Municipal solid waste & e-waste specialist'},
    'civil': {'name': 'M/s. Jyothi Constructions', 'type': 'Civil Contractor (Class-I)', 'detail': 'Government-approved, Palpannai, Trichy'},
    'civil_alt': {'name': 'Tamil Builders', 'type': 'Civil Contractor', 'detail': 'Handles municipal civil infrastructure projects'},
    'infra_major': {'name': 'Larsen & Toubro (L&T)', 'type': 'Infrastructure (Class-I)', 'detail': 'Executing 90%+ of underground drainage projects in Trichy'},
    'manpower': {'name': 'Vision Care Services Pvt Ltd', 'type': 'Manpower Outsourcing', 'detail': 'Oldest agency in Trichy, healthcare & facility staffing'},
    'manpower_alt': {'name': 'First Choice Outsourcing Services', 'type': 'Security & Manpower', 'detail': 'Government department manpower & security services'},
    'staffing': {'name': 'SPM HR Solutions', 'type': 'Staffing & Placement', 'detail': 'Leading consultant for government & corporate staffing'},
    'transport': {'name': 'Sri Renu Travels', 'type': 'Transport Services', 'detail': 'Fleet services for corporate & government'},
    'building': {'name': 'Sri Venket Lakshmi Associates', 'type': 'Building Contractor', 'detail': 'High-rated government-approved infrastructure services'}
}

# Map each sub-problem category to its real contractor
CATEGORY_CONTRACTOR_MAP = {
    'toilet_facilities': TRICHY_CONTRACTORS['cleaning'],
    'infrastructure': TRICHY_CONTRACTORS['civil'],
    'audio_visual': TRICHY_CONTRACTORS['manpower'],
    'signage_braille': TRICHY_CONTRACTORS['civil_alt'],
    'staff_assistance': TRICHY_CONTRACTORS['staffing'],
    'ramp_wheelchair': TRICHY_CONTRACTORS['building']
}


@app.route('/api/common-issues')
def get_common_issues():
    """Aggregate the most common grievance issues across all bus stands with contractor info"""
    try:
        from services.scoring_engine import load_stops, load_grievances
        from services.nlp_engine import classify_grievance, classify_sub_problem, CLUSTER_DEFINITIONS

        stops = load_stops()
        grievances = load_grievances()
        
        # Build a stop name lookup
        stop_names = {s['id']: s['name'] for s in stops}
        
        # Classify every grievance
        issue_tracker = {}  # sub_problem -> {count, stops set, category, ...}
        
        for g in grievances:
            cluster_id, _, _ = classify_grievance(g['text'])
            sub = classify_sub_problem(g['text'], cluster_id)
            
            key = sub['sub_problem']
            if key not in issue_tracker:
                contractor = CATEGORY_CONTRACTOR_MAP.get(cluster_id, TRICHY_CONTRACTORS['civil'])
                issue_tracker[key] = {
                    'sub_problem': key,
                    'category': CLUSTER_DEFINITIONS[cluster_id]['label'],
                    'category_color': CLUSTER_DEFINITIONS[cluster_id]['color'],
                    'count': 0,
                    'affected_stops': set(),
                    'primary_authority': sub['primary_authority'],
                    'priority': sub['priority'],
                    'action': sub['action'],
                    'contractor_name': contractor['name'],
                    'contractor_type': contractor['type'],
                    'contractor_detail': contractor['detail'],
                    'fault_by': sub.get('fault_by', 'Unknown'),
                    'contractor_resp': sub.get('contractor_resp', ''),
                    'civilian_resp': sub.get('civilian_resp', '')
                }
            
            issue_tracker[key]['count'] += 1
            stop_name = stop_names.get(g['stop_id'], g['stop_id'])
            issue_tracker[key]['affected_stops'].add(stop_name)
        
        # Convert sets to lists and sort by frequency
        results = []
        for issue in issue_tracker.values():
            issue['affected_stops'] = sorted(list(issue['affected_stops']))
            issue['stops_affected_count'] = len(issue['affected_stops'])
            results.append(issue)
        
        results.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': results[:10]  # Top 10 most common issues
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stops/<stop_id>/details')
def get_stop_details(stop_id):
    """Get rich deep-analytics metadata for a specific stop"""
    try:
        from services.scoring_engine import load_stops, load_grievances
        from services.nlp_engine import classify_grievance, classify_sub_problem, CLUSTER_DEFINITIONS
        import random
        
        stops = load_stops()
        all_grievances = load_grievances()
        
        stop = next((s for s in stops if s['id'] == stop_id), None)
        if not stop:
            return jsonify({'success': False, 'error': 'Stop not found'}), 404
            
        # Filter grievances
        raw_grievances = [g for g in all_grievances if g['stop_id'] == stop_id]
        
        # Process them through NLP classifier + sub-problem detector
        stop_grievances = []
        category_counts = {cid: 0 for cid in CLUSTER_DEFINITIONS.keys()}
        
        for g in raw_grievances:
            cluster_id, confidence, _ = classify_grievance(g['text'])
            category_counts[cluster_id] += 1
            
            # Deep classify: sub-problem, authority, priority, action
            sub = classify_sub_problem(g['text'], cluster_id)
            
            stop_grievances.append({
                **g,
                'cluster_label': CLUSTER_DEFINITIONS[cluster_id]['label'],
                'cluster_color': CLUSTER_DEFINITIONS[cluster_id]['color'],
                'sub_problem': sub['sub_problem'],
                'primary_authority': sub['primary_authority'],
                'secondary_authority': sub['secondary_authority'],
                'priority': sub['priority'],
                'suggestion': sub['action'],
                'fault_by': sub.get('fault_by', 'Unknown'),
                'contractor_resp': sub.get('contractor_resp', ''),
                'civilian_resp': sub.get('civilian_resp', '')
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
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    print(f"\n[*] Accessibility Auditor API Server Starting...")
    print(f"[*] City: Tiruchirappalli (Trichy), Tamil Nadu")
    print(f"[*] Port: {port} | Debug: {debug}")
    print(f"[*] Frontend: http://localhost:{port}")
    print(f"[*] API: http://localhost:{port}/api/stops\n")
    app.run(debug=debug, host='0.0.0.0', port=port)
