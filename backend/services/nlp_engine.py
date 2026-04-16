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
    # ──── Toilet & Facilities ────
    'Toilet not clean': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (S.R. Vedhaah) is legally responsible for "Site Clearance" under their O&M contract with Trichy City Corporation. This means removing all waste, sanitizing surfaces, and maintaining documented cleaning logs with 3x/day frequency. Most contracts for firms like S.R. Vedhaah include a "De-mobilization" clause where they must leave every shift with a clean, inspected site.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) is responsible for security and public behavior management. If the site is "dirty" because civilians are entering and misusing the facility — throwing trash, spitting pan masala, or not flushing — the Corporation must provide better surveillance (CCTV), impose fines under Municipal Bylaws, and install tamper-proof fixtures to reduce civilian-caused damage.'
    },
    'No water supply': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Private Plumbing Contractor) is responsible for maintaining all pipelines, valves, and overhead tank connections in working condition as per their Service Level Agreement (SLA). If supply fails due to pipeline blockage or pump failure within the premises, the plumbing contractor must restore it within 24 hours or face contractual penalties.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Water Supply Division) bears primary responsibility for ensuring municipal water supply reaches the bus stand. If civilians are wasting water — leaving taps running, washing clothes, or bathing at bus stand taps — the Corporation must install auto-shutoff sensor taps and water conservation signage to prevent public wastage.'
    },
    'Water not coming regularly': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor has limited responsibility here. Their duty is to maintain internal plumbing so that when water arrives, it flows properly. Any pump or motor failures within the bus stand premises fall under their SLA.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Water Supply Division) is solely responsible for scheduling water supply timings and maintaining adequate pressure. This is a government infrastructure issue — not caused by civilians. The Corporation must coordinate with TWAD Board to ensure reliable supply scheduling.'
    },
    'Poor water quality': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (Private Tank Maintenance Contractor) failed to perform quarterly tank cleaning and water quality testing as mandated in their contract. They are legally liable for any health issues arising from contaminated water. Contract terms typically require them to submit lab-tested water quality reports every 90 days to the Corporation.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Health Wing) must ensure no unauthorized connections or external contamination sources exist near the water storage. If civilians are dumping waste near overhead tanks or water sources, the Corporation must erect barriers and enforce penalties under the TN Public Health Act.'
    },
    'Water tank not cleaned': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (Tank Maintenance Contractor) has violated their Key Performance Indicator (KPI) obligation. Per the O&M agreement, water tanks must be cleaned, disinfected, and documented quarterly. Failure to comply triggers automatic penalty deductions from their monthly billing. The contractor must produce photographic evidence and lab reports of each cleaning cycle.',
        'civilian_resp': 'The Client/Owner has oversight responsibility. Tank cleaning is purely a contractual obligation of the maintenance contractor — civilians have no access to water tanks. However, the Corporation must audit contractor performance and not accept self-reported compliance without physical verification.'
    },
    'Broken flush or fittings': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (Private Plumbing Contractor) is contractually required to replace broken fittings — flush mechanisms, taps, lever handles, door locks — within 48 hours of a reported complaint. Their SLA includes "Preventive Maintenance" clauses requiring weekly inspection of all toilet fixtures. Failure to replace within the stipulated time incurs penalty deductions.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) acknowledges that civilian vandalism — forcing flush handles, breaking ceramic basins, stealing taps — is a major contributor. The Corporation must install vandal-proof stainless steel fixtures, deploy CCTV at toilet entrances, and engage VDoDay House Keeping for round-the-clock monitoring to deter misuse.'
    },
    'No soap or handwash': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (VDoDay House Keeping / S.R. Vedhaah) must refill all soap dispensers as part of their daily cleaning checklist. The O&M contract specifies "consumables supply" — soap, tissue, and cleaning agents — as contractor obligations. Empty dispensers constitute a direct contract violation subject to penalty.',
        'civilian_resp': 'The Client/Owner notes that theft of soap dispensers and liquid soap by the public has been documented at several bus stands. The Corporation must install wall-mounted, tamper-proof, lockable dispensers and use bulk liquid soap rather than bar soap to reduce theft incentive.'
    },
    'Bad smell': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (S.R. Vedhaah) is not meeting the contractual cleaning frequency and quality standards. Per their agreement, all toilet blocks must be cleaned with enzymatic deodorizers, and drain traps must be acid-washed weekly. Persistent odor indicates the contractor is skipping shifts or using diluted cleaning agents — both constitute SLA violations subject to penalty.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) must address civilian-caused odor sources: public urination on walls and outside toilet blocks, paan spitting, and littering of food waste. The Corporation must install physical barriers (fencing/walls), "No Urination" penalty signage with fine amounts displayed, and proper drainage to eliminate stagnant water.'
    },
    'No disabled-friendly toilet': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (M/s. Jyothi Constructions or equivalent Class-I Civil Contractor) is responsible for constructing the accessible toilet as per RPWD Act 2016 specifications once the Corporation issues a formal work order. Construction must include 900mm wide doors, grab bars, emergency pull cords, and wheelchair-turning space — all per IS 17802 standards.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) bears sole responsibility for this gap. The absence of a disabled-friendly toilet is a planning and budgetary failure by the government, not a civilian-caused issue. The Corporation must allocate funds under Smart City Mission or AMRUT scheme and issue construction tenders immediately.'
    },
    # ──── Infrastructure & Safety ────
    'Broken pavement': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (Tamil Builders / M/s. Jyothi Constructions) is liable if the pavement failure is due to sub-standard materials, inadequate base preparation, or workmanship defects within the "Defect Liability Period" (typically 12-24 months post-construction). The contractor must repair at their own cost during this period, using anti-skid interlocking tiles per Corporation standards.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) must control civilian-caused damage: heavy vehicle (auto/truck) parking on pedestrian pavements, unauthorized vendor encroachments placing heavy loads, and tree root damage. The Corporation must install bollards to prevent vehicle entry and enforce anti-encroachment drives regularly.'
    },
    'Potholes near bus stop': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (L&T for major roads / Tamil Builders for internal roads) is contractually bound to fill potholes within 7 working days of reporting under TNRSP (Tamil Nadu Road Sector Project) norms. For National Highways near bus stops, NHAI-appointed contractors are responsible. Failure to repair within the stipulated timeframe triggers penalty clauses and may result in contract termination.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Roads Division / Highways Department) must address root causes: poor drainage causing water seepage that erodes road base, overloaded commercial vehicles exceeding axle-load limits, and unauthorized utility trenching by cable/pipe laying agencies. Weight enforcement checkpoints and proper drain outlets are the Corporation\'s responsibility.'
    },
    'No shelter': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Sri Venket Lakshmi Associates / equivalent building contractor) will construct the shelter once a tender is awarded. Pre-fabricated bus shelters can be installed within 15-20 working days. Delay beyond the contracted timeline triggers daily penalty as per contract terms.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation / TNSTC Trichy Division) bears full responsibility. Shelter absence is a government planning and budgetary gap — not civilian-caused. The Corporation must allocate funds under Smart City Mission or AMRUT scheme and prioritize high-footfall stops.'
    },
    'Waterlogging': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (L&T for underground drainage / Private Drainage Contractor for surface drains) failed to clear storm water drains before the monsoon season. This is an SLA violation. Contracts mandate pre-monsoon drain clearing by September every year, with photographic documentation submitted to the Corporation.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Drainage Division) must address civilian-caused blockages: plastic bags, food waste, and construction debris dumped into drains by residents and vendors. The Corporation must enforce solid waste segregation, install drain-mouth gratings to prevent debris entry, and conduct weekly "Mega Cleaning Drives".'
    },
    'No seating': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Tamil Builders / furniture supplier) must manufacture and install stainless steel benches with armrests once a purchase order is issued. Standard municipal benches must be bolted into concrete foundations to prevent theft.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) notes that vandalism and theft of metal seating for scrap value is documented at several bus stops. If seating disappears due to civilian theft, the Corporation must file FIR, install anti-theft concrete benches (which cannot be sold as scrap), and use CCTV surveillance.'
    },
    'Unsafe structure': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (original Civil Contractor — M/s. Jyothi Constructions or equivalent) is legally liable if the structural failure occurs within the Defect Liability Period. Under the Indian Contract Act and PWD guidelines, structural failures due to sub-standard concrete, inadequate reinforcement, or poor foundation work constitute criminal negligence. The contractor faces legal action and must bear all repair costs.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Engineering Wing) must ensure no unauthorized structural modifications. If vendors or unauthorized occupants have added weight (illegal constructions on rooftops, heavy signboards) or drilled into load-bearing walls, the Corporation must conduct immediate evacuation, engage a structural auditor, and remove all unauthorized additions.'
    },
    'Lights not working': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (Private Electrical Contractor engaged by Trichy Corporation) must replace faulty LED fixtures, wiring, and MCBs within 24 hours of a complaint. TANGEDCO is responsible if the failure is due to power supply issues (transformer failure, cable fault). The electrical contractor\'s AMC covers all internal fixtures; TANGEDCO covers the power feed.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) acknowledges that civilian vandalism — stone-throwing at lights, copper wire theft, and unauthorized electricity tapping — is a major cause of lighting failures. The Corporation must install vandal-proof polycarbonate housings, underground armored cables, and CCTV at transformer locations to prevent theft.'
    },
    # ──── Audio & Visual ────
    'No announcement system': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Private IT/AV Vendor) must install the PA system once TNSTC Trichy Division issues a purchase order. Installation includes speakers, amplifiers, microphones, and automated announcement software with multi-language support (Tamil/English/Hindi).',
        'civilian_resp': 'The Client/Owner (TNSTC Trichy Division) bears full responsibility. Absence of an announcement system is a government procurement and budgetary gap. TNSTC must allocate funds and issue tenders. Civilians have no role in system procurement.'
    },
    'Speaker not working': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (Vision Care Services Pvt Ltd or AV Maintenance Vendor) is bound by their Annual Maintenance Contract (AMC) to repair all PA system faults within 48 hours. The AMC covers speaker replacement, amplifier repairs, and wiring restoration. Failure to respond within the SLA window triggers penalty deductions.',
        'civilian_resp': 'The Client/Owner (TNSTC Trichy Division) notes that speaker wire theft (for copper scrap value) and physical tampering with speaker housings by unauthorized persons is documented. TNSTC must install tamper-proof speaker enclosures, use conduit-protected wiring, and deploy CCTV near PA system equipment.'
    },
    'Display board not working': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (Private IT Vendor handling LED display systems) failed to maintain the hardware and software per their AMC. LED display boards require regular firmware updates, data feed connectivity checks, and panel replacements. The IT vendor is solely responsible for technical uptime and data accuracy. AMC penalty is applicable for downtime exceeding 24 hours.',
        'civilian_resp': 'The Client/Owner (TNSTC Trichy Division) notes rare civilian involvement. Occasional damage from thrown objects or vandalism is possible. TNSTC must install protective glass screens over LED boards and mount them at heights inaccessible to the public.'
    },
    'Wrong or outdated information': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Private IT Vendor + TNSTC IT Cell) must jointly maintain accurate route databases. The IT vendor is responsible for the software platform; TNSTC IT Cell must provide updated route, timing, and fare data. Automated data sync should be implemented to eliminate manual errors.',
        'civilian_resp': 'The Client/Owner (TNSTC Trichy Division) bears full responsibility. Data accuracy is an operational issue — civilians have no role in route database management. TNSTC must implement automated GPS-based bus tracking to provide real-time, accurate information.'
    },
    # ──── Signage & Braille ────
    'No signboards': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Tamil Builders / Private Signage Contractor) must fabricate and install bilingual signboards (Tamil/English) once the Corporation issues a work order. Signboards must use reflective, weather-resistant materials per IRC (Indian Road Congress) standards.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Works Division) bears sole responsibility. Absence of signboards is a government planning gap. Civilians cannot be blamed for infrastructure the government has not yet installed.'
    },
    'Faded or unreadable boards': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (Private Signage Contractor) must replace faded signs under their warranty period or AMC. Original signage contracts typically include a 3-5 year warranty against fading, peeling, and material degradation. If the signs faded within warranty, the contractor must replace them at zero additional cost.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) acknowledges that defacement by the public — pasting political posters, commercial advertisements, stickers, and spray-painting graffiti over directional signs — is a major cause of unreadability. The Corporation must enforce the TN Prevention of Defacement of Property Act, impose fines, and use anti-graffiti coatings on signboards.'
    },
    'No Braille signage': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Accessibility/Signage Contractor) must install Braille tactile route maps, tactile ground surface indicators (TGSI), and raised-letter signage when mandated by the RPWD compliance order. Specifications must follow IS 17802 and the Harmonised Guidelines issued by the Ministry of Urban Development.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Accessibility Cell / Dept. for Welfare of Differently Abled) bears sole responsibility. Braille absence is a policy and RPWD Act 2016 compliance failure by the government. Civilians have no role in accessibility infrastructure provision.'
    },
    'Wrong directions': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (Private Signage Contractor) installed incorrect directional information. This is a fabrication error or installation mistake. The contractor must audit all directional signage, verify against GPS coordinates and current bus routes, and correct all errors within 15 working days at their own cost.',
        'civilian_resp': 'The Client/Owner (TNSTC Trichy Division) must verify that no unauthorized sign relocation has occurred. Vendors or unauthorized persons sometimes move or rotate directional signs to benefit their shops. TNSTC must physically bolt signs into permanent positions and use tamper-evident fasteners.'
    },
    # ──── Staff & Assistance ────
    'Staff not helping': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor/Employer (TNSTC Trichy Division - HR Department) is the employer of record. Staff assistance is a core employment duty defined in TNSTC\'s Staff Conduct Rules. HR must enforce passenger assistance protocols through regular performance reviews, mystery audits, and mandatory training programs. Staff found violating assistance protocols face written warnings, salary deductions, and transfer to remote depots.',
        'civilian_resp': 'The Client/Owner (TNSTC Management) acknowledges this is entirely an employment and training issue. Civilians are the complainants, not the cause. However, TNSTC should also establish a visible complaint mechanism (QR-code feedback boards, toll-free helpline) so passengers can report unhelpful staff in real-time.'
    },
    'Rude behavior': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor/Employer (TNSTC Trichy Division - HR) must take immediate disciplinary action per TNSTC Service Rules. Rude behavior toward passengers — especially disabled, elderly, and women passengers — constitutes misconduct under State Transport Corporation employee regulations. Mandatory sensitivity training and disability awareness workshops must be conducted quarterly. Repeat offenders face suspension.',
        'civilian_resp': 'The Client/Owner (TNSTC / Transport Commissioner Office) notes that verbal abuse from passengers toward staff can sometimes provoke rude responses. Both parties need de-escalation. However, as public servants, staff are held to a higher standard of conduct. TNSTC must install audio recording at counters and conflict resolution protocols.'
    },
    'No assistance for disabled': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (First Choice Outsourcing Services / SPM HR Solutions — Help-desk staffing agencies) must deploy trained accessibility assistants at help-desk counters during 6AM-10PM operating hours. The staffing contract specifies "Disability Assistance" as a key deliverable. The Depot Manager (TNSTC) must ensure coverage at peak hours.',
        'civilian_resp': 'The Client/Owner (TNSTC / Trichy City Corporation) must also raise public awareness. Lack of "Good Samaritan" culture among fellow passengers means disabled travelers often wait without help. The Corporation must run awareness campaigns, install "Please Help" call buttons at platforms, and train ticket counter staff in basic sign language.'
    },
    # ──── Ramp & Wheelchair ────
    'No ramp installed': {
        'fault_by': 'Government',
        'contractor_resp': 'The Contractor (Sri Venket Lakshmi Associates / M/s. Jyothi Constructions) must construct a 1:12 gradient ramp with anti-skid surface, dual handrails, and tactile edge indicators once the Corporation issues a formal work order per RPWD Act 2016 Section 40-46. Construction must comply with IS 17802 and NBC 2016 accessibility provisions.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Works Division) bears sole responsibility. Ramp absence is a government infrastructure planning failure, not a civilian-caused issue. The Corporation must conduct an accessibility audit of all 30 bus stops, identify gaps, allocate budget under AMRUT/Smart City Mission, and issue construction tenders within 90 days.'
    },
    'Ramp too steep': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (original Civil Contractor) built the ramp in violation of IS 17802 standards, which mandate a maximum slope of 1:12 (8.33%). This is a construction quality failure. The contractor must demolish the non-compliant ramp and rebuild it to specification entirely at their own cost within the Defect Liability Period. If the DLP has expired, the Corporation must issue a fresh tender.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation - Engineering Wing) must ensure quality inspection. This is not a civilian-caused issue — it is a construction supervision failure. The Corporation\'s Junior Engineer should have rejected the ramp during the "Measurement Book" inspection stage. Quality audit protocols must be strengthened.'
    },
    'Pathway too narrow for wheelchair': {
        'fault_by': 'Both',
        'contractor_resp': 'The Contractor (Tamil Builders / Private Civil Contractor) built the pathway below the minimum 1200mm width required for wheelchair passage per IS 17802. This is a specifications violation. The contractor must widen the pathway, add TGSI (Tactile Ground Surface Indicator) strips on both edges, and ensure 1500mm turning space at corners — all at contractor cost if within DLP.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) must address encroachment. Even if the pathway was built to specification, unauthorized parking of two-wheelers, vendor carts, and display boards by civilians often narrows the accessible route. The Corporation must install fixed bollards, conduct daily anti-encroachment drives, and impose fines on violators under Municipal Corporation bylaws.'
    },
    'No handrails': {
        'fault_by': 'Contractor',
        'contractor_resp': 'The Contractor (Sri Venket Lakshmi Associates / Private Civil Contractor) omitted handrails from the ramp/stairway construction, violating the approved Building Plan and IS 17802 specifications. Dual-height stainless steel handrails (700mm and 900mm) on both sides are mandatory per RPWD Act. The contractor must install them within 10 working days at their own cost.',
        'civilian_resp': 'The Client/Owner (Trichy City Corporation) notes that theft of metal handrails for scrap value has been documented at multiple locations across Tamil Nadu. If handrails were installed but subsequently stolen, the Corporation must file an FIR, replace with welded/embedded (non-removable) SS handrails, and install anti-theft surveillance.'
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
