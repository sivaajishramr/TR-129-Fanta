"""
Tensor'26 - Inclusive Public Transport Accessibility Auditor
Backend API Server (Flask)
"""
from flask import Flask, jsonify, send_from_directory, request
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
    """Get 12-month historical trend data with per-stop breakdowns"""
    try:
        import json, random
        from services.scoring_engine import load_stops, load_checklist, calculate_gap_score
        
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical_trends.json')
        with open(file_path, 'r') as f:
            trends_data = json.load(f)
        
        # Generate per-stop 12-month trends based on current gap scores
        stops = load_stops()
        checklist = load_checklist()
        months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
        
        stop_trends = {}
        for stop in stops:
            scored = calculate_gap_score(stop, checklist)
            current_gap = scored['gap_score']
            stop_id = stop['id']
            
            # Use stop_id hash as seed for consistent random data
            seed = sum(ord(c) for c in stop_id)
            rng = random.Random(seed)
            
            # Generate 12-month trajectory (starts worse, trends toward current)
            start_gap = min(100, current_gap + rng.uniform(8, 22))
            monthly_scores = []
            
            for i in range(12):
                progress = i / 11.0
                base = start_gap - (start_gap - current_gap) * progress
                noise = rng.uniform(-2.5, 2.5)
                score = round(max(0, min(100, base + noise)), 1)
                monthly_scores.append(score)
            
            # Compute grievance counts per month (higher gap = more grievances)
            monthly_grievances = []
            for score in monthly_scores:
                base_g = int(score * 0.08 + rng.randint(0, 3))
                monthly_grievances.append(max(0, base_g))
            
            stop_trends[stop_id] = {
                'name': stop['name'],
                'gap_scores': monthly_scores,
                'grievance_counts': monthly_grievances,
                'current_gap': current_gap,
                'start_gap': round(monthly_scores[0], 1),
                'improvement': round(monthly_scores[0] - monthly_scores[-1], 1)
            }
        
        return jsonify({
            'success': True,
            'data': trends_data,
            'stop_trends': stop_trends,
            'months': months
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """AI Chat endpoint — answers accessibility questions using real data"""
    try:
        from services.chat_engine import process_chat
        data = request.get_json()
        user_message = data.get('message', '')
        response = process_chat(user_message)
        return jsonify({'success': True, 'response': response})
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

# Company profiles with detailed research data
COMPANY_PROFILES = {
    'S.R. Vedhaah': {
        'name': 'S.R. Vedhaah',
        'type': 'Sanitation & Solid Waste Management',
        'location': 'Tiruchirappalli, Tamil Nadu',
        'operations_head': 'Kishore Mohan',
        'contract_with': 'Tiruchirappalli City Municipal Corporation (TCMC)',
        'since': 'June 2023',
        'workforce': '~2,000 sanitation workers',
        'coverage': 'All 65 wards of Trichy city',
        'key_projects': [
            'City-wide door-to-door waste collection using battery-operated & LCV vehicles',
            'Litter-Free Corridor initiative on major city roads',
            'Conversion of identified "garbage black spots" into green spaces with waste-to-art exhibits',
            'Coordination of non-recyclable plastic waste transport to cement plants as RDF (Refuse-Derived Fuel)',
            'Reduction of dependency on Ariyamangalam dump yard through sustainable waste processing'
        ],
        'specializations': [
            'Door-to-door solid waste collection',
            'Street sweeping & road sanitation',
            'Commercial area intensified collection',
            'Waste segregation & recycling coordination',
            'Green space beautification drives'
        ],
        'performance': 'Monitored directly by Trichy City Corporation with regular reviews of collection status, beautified spots, and litter-free corridor effectiveness.',
        'rating': '4.2/5'
    },
    'Larsen & Toubro (L&T)': {
        'name': 'Larsen & Toubro (L&T)',
        'type': 'Infrastructure & Engineering (Class-I)',
        'location': 'Mumbai (HQ), Trichy Division Office',
        'operations_head': 'Water & Effluent Treatment Business Unit',
        'contract_with': 'Tiruchirappalli City Corporation / AMRUT Mission',
        'since': '2019',
        'workforce': '500+ engineers & workers (Trichy UGD project)',
        'coverage': 'Phase III Underground Drainage — multiple wards',
        'key_projects': [
            'Phase III Underground Drainage (UGD) scheme for Tiruchirappalli — 90%+ execution',
            'Laying of sewer pipelines across city wards',
            'Construction of RCC manholes and pumping/lifting stations',
            'House Service Connections (HSC) to residential properties',
            'Project funded under AMRUT (Atal Mission for Rejuvenation and Urban Transformation)'
        ],
        'specializations': [
            'Underground drainage systems',
            'Sewage Treatment Plants (STP)',
            'Water supply infrastructure',
            'Heavy civil engineering',
            'Smart City infrastructure projects'
        ],
        'performance': 'Phase III significantly completed and moving towards commissioning as of 2025-26. L&T is the dominant infrastructure contractor in Trichy.',
        'rating': '4.7/5'
    },
    'M/s. Jyothi Constructions': {
        'name': 'M/s. Jyothi Constructions',
        'type': 'Civil Contractor (Class-I)',
        'location': 'Jyothi Nagar, Chennai Bye Pass Road, Trichy-620010',
        'operations_head': 'Partnership Firm',
        'contract_with': 'Tamil Nadu PWD, Highways Dept., Trichy City Corporation',
        'since': '2005+',
        'workforce': '200+ skilled construction workers',
        'coverage': 'Trichy district and surrounding areas',
        'key_projects': [
            'Multiple government infrastructure tenders via TN e-Procurement portal',
            'Building construction for government departments',
            'Road and bridge construction under PWD contracts',
            'Bus stand infrastructure construction and renovation',
            'Public building construction for municipal bodies'
        ],
        'specializations': [
            'Government building construction',
            'Road & bridge infrastructure',
            'Public works (PWD) projects',
            'Bus stand & transit infrastructure',
            'Reinforced concrete structures'
        ],
        'performance': 'Registered Class-I contractor with GSTIN 33AAFFJ1714R1Z7. Regularly participates in state-level infrastructure tenders. Verified on TN Government e-Procurement portal.',
        'rating': '4.0/5'
    },
    'Tamil Builders': {
        'name': 'Tamil Builders',
        'type': 'Civil & Signage Contractor',
        'location': 'Tiruchirappalli, Tamil Nadu',
        'operations_head': 'Proprietorship Firm',
        'contract_with': 'Trichy City Corporation - Works Division',
        'since': '2010+',
        'workforce': '100+ workers',
        'coverage': 'Trichy urban and semi-urban areas',
        'key_projects': [
            'Municipal signage installation across bus stands',
            'Bilingual (Tamil/English) directional & wayfinding signage',
            'Pavement and footpath construction',
            'Internal road construction within bus stand premises',
            'Bench and seating infrastructure installation'
        ],
        'specializations': [
            'Signage fabrication & installation (reflective, LED)',
            'Pavement & interlocking tile work',
            'Small-scale civil infrastructure',
            'Municipal furniture (benches, railings)',
            'Wayfinding & directional signage per IRC standards'
        ],
        'performance': 'Regular vendor for Trichy Corporation minor works. Known for timely completion of small-to-medium infrastructure projects.',
        'rating': '3.8/5'
    },
    'Sri Venket Lakshmi Associates': {
        'name': 'Sri Venket Lakshmi Associates',
        'type': 'Building & Accessibility Contractor',
        'location': 'Tiruchirappalli, Tamil Nadu',
        'operations_head': 'Proprietorship',
        'contract_with': 'Trichy City Corporation, Government Departments',
        'since': '2008+',
        'workforce': '150+ workers',
        'coverage': 'Trichy and surrounding districts',
        'key_projects': [
            'Government-approved building construction and renovation',
            'Ramp and accessibility infrastructure per RPWD Act 2016',
            'Handrail installation and wheelchair pathway construction',
            'Bus shelter construction and pre-fab shelter installation',
            'Public toilet block construction for municipalities'
        ],
        'specializations': [
            'RPWD Act-compliant accessibility infrastructure',
            'Ramp construction (1:12 gradient, anti-skid, TGSI)',
            'Stainless steel handrail fabrication & installation',
            'Pre-fabricated bus shelter erection',
            'Government building renovation & retrofitting'
        ],
        'performance': 'Listed as government-approved contractor on multiple platforms. Specializes in accessibility retrofitting under AMRUT and Smart City Mission.',
        'rating': '4.1/5'
    },
    'Vision Care Services Pvt Ltd': {
        'name': 'Vision Care Services Pvt Ltd',
        'type': 'Manpower & Facility Outsourcing',
        'location': 'Tiruchirappalli, Tamil Nadu',
        'operations_head': 'Pvt Ltd Company',
        'contract_with': 'TNSTC Trichy Division, Government Hospitals, Corporates',
        'since': '2000+',
        'workforce': '1,000+ deployed staff across contracts',
        'coverage': 'Trichy, Chennai, across Tamil Nadu',
        'key_projects': [
            'Manpower outsourcing for TNSTC bus stands (help-desk, security)',
            'Healthcare facility staffing for government hospitals',
            'Corporate facility management services',
            'Security guard deployment for public infrastructure',
            'Audio-visual system maintenance for transit facilities'
        ],
        'specializations': [
            'Manpower outsourcing & staffing',
            'Healthcare facility management',
            'Security services for government premises',
            'Help-desk and customer service deployment',
            'AV and PA system maintenance'
        ],
        'performance': 'One of the oldest outsourcing agencies in Trichy. Supplies trained manpower to government and private sector across Tamil Nadu.',
        'rating': '3.9/5'
    },
    'Eco Wise': {
        'name': 'Eco Wise',
        'type': 'Waste Management Specialist',
        'location': 'Tiruchirappalli, Tamil Nadu',
        'operations_head': 'Specialist Firm',
        'contract_with': 'TCMC, Industrial Estates, Residential Complexes',
        'since': '2015+',
        'workforce': '100+ workers',
        'coverage': 'Trichy industrial and residential sectors',
        'key_projects': [
            'Municipal solid waste processing and disposal',
            'E-waste collection and certified recycling',
            'Industrial waste management for manufacturing units',
            'Composting and bio-waste processing facilities',
            'Hazardous waste handling and transport'
        ],
        'specializations': [
            'E-waste collection & certified disposal',
            'Municipal solid waste processing',
            'Industrial hazardous waste management',
            'Composting & organic waste conversion',
            'Compliance with TNPCB (Pollution Control Board) norms'
        ],
        'performance': 'Specialized firm managing both municipal and industrial waste streams. TNPCB-compliant operations.',
        'rating': '4.0/5'
    },
    'SPM HR Solutions': {
        'name': 'SPM HR Solutions',
        'type': 'Staffing & Placement Consultant',
        'location': 'Tiruchirappalli, Tamil Nadu',
        'operations_head': 'Consultancy Firm',
        'contract_with': 'TNSTC, Government Departments, Private Corporates',
        'since': '2012+',
        'workforce': '500+ placed staff',
        'coverage': 'Trichy and across Tamil Nadu',
        'key_projects': [
            'Staffing for TNSTC bus stand help-desks and counters',
            'Government department temporary staffing',
            'Corporate HR outsourcing and recruitment',
            'Training programs for government-deployed staff',
            'Disability awareness and sensitivity training coordination'
        ],
        'specializations': [
            'Government staffing & placement',
            'HR outsourcing for public sector',
            'Training and skill development programs',
            'Temporary and contract staffing',
            'Customer service staff recruitment'
        ],
        'performance': 'Leading HR consultant in Trichy region. Known for reliable government staffing placement and training coordination.',
        'rating': '3.7/5'
    }
}


@app.route('/api/company-profile')
def get_company_profile():
    """Return detailed profile for a specific contractor company"""
    from flask import request
    company_name = request.args.get('name', '')
    profile = COMPANY_PROFILES.get(company_name)
    if profile:
        return jsonify({'success': True, 'data': profile})
    return jsonify({'success': False, 'error': f'Company not found: {company_name}'}), 404


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
        
        # ── AI Contractor Scoring Engine ──
        # Aggregate stats per contractor
        contractor_stats = {}
        total_grievances = len(grievances)
        total_stops = len(stops)
        
        for issue in results:
            cname = issue['contractor_name']
            if cname not in contractor_stats:
                contractor_stats[cname] = {
                    'total_grievances': 0,
                    'high_count': 0,
                    'medium_count': 0,
                    'low_count': 0,
                    'contractor_fault_count': 0,
                    'affected_stops': set(),
                    'issue_types': 0
                }
            stats = contractor_stats[cname]
            stats['total_grievances'] += issue['count']
            stats['issue_types'] += 1
            stats['affected_stops'].update(issue['affected_stops'])
            if issue['priority'] == 'High':
                stats['high_count'] += issue['count']
            elif issue['priority'] == 'Medium':
                stats['medium_count'] += issue['count']
            else:
                stats['low_count'] += issue['count']
            if issue['fault_by'] in ('Contractor', 'Both'):
                stats['contractor_fault_count'] += issue['count']
        
        # Compute AI score (0-100, higher = better performance)
        for cname, stats in contractor_stats.items():
            g_count = stats['total_grievances']
            stops_affected = len(stats['affected_stops'])
            
            # Base score starts at 100
            score = 100.0
            
            # Penalty: grievance volume relative to total (-0 to -25)
            volume_ratio = g_count / max(total_grievances, 1)
            score -= volume_ratio * 25
            
            # Penalty: severity weighting (-0 to -30)
            severity_penalty = (stats['high_count'] * 3 + stats['medium_count'] * 1.5 + stats['low_count'] * 0.5)
            max_severity = g_count * 3
            severity_ratio = severity_penalty / max(max_severity, 1)
            score -= severity_ratio * 30
            
            # Penalty: contractor at fault ratio (-0 to -25)
            fault_ratio = stats['contractor_fault_count'] / max(g_count, 1)
            score -= fault_ratio * 25
            
            # Penalty: geographic spread (-0 to -20)
            spread_ratio = stops_affected / max(total_stops, 1)
            score -= spread_ratio * 20
            
            stats['ai_score'] = round(max(0, min(100, score)), 1)
            
            # Grade
            s = stats['ai_score']
            if s >= 85:
                stats['grade'] = 'A+'
            elif s >= 75:
                stats['grade'] = 'A'
            elif s >= 65:
                stats['grade'] = 'B+'
            elif s >= 55:
                stats['grade'] = 'B'
            elif s >= 45:
                stats['grade'] = 'C'
            elif s >= 35:
                stats['grade'] = 'D'
            else:
                stats['grade'] = 'F'
            
            stats['affected_stops'] = len(stats['affected_stops'])
        
        # Inject AI score into each issue
        for issue in results:
            cname = issue['contractor_name']
            stats = contractor_stats.get(cname, {})
            issue['ai_score'] = stats.get('ai_score', 0)
            issue['ai_grade'] = stats.get('grade', '?')
            issue['contractor_total_grievances'] = stats.get('total_grievances', 0)
            issue['contractor_high_count'] = stats.get('high_count', 0)
            issue['contractor_stops_affected'] = stats.get('affected_stops', 0)
        
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
