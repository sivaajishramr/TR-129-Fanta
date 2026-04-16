"""
AI Chat Engine — Natural Language Accessibility Assistant
Answers questions about bus stop accessibility using real data from the scoring engine.
"""
import re
from difflib import SequenceMatcher
from services.scoring_engine import load_stops, load_checklist, load_grievances, calculate_gap_score


# Feature display names
FEATURE_NAMES = {
    'ramp': 'Wheelchair Ramp',
    'tactile_path': 'Tactile Path (for visually impaired)',
    'audio_signal': 'Audio Announcement System',
    'wheelchair_space': 'Wheelchair Waiting Space',
    'braille_signage': 'Braille Signage',
    'elevator': 'Elevator / Lift',
    'accessible_toilet': 'Accessible Toilet',
    'staff_assistance': 'Staff Assistance Available'
}

# Intent patterns
INTENT_PATTERNS = {
    'accessibility_check': [
        r'accessible', r'wheelchair', r'disability', r'disabled', r'blind',
        r'visually impaired', r'ramp', r'braille', r'tactile', r'elevator',
        r'lift', r'toilet', r'audio', r'staff', r'help'
    ],
    'grievance_info': [
        r'complaint', r'grievance', r'problem', r'issue', r'report',
        r'broken', r'damaged', r'missing', r'not working', r'dirty'
    ],
    'comparison': [
        r'compare', r'better', r'worse', r'best', r'worst', r'safest',
        r'most accessible', r'least accessible', r'rank', r'top'
    ],
    'general_stats': [
        r'how many', r'total', r'average', r'overall', r'city',
        r'trichy', r'summary', r'statistics', r'stats', r'coverage'
    ],
    'recommendation': [
        r'recommend', r'suggest', r'should i', r'which stop', r'where',
        r'nearest', r'closest', r'safe', r'good stop'
    ],
    'greeting': [
        r'^hi$', r'^hello', r'^hey', r'good morning', r'good evening',
        r'namaste', r'vanakkam'
    ],
    'feature_specific': [
        r'ramp', r'braille', r'tactile', r'elevator', r'lift',
        r'toilet', r'audio', r'staff', r'wheelchair space'
    ]
}


def find_stop_in_query(query, stops):
    """Find which bus stop the user is asking about using fuzzy matching"""
    query_lower = query.lower()
    
    best_match = None
    best_score = 0
    
    for stop in stops:
        name_lower = stop['name'].lower()
        
        # Direct substring match (highest priority)
        if name_lower in query_lower or query_lower in name_lower:
            return stop
        
        # Try matching key parts of stop name
        name_parts = re.split(r'[\s\(\)\-,]+', name_lower)
        significant_parts = [p for p in name_parts if len(p) > 3 and p not in ('bus', 'stand', 'stop', 'station', 'railway')]
        
        for part in significant_parts:
            if part in query_lower:
                score = len(part) / len(name_lower)
                if score > best_score:
                    best_score = score
                    best_match = stop
        
        # Fuzzy match
        ratio = SequenceMatcher(None, name_lower, query_lower).ratio()
        if ratio > 0.5 and ratio > best_score:
            best_score = ratio
            best_match = stop
    
    return best_match if best_score > 0.25 else None


def detect_intent(query):
    """Detect the user's intent from their query"""
    query_lower = query.lower()
    scores = {}
    
    for intent, patterns in INTENT_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, query_lower))
        if score > 0:
            scores[intent] = score
    
    if not scores:
        return 'general'
    
    return max(scores, key=scores.get)


def get_accessibility_response(stop, score_data, grievances):
    """Generate detailed accessibility response for a stop"""
    gap = score_data['gap_score']
    missing = score_data['missing_features']
    present = score_data['present_features']
    
    # Count grievances for this stop
    stop_grievances = [g for g in grievances if g['stop_id'] == stop['id']]
    
    # Determine status emoji/label
    if gap > 70:
        status = "🔴 Critical"
        verdict = "This stop has significant accessibility gaps and needs urgent attention."
    elif gap > 40:
        status = "🟡 Warning"
        verdict = "This stop has moderate accessibility but several features are missing."
    else:
        status = "🟢 Good"
        verdict = "This stop meets most accessibility standards."
    
    # Build response
    lines = []
    lines.append(f"**{stop['name']}** — {status}")
    lines.append(f"")
    lines.append(f"📊 **Gap Score:** {gap}% | 👥 **Daily Footfall:** {stop.get('daily_footfall', 'N/A'):,}")
    lines.append(f"")
    
    # Present features
    if present:
        lines.append(f"✅ **Available Features ({len(present)}):**")
        for f in present:
            lines.append(f"  • {f['name']}")
    
    lines.append(f"")
    
    # Missing features
    if missing:
        lines.append(f"❌ **Missing Features ({len(missing)}):**")
        for f in missing:
            lines.append(f"  • {f['name']}")
    
    lines.append(f"")
    lines.append(f"📋 **Grievances Filed:** {len(stop_grievances)}")
    lines.append(f"")
    lines.append(f"💬 {verdict}")
    
    return '\n'.join(lines)


def get_feature_response(query, stops, checklist, grievances):
    """Answer questions about a specific accessibility feature across stops"""
    query_lower = query.lower()
    
    # Detect which feature
    feature_key = None
    for key, name in FEATURE_NAMES.items():
        if key.replace('_', ' ') in query_lower or name.lower() in query_lower:
            feature_key = key
            break
    
    if not feature_key:
        # Try partial matching
        if 'ramp' in query_lower:
            feature_key = 'ramp'
        elif 'braille' in query_lower:
            feature_key = 'braille_signage'
        elif 'tactile' in query_lower:
            feature_key = 'tactile_path'
        elif 'elevator' in query_lower or 'lift' in query_lower:
            feature_key = 'elevator'
        elif 'toilet' in query_lower or 'restroom' in query_lower:
            feature_key = 'accessible_toilet'
        elif 'audio' in query_lower or 'announcement' in query_lower:
            feature_key = 'audio_signal'
        elif 'staff' in query_lower:
            feature_key = 'staff_assistance'
        elif 'wheelchair' in query_lower and 'space' in query_lower:
            feature_key = 'wheelchair_space'
    
    if not feature_key:
        return None
    
    feature_name = FEATURE_NAMES[feature_key]
    has_it = [s for s in stops if s['features'].get(feature_key, False)]
    missing_it = [s for s in stops if not s['features'].get(feature_key, False)]
    
    lines = []
    lines.append(f"**{feature_name}** — City-wide Analysis")
    lines.append(f"")
    lines.append(f"📊 **{len(has_it)}** out of **{len(stops)}** stops have this feature ({round(len(has_it)/len(stops)*100)}%)")
    lines.append(f"")
    
    if has_it:
        lines.append(f"✅ **Stops WITH {feature_name}** ({len(has_it)}):")
        for s in has_it[:8]:
            lines.append(f"  • {s['name']}")
        if len(has_it) > 8:
            lines.append(f"  _(... and {len(has_it)-8} more)_")
    
    lines.append(f"")
    
    if missing_it:
        lines.append(f"❌ **Stops WITHOUT {feature_name}** ({len(missing_it)}):")
        for s in missing_it[:5]:
            lines.append(f"  • {s['name']}")
        if len(missing_it) > 5:
            lines.append(f"  _(... and {len(missing_it)-5} more)_")
    
    return '\n'.join(lines)


def get_comparison_response(stops, checklist, grievances):
    """Compare stops and find best/worst"""
    scored = []
    for stop in stops:
        sd = calculate_gap_score(stop, checklist)
        scored.append({'stop': stop, 'gap': sd['gap_score'], 'missing': sd['missing_count']})
    
    scored.sort(key=lambda x: x['gap'])
    
    best_5 = scored[:5]
    worst_5 = scored[-5:][::-1]
    
    lines = []
    lines.append(f"**🏆 Top 5 Most Accessible Stops:**")
    for i, s in enumerate(best_5, 1):
        emoji = '🥇🥈🥉4️⃣5️⃣'[i-1] if i <= 3 else f'{i}.'
        lines.append(f"  {emoji} **{s['stop']['name']}** — Gap: {s['gap']}%")
    
    lines.append(f"")
    lines.append(f"**🚨 Top 5 Least Accessible Stops:**")
    for i, s in enumerate(worst_5, 1):
        lines.append(f"  {i}. **{s['stop']['name']}** — Gap: {s['gap']}% ({s['missing']} features missing)")
    
    return '\n'.join(lines)


def get_stats_response(stops, checklist, grievances):
    """Return city-wide statistics"""
    total = len(stops)
    total_g = len(grievances)
    
    critical = 0
    warning = 0
    good = 0
    total_gap = 0
    
    for stop in stops:
        sd = calculate_gap_score(stop, checklist)
        total_gap += sd['gap_score']
        if sd['gap_score'] > 70:
            critical += 1
        elif sd['gap_score'] > 40:
            warning += 1
        else:
            good += 1
    
    avg_gap = round(total_gap / total, 1) if total > 0 else 0
    
    lines = []
    lines.append(f"**🏙️ Trichy Public Transport Accessibility — At a Glance**")
    lines.append(f"")
    lines.append(f"📍 **Total Stops Analyzed:** {total}")
    lines.append(f"📋 **Total Grievances:** {total_g}")
    lines.append(f"📊 **Average Gap Score:** {avg_gap}%")
    lines.append(f"")
    lines.append(f"🔴 **Critical Stops:** {critical} ({round(critical/total*100)}%)")
    lines.append(f"🟡 **Warning Stops:** {warning} ({round(warning/total*100)}%)")
    lines.append(f"🟢 **Good Stops:** {good} ({round(good/total*100)}%)")
    lines.append(f"")
    
    # Feature coverage
    features_coverage = {}
    for key in FEATURE_NAMES:
        count = sum(1 for s in stops if s['features'].get(key, False))
        features_coverage[key] = count
    
    lines.append(f"**♿ Feature Coverage Across All Stops:**")
    for key, name in FEATURE_NAMES.items():
        count = features_coverage[key]
        pct = round(count/total*100)
        bar = '█' * (pct // 10) + '░' * (10 - pct // 10)
        lines.append(f"  {bar} **{pct}%** — {name}")
    
    return '\n'.join(lines)


def get_greeting_response():
    """Return a friendly greeting"""
    return (
        "**👋 Hello! I'm AccessAudit AI Assistant**\n\n"
        "I can help you with:\n"
        "• 🔍 Check accessibility of any bus stop\n"
        "• ♿ Find stops with specific features (ramps, braille, etc.)\n"
        "• 🏆 Compare stops — best & worst accessibility\n"
        "• 📊 City-wide accessibility statistics\n"
        "• 📋 Grievance information for any stop\n\n"
        "**Try asking:** _\"Is Chatram Bus Stand wheelchair accessible?\"_"
    )


def process_chat(query):
    """Main chat processing function — takes a user query, returns an AI response"""
    if not query or not query.strip():
        return get_greeting_response()
    
    query = query.strip()
    
    # Load data
    stops = load_stops()
    checklist = load_checklist()
    grievances = load_grievances()
    
    # Detect intent
    intent = detect_intent(query)
    
    # Handle greeting
    if intent == 'greeting':
        return get_greeting_response()
    
    # Handle general stats
    if intent == 'general_stats':
        return get_stats_response(stops, checklist, grievances)
    
    # Handle comparison
    if intent == 'comparison':
        return get_comparison_response(stops, checklist, grievances)
    
    # Handle feature-specific questions (city-wide)
    stop = find_stop_in_query(query, stops)
    
    if intent == 'feature_specific' and not stop:
        resp = get_feature_response(query, stops, checklist, grievances)
        if resp:
            return resp
    
    # Handle recommendation
    if intent == 'recommendation':
        resp = get_comparison_response(stops, checklist, grievances)
        return "**♿ Recommended Most Accessible Stops in Trichy:**\n\n" + resp
    
    # Stop-specific queries
    if stop:
        score_data = calculate_gap_score(stop, checklist)
        
        # Feature-specific for a stop
        if intent == 'feature_specific':
            feature_resp = get_feature_response(query, stops, checklist, grievances)
            stop_resp = get_accessibility_response(stop, score_data, grievances)
            if feature_resp:
                feature_key = None
                for key in FEATURE_NAMES:
                    if key.replace('_', ' ') in query.lower() or key in query.lower():
                        feature_key = key
                        break
                if feature_key:
                    has = stop['features'].get(feature_key, False)
                    fname = FEATURE_NAMES[feature_key]
                    if has:
                        return f"✅ **Yes!** {stop['name']} **has** {fname}.\n\n" + stop_resp
                    else:
                        return f"❌ **No.** {stop['name']} does **not have** {fname}.\n\n" + stop_resp
            return stop_resp
        
        # Default: full accessibility report
        return get_accessibility_response(stop, score_data, grievances)
    
    # Fallback — try to be helpful
    return (
        "🤔 I'm not sure I understood that. Here are some things you can ask me:\n\n"
        "• **\"Is Chatram Bus Stand wheelchair accessible?\"**\n"
        "• **\"Which stops have braille signage?\"**\n"
        "• **\"What are the worst stops in Trichy?\"**\n"
        "• **\"Show me city statistics\"**\n"
        "• **\"Does Srirangam have a ramp?\"**\n\n"
        "_Try mentioning a specific bus stop name for detailed info!_"
    )
