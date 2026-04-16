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
