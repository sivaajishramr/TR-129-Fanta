"""
NLP Engine - Grievance text clustering using TF-IDF and keyword-based classification
"""
import json
import os
import re
import math
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')

# Predefined cluster categories with keywords
CLUSTER_DEFINITIONS = {
    'ramp_wheelchair': {
        'label': 'Ramp & Wheelchair Access',
        'icon': '[W]',
        'keywords': ['ramp', 'wheelchair', 'slope', 'step', 'steps', 'climb', 'steep',
                     'narrow', 'width', 'handrail', 'handrails', 'kerb', 'curb',
                     'boarding', 'board', 'lift', 'lifted', 'carry', 'carried',
                     'walker', 'walking stick', 'mobility', 'low-floor', 'low floor'],
        'color': '#ef4444'
    },
    'audio_visual': {
        'label': 'Audio & Visual Signals',
        'icon': '[A]',
        'keywords': ['audio', 'signal', 'announcement', 'announce', 'blind',
                     'visually impaired', 'partially blind', 'hear', 'hearing',
                     'deaf', 'sound', 'speaker', 'display', 'led', 'screen',
                     'verbal', 'route number', 'bus number', 'identify'],
        'color': '#f97316'
    },
    'signage_braille': {
        'label': 'Signage & Braille',
        'icon': '[S]',
        'keywords': ['braille', 'sign', 'signage', 'signboard', 'board', 'route map',
                     'direction', 'navigate', 'navigation', 'information', 'read',
                     'unreadable', 'worn out', 'markers', 'reflective'],
        'color': '#8b5cf6'
    },
    'toilet_facilities': {
        'label': 'Toilet & Facilities',
        'icon': '[T]',
        'keywords': ['toilet', 'restroom', 'bathroom', 'washroom', 'grab bar',
                     'grab bars', 'locked', 'dirty', 'hygiene', 'hygienic',
                     'cleaning', 'shelter', 'seating', 'seat', 'bench',
                     'shade', 'rain', 'sun', 'heat', 'waiting area', 'quiet'],
        'color': '#06b6d4'
    },
    'staff_assistance': {
        'label': 'Staff & Assistance',
        'icon': '[P]',
        'keywords': ['staff', 'help', 'assistance', 'assist', 'refused',
                     'ignored', 'rude', 'unhelpful', 'trained', 'training',
                     'awareness', 'conductor', 'driver', 'confused',
                     'discrimination', 'job'],
        'color': '#10b981'
    },
    'infrastructure': {
        'label': 'Infrastructure & Safety',
        'icon': '[I]',
        'keywords': ['broken', 'crumbled', 'pothole', 'potholes', 'uneven',
                     'pavement', 'footpath', 'drainage', 'gap', 'dangerous',
                     'unsafe', 'risk', 'accident', 'fell', 'fall', 'trip',
                     'lighting', 'dark', 'night', 'repair', 'maintenance',
                     'blocked', 'parked', 'obstruction'],
        'color': '#eab308'
    }
}


def preprocess_text(text):
    """Clean and tokenize text"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    # Remove common stop words
    stop_words = {'i', 'me', 'my', 'the', 'a', 'an', 'is', 'are', 'was', 'were',
                  'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                  'will', 'would', 'could', 'should', 'may', 'might', 'shall',
                  'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                  'from', 'as', 'into', 'through', 'during', 'before', 'after',
                  'this', 'that', 'these', 'those', 'it', 'its', 'and', 'but',
                  'or', 'not', 'no', 'so', 'if', 'than', 'too', 'very', 'just',
                  'about', 'up', 'out', 'they', 'them', 'their', 'we', 'our',
                  'he', 'she', 'his', 'her', 'who', 'which', 'what', 'when',
                  'where', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
                  'most', 'other', 'some', 'such', 'only', 'own', 'same', 'here',
                  'there', 'also', 'over', 'any', 'even', 'because', 'between'}
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
    return tokens


def classify_grievance(text):
    """
    Classify a single grievance into one or more clusters based on keyword matching.
    Returns the best matching cluster and confidence score.
    """
    tokens = preprocess_text(text)
    text_lower = text.lower()
    
    scores = {}
    
    for cluster_id, cluster_def in CLUSTER_DEFINITIONS.items():
        score = 0
        matched_keywords = []
        
        for keyword in cluster_def['keywords']:
            if ' ' in keyword:
                # Multi-word keyword - check in original text
                if keyword in text_lower:
                    score += 2  # Higher weight for multi-word matches
                    matched_keywords.append(keyword)
            else:
                if keyword in tokens:
                    score += 1
                    matched_keywords.append(keyword)
        
        if score > 0:
            scores[cluster_id] = {
                'score': score,
                'matched_keywords': matched_keywords
            }
    
    if not scores:
        return 'infrastructure', 0, []  # Default fallback
    
    # Get the best matching cluster
    best_cluster = max(scores, key=lambda k: scores[k]['score'])
    best_score = scores[best_cluster]['score']
    max_possible = len(CLUSTER_DEFINITIONS[best_cluster]['keywords'])
    confidence = round(min(best_score / max(max_possible * 0.3, 1), 1.0), 2)
    
    return best_cluster, confidence, scores[best_cluster]['matched_keywords']


# ===== SUB-PROBLEM CLASSIFICATION & AUTHORITY MAPPING =====
# Trichy-specific: Bus stands owned by Trichy City Corporation, 
# operations by TNSTC. Cleaning, electrical, toilet maintenance 
# outsourced to private contractors via PPP / tender model.

SUB_PROBLEM_RULES = {
    'toilet_facilities': [
        {
            'keywords': ['not clean', 'dirty', 'unhygienic', 'filthy', 'smelly toilet'],
            'sub_problem': 'Toilet not clean',
            'primary_authority': 'Private Cleaning Contractor (Trichy Corp.)',
            'secondary_authority': 'Trichy City Corporation - Health Wing',
            'priority': 'High',
            'action': 'Issue penalty notice to contractor and deploy immediate deep-cleaning team'
        },
        {
            'keywords': ['no water', 'water supply', 'dry tap', 'no tap water'],
            'sub_problem': 'No water supply',
            'primary_authority': 'Trichy City Corporation - Water Supply Division',
            'secondary_authority': 'Private Plumbing Contractor',
            'priority': 'High',
            'action': 'Restore water supply and install overhead tank with auto-fill mechanism'
        },
        {
            'keywords': ['water not coming', 'irregular water', 'water timing'],
            'sub_problem': 'Water not coming regularly',
            'primary_authority': 'Trichy City Corporation - Water Supply Division',
            'secondary_authority': None,
            'priority': 'Medium',
            'action': 'Schedule regular water supply timings and install storage tank with pump'
        },
        {
            'keywords': ['poor water', 'bad water', 'water quality', 'contaminated'],
            'sub_problem': 'Poor water quality',
            'primary_authority': 'Trichy City Corporation - Health Wing',
            'secondary_authority': 'Private Tank Maintenance Contractor',
            'priority': 'High',
            'action': 'Test water quality and clean storage tanks immediately per TWAD standards'
        },
        {
            'keywords': ['tank not cleaned', 'water tank', 'tank dirty'],
            'sub_problem': 'Water tank not cleaned',
            'primary_authority': 'Private Tank Maintenance Contractor',
            'secondary_authority': 'Trichy City Corporation',
            'priority': 'Medium',
            'action': 'Schedule quarterly tank cleaning per contract KPI and issue penalty if overdue'
        },
        {
            'keywords': ['broken flush', 'flush not working', 'fittings', 'broken tap', 'leaking'],
            'sub_problem': 'Broken flush or fittings',
            'primary_authority': 'Private Plumbing Contractor',
            'secondary_authority': 'Trichy City Corporation - Works Division',
            'priority': 'Medium',
            'action': 'Replace broken fittings within 48 hours per maintenance SLA'
        },
        {
            'keywords': ['no soap', 'handwash', 'sanitizer', 'no hand wash'],
            'sub_problem': 'No soap or handwash',
            'primary_authority': 'Private Housekeeping Contractor',
            'secondary_authority': None,
            'priority': 'Low',
            'action': 'Refill soap dispensers per daily checklist and deduct penalty for lapse'
        },
        {
            'keywords': ['bad smell', 'stench', 'odor', 'foul smell'],
            'sub_problem': 'Bad smell',
            'primary_authority': 'Private Cleaning Contractor (Trichy Corp.)',
            'secondary_authority': 'Trichy City Corporation - Health Wing',
            'priority': 'Medium',
            'action': 'Increase cleaning frequency to 3x/day and apply enzymatic deodorizer'
        },
        {
            'keywords': ['disabled toilet', 'accessible toilet', 'wheelchair toilet', 'no disabled'],
            'sub_problem': 'No disabled-friendly toilet',
            'primary_authority': 'Trichy City Corporation - Works Division',
            'secondary_authority': 'TNSTC Trichy Division',
            'priority': 'High',
            'action': 'Construct RPWD-compliant accessible toilet with grab bars, 900mm door, and emergency cord'
        }
    ],
    'infrastructure': [
        {
            'keywords': ['broken pavement', 'cracked pavement', 'pavement damage'],
            'sub_problem': 'Broken pavement',
            'primary_authority': 'Trichy City Corporation - Engineering Wing',
            'secondary_authority': 'Private Civil Contractor',
            'priority': 'Medium',
            'action': 'Repair pavement with anti-skid interlocking tiles per Corporation standards'
        },
        {
            'keywords': ['pothole', 'potholes', 'road damage', 'road condition'],
            'sub_problem': 'Potholes near bus stop',
            'primary_authority': 'Trichy City Corporation - Roads Division',
            'secondary_authority': 'Highways Department (if NH/SH road)',
            'priority': 'High',
            'action': 'Fill potholes within 7 days and resurface approach road under TNRSP scheme'
        },
        {
            'keywords': ['no shelter', 'no roof', 'no shade', 'exposed', 'rain', 'sun'],
            'sub_problem': 'No shelter',
            'primary_authority': 'Trichy City Corporation - Works Division',
            'secondary_authority': 'TNSTC Trichy Division',
            'priority': 'High',
            'action': 'Install weather-proof bus shelter with seating via Smart City Mission funds'
        },
        {
            'keywords': ['waterlogging', 'flooding', 'water stagnation', 'drainage', 'drain blocked'],
            'sub_problem': 'Waterlogging',
            'primary_authority': 'Trichy City Corporation - Drainage Division',
            'secondary_authority': 'Private Drainage Contractor',
            'priority': 'High',
            'action': 'Clear storm water drains and install proper outlets before monsoon season'
        },
        {
            'keywords': ['no seating', 'no bench', 'nowhere to sit', 'no seat'],
            'sub_problem': 'No seating',
            'primary_authority': 'Trichy City Corporation - Works Division',
            'secondary_authority': 'TNSTC Trichy Division',
            'priority': 'Medium',
            'action': 'Install stainless steel benches with armrests and shade cover'
        },
        {
            'keywords': ['unsafe', 'dangerous', 'collapse', 'structural', 'crack in wall'],
            'sub_problem': 'Unsafe structure',
            'primary_authority': 'Trichy City Corporation - Engineering Wing',
            'secondary_authority': 'PWD (Public Works Dept)',
            'priority': 'High',
            'action': 'Conduct emergency structural safety audit and barricade danger zone immediately'
        },
        {
            'keywords': ['lighting', 'dark', 'no light', 'light not working', 'dim light', 'flickering'],
            'sub_problem': 'Lights not working',
            'primary_authority': 'Private Electrical Contractor (Trichy Corp.)',
            'secondary_authority': 'TANGEDCO (for power supply issues)',
            'priority': 'High',
            'action': 'Replace faulty LED fixtures within 24 hours per electrical maintenance SLA'
        }
    ],
    'audio_visual': [
        {
            'keywords': ['no announcement', 'no audio', 'announcement system'],
            'sub_problem': 'No announcement system',
            'primary_authority': 'TNSTC Trichy Division',
            'secondary_authority': 'Private IT/AV Vendor',
            'priority': 'High',
            'action': 'Install automated PA system with multi-language bus arrival announcements'
        },
        {
            'keywords': ['speaker not working', 'speaker broken', 'speaker damage', 'no sound'],
            'sub_problem': 'Speaker not working',
            'primary_authority': 'Private AV Maintenance Contractor',
            'secondary_authority': 'TNSTC Trichy Division',
            'priority': 'Medium',
            'action': 'Repair or replace PA system speakers and schedule weekly testing'
        },
        {
            'keywords': ['display board', 'led board', 'screen not working', 'display not working'],
            'sub_problem': 'Display board not working',
            'primary_authority': 'Private IT Vendor (LED Systems)',
            'secondary_authority': 'TNSTC Trichy Division',
            'priority': 'High',
            'action': 'Restore LED display board and update real-time route data feed via API'
        },
        {
            'keywords': ['wrong information', 'outdated', 'incorrect route', 'wrong timing'],
            'sub_problem': 'Wrong or outdated information',
            'primary_authority': 'TNSTC Trichy Division - IT Cell',
            'secondary_authority': 'Private IT Vendor',
            'priority': 'Medium',
            'action': 'Update route database and implement automated data verification checks'
        }
    ],
    'signage_braille': [
        {
            'keywords': ['no signboard', 'no sign', 'missing sign', 'no board'],
            'sub_problem': 'No signboards',
            'primary_authority': 'Trichy City Corporation - Works Division',
            'secondary_authority': 'Private Signage Contractor',
            'priority': 'High',
            'action': 'Install bilingual signboards (Tamil/English) at all entry/exit points'
        },
        {
            'keywords': ['faded', 'unreadable', 'worn out', 'cant read', 'old sign'],
            'sub_problem': 'Faded or unreadable boards',
            'primary_authority': 'Private Signage Contractor',
            'secondary_authority': 'Trichy City Corporation',
            'priority': 'Medium',
            'action': 'Replace worn signage with weather-resistant reflective boards within 15 days'
        },
        {
            'keywords': ['no braille', 'braille missing', 'blind', 'visually impaired'],
            'sub_problem': 'No Braille signage',
            'primary_authority': 'Trichy City Corporation - Accessibility Cell',
            'secondary_authority': 'Dept. for Welfare of Differently Abled',
            'priority': 'High',
            'action': 'Install Braille route maps and tactile indicators per RPWD Act 2016 mandate'
        },
        {
            'keywords': ['wrong direction', 'misleading', 'incorrect direction'],
            'sub_problem': 'Wrong directions',
            'primary_authority': 'TNSTC Trichy Division',
            'secondary_authority': 'Private Signage Contractor',
            'priority': 'Medium',
            'action': 'Audit and correct all directional signage with GPS-verified data'
        }
    ],
    'staff_assistance': [
        {
            'keywords': ['not helping', 'no help', 'refused', 'ignored', 'unhelpful'],
            'sub_problem': 'Staff not helping',
            'primary_authority': 'TNSTC Trichy Division - HR',
            'secondary_authority': 'Depot Manager',
            'priority': 'High',
            'action': 'Issue warning to staff and mandate passenger assistance training within 7 days'
        },
        {
            'keywords': ['rude', 'misbehaved', 'shouted', 'disrespect', 'abusive'],
            'sub_problem': 'Rude behavior',
            'primary_authority': 'TNSTC Trichy Division - HR',
            'secondary_authority': 'Transport Commissioner Office',
            'priority': 'High',
            'action': 'Initiate disciplinary action and mandate sensitivity/disability awareness training'
        },
        {
            'keywords': ['no assistance', 'disabled help', 'wheelchair help', 'no support'],
            'sub_problem': 'No assistance for disabled',
            'primary_authority': 'Depot Manager - TNSTC Trichy',
            'secondary_authority': 'Private Security/Help-desk Contractor',
            'priority': 'High',
            'action': 'Deploy dedicated accessibility assistant at help-desk during 6AM-10PM hours'
        }
    ],
    'ramp_wheelchair': [
        {
            'keywords': ['no ramp', 'ramp missing', 'missing ramp', 'ramp not available'],
            'sub_problem': 'No ramp installed',
            'primary_authority': 'Trichy City Corporation - Works Division',
            'secondary_authority': 'Private Civil Contractor',
            'priority': 'High',
            'action': 'Install 1:12 gradient ramp with anti-skid surface and dual handrails per IS 17802'
        },
        {
            'keywords': ['steep ramp', 'ramp too steep', 'slope', 'gradient'],
            'sub_problem': 'Ramp too steep',
            'primary_authority': 'Trichy City Corporation - Engineering Wing',
            'secondary_authority': 'PWD (Public Works Dept)',
            'priority': 'High',
            'action': 'Demolish and rebuild ramp to 1:12 slope ratio per IS 17802 standards'
        },
        {
            'keywords': ['narrow', 'width', 'too small', 'cannot pass'],
            'sub_problem': 'Pathway too narrow for wheelchair',
            'primary_authority': 'Trichy City Corporation - Works Division',
            'secondary_authority': 'Private Civil Contractor',
            'priority': 'High',
            'action': 'Widen pathway to minimum 1200mm and add TGSI strips on both edges'
        },
        {
            'keywords': ['no handrail', 'handrail missing', 'grab rail'],
            'sub_problem': 'No handrails',
            'primary_authority': 'Private Civil Contractor',
            'secondary_authority': 'Trichy City Corporation',
            'priority': 'Medium',
            'action': 'Install dual-height SS handrails (700mm & 900mm) on both sides within 10 days'
        }
    ]
}


# ===== RESPONSIBILITY ANALYSIS: CONTRACTOR vs CIVILIAN =====
RESPONSIBILITY_MAP = {
    # Toilet & Facilities
    'Toilet not clean': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Legally responsible for "Site Clearance" and daily sanitation per O&M contract. S.R. Vedhaah must maintain 3x/day cleaning schedule with documented logs.',
        'civilian_resp': 'Public misuse (throwing trash, spitting) accelerates deterioration. Trichy Corp. must install CCTV and impose fines for misuse.'
    },
    'No water supply': {
        'fault_by': 'Government',
        'contractor_resp': 'Private Plumbing Contractor must maintain pipelines and tank connections in working condition per SLA.',
        'civilian_resp': 'Wastage of water by public (leaving taps open) strains supply. Water-saving signage and auto-shutoff taps recommended.'
    },
    'Water not coming regularly': {
        'fault_by': 'Government',
        'contractor_resp': 'Municipality Water Supply Division responsible for scheduling and ensuring supply pressure.',
        'civilian_resp': 'N/A — supply timing is a government infrastructure issue, not civilian-caused.'
    },
    'Poor water quality': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Private Tank Maintenance Contractor failed to clean water tanks per quarterly schedule. Penalty applicable.',
        'civilian_resp': 'Contamination may occur from unauthorized connections or dumping near water source.'
    },
    'Water tank not cleaned': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Tank Maintenance Contractor violated contract KPI. Must clean tanks quarterly with documented water quality reports.',
        'civilian_resp': 'N/A — tank maintenance is purely a contractor obligation.'
    },
    'Broken flush or fittings': {
        'fault_by': 'Both',
        'contractor_resp': 'Plumbing Contractor must replace broken fittings within 48 hours per maintenance SLA. Failure = penalty deduction.',
        'civilian_resp': 'Vandalism and rough usage by public is a major cause. CCTV surveillance and vandal-proof fixtures recommended.'
    },
    'No soap or handwash': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Housekeeping Contractor must refill soap dispensers daily per contract checklist. Lapse = penalty.',
        'civilian_resp': 'Theft of soap/dispensers by public reported. Wall-mounted tamper-proof dispensers recommended.'
    },
    'Bad smell': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Cleaning Contractor not meeting frequency and quality standards. Must apply enzymatic deodorizer and increase cleaning shifts.',
        'civilian_resp': 'Public urination outside toilets and littering worsen the problem. Fencing and signage needed.'
    },
    'No disabled-friendly toilet': {
        'fault_by': 'Government',
        'contractor_resp': 'Civil Contractor must construct accessible toilet as per RPWD Act specs when work order is issued.',
        'civilian_resp': 'N/A — this is a planning and infrastructure gap, not civilian-caused.'
    },
    # Infrastructure & Safety
    'Broken pavement': {
        'fault_by': 'Both',
        'contractor_resp': 'Civil Contractor used sub-standard materials or failed to maintain. Warranty claim applicable if within defect liability period.',
        'civilian_resp': 'Heavy vehicle parking and unauthorized encroachment by vendors accelerate pavement damage.'
    },
    'Potholes near bus stop': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Road Contractor failed to maintain approach roads. Must fill potholes within 7 days per TNRSP norms.',
        'civilian_resp': 'Overloaded vehicles and rainwater seepage (drainage failure) contribute to pothole formation.'
    },
    'No shelter': {
        'fault_by': 'Government',
        'contractor_resp': 'Civil Contractor must construct shelter when tender is awarded. Delay = contract penalty.',
        'civilian_resp': 'N/A — shelter absence is a government planning/budget issue.'
    },
    'Waterlogging': {
        'fault_by': 'Both',
        'contractor_resp': 'Drainage Contractor failed to clear storm drains before monsoon season. Blockage = SLA violation.',
        'civilian_resp': 'Plastic waste and garbage dumping by public blocks drains. Waste segregation enforcement needed.'
    },
    'No seating': {
        'fault_by': 'Government',
        'contractor_resp': 'Furniture Contractor must install benches when work order is issued.',
        'civilian_resp': 'Vandalism and theft of seating by public reported at some locations. Anti-theft concrete benches recommended.'
    },
    'Unsafe structure': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Original Civil Contractor liable if within defect liability period. Structural failure = legal action.',
        'civilian_resp': 'Unauthorized modifications or overloading by vendors may weaken structure.'
    },
    'Lights not working': {
        'fault_by': 'Both',
        'contractor_resp': 'Private Electrical Contractor must replace faulty fixtures within 24 hours. TANGEDCO responsible for power supply.',
        'civilian_resp': 'Vandalism (stone-throwing, wire theft) is a major cause. Vandal-proof LED housings recommended.'
    },
    # Audio & Visual
    'No announcement system': {
        'fault_by': 'Government',
        'contractor_resp': 'IT/AV Vendor must install PA system when purchase order is issued by TNSTC.',
        'civilian_resp': 'N/A — absence of system is a government procurement/budget issue.'
    },
    'Speaker not working': {
        'fault_by': 'Both',
        'contractor_resp': 'AV Maintenance Contractor must repair speakers within 48 hours per AMC (Annual Maintenance Contract).',
        'civilian_resp': 'Tampering and theft of speaker wiring reported. Tamper-proof enclosures needed.'
    },
    'Display board not working': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Private IT Vendor failed to maintain LED display hardware/software. AMC penalty applicable.',
        'civilian_resp': 'Rare civilian involvement. Occasionally damaged by thrown objects.'
    },
    'Wrong or outdated information': {
        'fault_by': 'Government',
        'contractor_resp': 'TNSTC IT Cell and vendor must update route database. Automated sync recommended.',
        'civilian_resp': 'N/A — data accuracy is entirely an operational responsibility.'
    },
    # Signage & Braille
    'No signboards': {
        'fault_by': 'Government',
        'contractor_resp': 'Signage Contractor must fabricate and install when work order is issued.',
        'civilian_resp': 'N/A — absence is a government planning gap.'
    },
    'Faded or unreadable boards': {
        'fault_by': 'Both',
        'contractor_resp': 'Signage Contractor must replace faded signs under warranty/AMC. Weather-resistant materials required.',
        'civilian_resp': 'Defacement with posters, stickers, and graffiti by public accelerates deterioration.'
    },
    'No Braille signage': {
        'fault_by': 'Government',
        'contractor_resp': 'Accessibility Contractor must install Braille maps when mandated by RPWD compliance order.',
        'civilian_resp': 'N/A — Braille absence is a policy/compliance gap.'
    },
    'Wrong directions': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Signage Contractor installed incorrect information. Must audit and correct immediately.',
        'civilian_resp': 'Unauthorized sign relocation or tampering by public/vendors possible.'
    },
    # Staff & Assistance
    'Staff not helping': {
        'fault_by': 'Government',
        'contractor_resp': 'TNSTC HR must enforce passenger assistance protocols. Staff performance review needed.',
        'civilian_resp': 'N/A — staff behavior is entirely an employment/training issue.'
    },
    'Rude behavior': {
        'fault_by': 'Government',
        'contractor_resp': 'TNSTC HR must take disciplinary action. Mandatory sensitivity training required.',
        'civilian_resp': 'Verbal abuse from passengers may provoke staff. De-escalation training for both sides recommended.'
    },
    'No assistance for disabled': {
        'fault_by': 'Both',
        'contractor_resp': 'Depot Manager must assign accessibility assistants. Help-desk Contractor must staff reception.',
        'civilian_resp': 'Lack of public awareness about assisting disabled co-passengers. Community awareness campaigns needed.'
    },
    # Ramp & Wheelchair
    'No ramp installed': {
        'fault_by': 'Government',
        'contractor_resp': 'Civil Contractor must construct ramp when work order is issued per RPWD mandate.',
        'civilian_resp': 'N/A — ramp absence is a government infrastructure planning failure.'
    },
    'Ramp too steep': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Civil Contractor built ramp violating IS 17802 standards (1:12 slope). Must demolish and rebuild at contractor cost.',
        'civilian_resp': 'N/A — construction quality is entirely a contractor issue.'
    },
    'Pathway too narrow for wheelchair': {
        'fault_by': 'Both',
        'contractor_resp': 'Civil Contractor built pathway below minimum 1200mm width. Reconstruction required.',
        'civilian_resp': 'Encroachment by parked vehicles and vendors narrows accessible pathways. Enforcement needed.'
    },
    'No handrails': {
        'fault_by': 'Contractor',
        'contractor_resp': 'Civil Contractor omitted handrails from construction. Must install within 10 days at contractor cost.',
        'civilian_resp': 'Theft of metal handrails for scrap value reported at some locations. Welded/embedded fixtures recommended.'
    }
}


def classify_sub_problem(text, category):
    """
    Given a grievance text and its detected category, classify the specific
    sub-problem and return authority mapping, priority, suggested action,
    and responsibility analysis (contractor vs civilian fault).
    """
    text_lower = text.lower()
    rules = SUB_PROBLEM_RULES.get(category, [])
    
    best_match = None
    best_score = 0
    
    for rule in rules:
        score = 0
        for kw in rule['keywords']:
            if kw in text_lower:
                score += 1
        if score > best_score:
            best_score = score
            best_match = rule
    
    if best_match:
        sub = best_match['sub_problem']
        resp = RESPONSIBILITY_MAP.get(sub, {})
        return {
            'sub_problem': sub,
            'primary_authority': best_match['primary_authority'],
            'secondary_authority': best_match['secondary_authority'],
            'priority': best_match['priority'],
            'action': best_match['action'],
            'fault_by': resp.get('fault_by', 'Unknown'),
            'contractor_resp': resp.get('contractor_resp', ''),
            'civilian_resp': resp.get('civilian_resp', '')
        }
    
    # Fallback defaults per category (Trichy-specific)
    fallback = {
        'toilet_facilities': {'sub_problem': 'General toilet/facility issue', 'primary_authority': 'Private Cleaning Contractor (Trichy Corp.)', 'secondary_authority': 'Trichy City Corporation', 'priority': 'Medium', 'action': 'Conduct facility inspection and issue work order to maintenance contractor'},
        'infrastructure': {'sub_problem': 'General infrastructure issue', 'primary_authority': 'Trichy City Corporation - Engineering Wing', 'secondary_authority': 'Private Civil Contractor', 'priority': 'Medium', 'action': 'Schedule infrastructure assessment and issue repair tender'},
        'audio_visual': {'sub_problem': 'General audio/visual system issue', 'primary_authority': 'TNSTC Trichy Division', 'secondary_authority': 'Private IT/AV Vendor', 'priority': 'Medium', 'action': 'Inspect and restore audio/visual systems via vendor service agreement'},
        'signage_braille': {'sub_problem': 'General signage issue', 'primary_authority': 'Trichy City Corporation - Works Division', 'secondary_authority': 'Private Signage Contractor', 'priority': 'Medium', 'action': 'Audit and update all signage at the stop per accessibility standards'},
        'staff_assistance': {'sub_problem': 'General staff issue', 'primary_authority': 'TNSTC Trichy Division - HR', 'secondary_authority': 'Depot Manager', 'priority': 'Medium', 'action': 'Review staff performance and schedule disability awareness training'},
        'ramp_wheelchair': {'sub_problem': 'General accessibility barrier', 'primary_authority': 'Trichy City Corporation - Works Division', 'secondary_authority': 'Private Civil Contractor', 'priority': 'High', 'action': 'Conduct accessibility audit per RPWD Act 2016 guidelines'}
    }
    
    fb = fallback.get(category, {
        'sub_problem': 'Unclassified issue',
        'primary_authority': 'Transport Department',
        'secondary_authority': None,
        'priority': 'Medium',
        'action': 'Investigate and resolve the reported issue'
    })
    fb['fault_by'] = 'Unknown'
    fb['contractor_resp'] = 'Requires investigation to determine contractor obligation.'
    fb['civilian_resp'] = 'Requires investigation to determine if public misuse contributed.'
    return fb




def compute_tfidf(documents):
    """Compute TF-IDF scores for all documents"""
    n_docs = len(documents)
    
    # Document frequency
    df = Counter()
    doc_tokens = []
    
    for doc in documents:
        tokens = preprocess_text(doc)
        doc_tokens.append(tokens)
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df[token] += 1
    
    # TF-IDF per document
    tfidf_docs = []
    for tokens in doc_tokens:
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        tfidf = {}
        for token, count in tf.items():
            tf_score = count / total
            idf_score = math.log(n_docs / (df[token] + 1)) + 1
            tfidf[token] = round(tf_score * idf_score, 4)
        tfidf_docs.append(tfidf)
    
    return tfidf_docs


def compute_silhouette_score(grievances_with_clusters):
    """
    Compute a simplified silhouette score for the clustering.
    
    For each point: s(i) = (b(i) - a(i)) / max(a(i), b(i))
    a(i) = avg distance to points in same cluster
    b(i) = min avg distance to points in nearest other cluster
    
    We use keyword overlap as a distance metric.
    """
    if len(grievances_with_clusters) < 2:
        return 0.0
    
    # Group by cluster
    clusters = {}
    for g in grievances_with_clusters:
        cid = g['cluster']
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(set(preprocess_text(g['text'])))
    
    # Need at least 2 clusters
    active_clusters = {k: v for k, v in clusters.items() if len(v) > 0}
    if len(active_clusters) < 2:
        return 0.0
    
    def jaccard_distance(set1, set2):
        if not set1 and not set2:
            return 0
        union = set1 | set2
        if not union:
            return 0
        intersection = set1 & set2
        return 1 - len(intersection) / len(union)
    
    silhouette_scores = []
    
    for g in grievances_with_clusters:
        g_tokens = set(preprocess_text(g['text']))
        own_cluster = g['cluster']
        
        # a(i): average distance to own cluster members
        own_members = clusters.get(own_cluster, [])
        if len(own_members) <= 1:
            a_i = 0
        else:
            distances = [jaccard_distance(g_tokens, m) for m in own_members if m != g_tokens]
            a_i = sum(distances) / len(distances) if distances else 0
        
        # b(i): minimum average distance to other clusters
        b_i = float('inf')
        for cid, members in active_clusters.items():
            if cid == own_cluster:
                continue
            distances = [jaccard_distance(g_tokens, m) for m in members]
            avg_dist = sum(distances) / len(distances) if distances else float('inf')
            b_i = min(b_i, avg_dist)
        
        if b_i == float('inf'):
            b_i = 0
        
        # Silhouette score for this point
        max_ab = max(a_i, b_i)
        if max_ab == 0:
            s_i = 0
        else:
            s_i = (b_i - a_i) / max_ab
        
        silhouette_scores.append(s_i)
    
    # Average silhouette score
    avg_score = sum(silhouette_scores) / len(silhouette_scores)
    return round(avg_score, 4)


def cluster_grievances():
    """
    Main function: Load grievances, classify each into clusters,
    compute stats, and return results.
    """
    with open(os.path.join(DATA_DIR, 'grievances.json'), 'r') as f:
        grievances = json.load(f)
    
    # Classify each grievance
    classified = []
    for g in grievances:
        cluster_id, confidence, keywords = classify_grievance(g['text'])
        classified.append({
            'id': g['id'],
            'stop_id': g['stop_id'],
            'text': g['text'],
            'date': g['date'],
            'cluster': cluster_id,
            'cluster_label': CLUSTER_DEFINITIONS[cluster_id]['label'],
            'cluster_icon': CLUSTER_DEFINITIONS[cluster_id]['icon'],
            'cluster_color': CLUSTER_DEFINITIONS[cluster_id]['color'],
            'confidence': confidence,
            'matched_keywords': keywords
        })
    
    # Compute TF-IDF
    tfidf_scores = compute_tfidf([g['text'] for g in grievances])
    
    # Get top keywords per cluster
    cluster_keywords = {}
    for i, g in enumerate(classified):
        cid = g['cluster']
        if cid not in cluster_keywords:
            cluster_keywords[cid] = Counter()
        for word, score in tfidf_scores[i].items():
            cluster_keywords[cid][word] += score
    
    # Compute silhouette score
    silhouette = compute_silhouette_score(classified)
    
    # Build cluster summary
    cluster_summary = []
    for cluster_id, cluster_def in CLUSTER_DEFINITIONS.items():
        members = [g for g in classified if g['cluster'] == cluster_id]
        top_words = cluster_keywords.get(cluster_id, Counter()).most_common(10)
        
        cluster_summary.append({
            'id': cluster_id,
            'label': cluster_def['label'],
            'icon': cluster_def['icon'],
            'color': cluster_def['color'],
            'count': len(members),
            'percentage': round(len(members) / len(classified) * 100, 1) if classified else 0,
            'top_keywords': [{'word': w, 'score': round(s, 3)} for w, s in top_words],
            'sample_grievances': [m['text'][:120] + '...' if len(m['text']) > 120 else m['text'] for m in members[:3]]
        })
    
    # Sort by count descending
    cluster_summary.sort(key=lambda x: x['count'], reverse=True)
    
    # Grievances per stop
    stop_grievances = {}
    for g in classified:
        sid = g['stop_id']
        if sid not in stop_grievances:
            stop_grievances[sid] = []
        stop_grievances[sid].append(g)
    
    return {
        'total_grievances': len(classified),
        'silhouette_score': silhouette,
        'silhouette_quality': (
            'Excellent' if silhouette > 0.7 else
            'Good' if silhouette > 0.5 else
            'Fair' if silhouette > 0.25 else
            'Poor'
        ),
        'clusters': cluster_summary,
        'grievances': classified,
        'stop_grievances': stop_grievances
    }
