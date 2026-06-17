from config import PERSONA_WEIGHTS
from pipeline.honeypot import is_honeypot
from pipeline.coarse_filter import is_coarse_match
from pipeline.scorers.technical import calculate_technical_score
from pipeline.scorers.hiring_manager import calculate_hiring_manager_score
from pipeline.scorers.culture_fit import calculate_culture_fit_score
from pipeline.scorers.recruiter_ops import calculate_recruiter_ops_score
from pipeline.scorers.logistics_education import calculate_logistics_education_score
from pipeline.modifiers.semantic_similarity import apply_semantic_similarity
from pipeline.modifiers.hard_disqualifiers import get_hard_disqualifier_multiplier
from pipeline.jd_parser import JDParser

import json
import re

def extract_jd_metadata(jd_text):
    metadata = {
        "title": "Senior AI Engineer",
        "role": "Series A Founding AI/ML Lead",
        "skills": "LLMs, RAG, PyTorch, Vector DBs, Embedding Search",
        "disqualifiers": "Pure Consulting, Title-Chasers, Academic-only CVs"
    }
    
    if not jd_text:
        return metadata
        
    lines = [line.strip() for line in jd_text.split("\n") if line.strip()]
    
    for line in lines:
        if line.lower().startswith("job title:") or line.lower().startswith("job description:"):
            title_part = line.split(":", 1)[1].strip()
            if "\u2014" in title_part:
                title_part = title_part.split("\u2014", 1)[0].strip()
            metadata["title"] = title_part
            break
            
    for line in lines:
        if line.lower().startswith("company:"):
            comp_part = line.split(":", 1)[1].strip()
            if "(" in comp_part:
                comp_part = comp_part.split("(", 1)[0].strip()
            metadata["role"] = f"Hiring at {comp_part}"
            break
            
    skills_found = []
    vocab = [
        "Ray", "Triton", "CUDA", "PyTorch", "TensorFlow", "FAISS", "Milvus", "Qdrant",
        "SQL", "Spark", "Airflow", "dbt", "Snowflake", "BigQuery", "LLMs", "RAG",
        "Transformers", "LangChain", "PEFT", "LoRA", "Python"
    ]
    for word in vocab:
        if re.search(r'\b' + re.escape(word) + r'\b', jd_text, re.IGNORECASE):
            skills_found.append(word)
            
    if skills_found:
        metadata["skills"] = ", ".join(skills_found[:6])
        
    disq_found = []
    if "consulting" in jd_text.lower() or "tcs" in jd_text.lower():
        disq_found.append("Pure Consulting")
    if "title-chasers" in jd_text.lower() or "job hopping" in jd_text.lower() or "hopping" in jd_text.lower():
        disq_found.append("Title-Chasers")
    if "research" in jd_text.lower() or "academic" in jd_text.lower():
        disq_found.append("Academic-only CVs")
        
    if disq_found:
        metadata["disqualifiers"] = ", ".join(disq_found)
        
    return metadata

def apply_diversity_reranking(candidates, top_n=150):
    """
    Prevent clustering of near-identical candidates in the top 100.
    If multiple candidates share the same company+title combo, apply
    diminishing returns after the 3rd occurrence.
    """
    # Track company+title combos seen
    combo_counts = {}
    
    for c in candidates[:top_n]:
        profile = c.get('profile', {})
        company = str(profile.get('current_company', '')).lower().strip()
        title = str(profile.get('current_title', '')).lower().strip()
        combo = f"{company}|{title}"
        
        combo_counts[combo] = combo_counts.get(combo, 0) + 1
        count = combo_counts[combo]
        
        if count > 3:
            # Diminishing returns: 5% penalty per duplicate beyond 3rd
            penalty = 1.0 - min((count - 3) * 0.05, 0.40)
            c['final_score'] = round(c['final_score'] * penalty, 4)
            c['diversity_penalty'] = True
    
    return candidates

def rank_candidates(candidates_generator, jd_text):
    """
    Core pipeline coordinator. Runs ingestion, honeypot filters, coarse filters,
    calculates persona scores, computes semantic similarity boosts, sorts and ranks candidates.
    Returns the top 100 ranked candidates and pipeline statistics.
    """
    try:
        metadata = extract_jd_metadata(jd_text)
        with open("active_jd_metadata.json", "w", encoding="utf-8") as fmeta:
            json.dump(metadata, fmeta, indent=2)
    except Exception:
        pass
    scored_candidates = []
    honeypot_details = []
    stuffer_details = []
    
    stats = {
        'total_scanned': 0,
        'honeypots_blocked': 0,
        'stuffers_filtered': 0
    }
    
    for candidate in candidates_generator:
        stats['total_scanned'] += 1
        profile = candidate.get('profile', {})
        
        # 1. Honeypot check
        if is_honeypot(candidate):
            stats['honeypots_blocked'] += 1
            honeypot_details.append({
                'id': candidate.get('candidate_id', ''),
                'name': profile.get('anonymized_name', 'Anonymous'),
                'title': profile.get('current_title', ''),
                'yoe': profile.get('years_of_experience', 0)
            })
            continue
            
        # 2. Coarse Heuristics Filter
        if not is_coarse_match(candidate):
            stats['stuffers_filtered'] += 1
            stuffer_details.append({
                'id': candidate.get('candidate_id', ''),
                'name': profile.get('anonymized_name', 'Anonymous'),
                'title': profile.get('current_title', ''),
                'yoe': profile.get('years_of_experience', 0),
                'skills': [s.get('name', '') for s in candidate.get('skills', [])[:3]]
            })
            continue
            
        # 3. Calculate Individual Persona Scores
        tech = calculate_technical_score(candidate)
        hiring_manager = calculate_hiring_manager_score(candidate)
        culture_fit = calculate_culture_fit_score(candidate)
        recruiter_ops = calculate_recruiter_ops_score(candidate)
        logistics_edu = calculate_logistics_education_score(candidate)
        
        # Weighted Persona Sum
        persona_sum = (
            tech * PERSONA_WEIGHTS['technical'] +
            hiring_manager * PERSONA_WEIGHTS['hiring_manager'] +
            culture_fit * PERSONA_WEIGHTS['culture_fit'] +
            recruiter_ops * PERSONA_WEIGHTS['recruiter_ops'] +
            logistics_edu * (PERSONA_WEIGHTS['logistics'] + PERSONA_WEIGHTS['education'])
        )
        
        candidate['scores'] = {
            'technical': tech,
            'hiring_manager': hiring_manager,
            'culture_fit': culture_fit,
            'recruiter_ops': recruiter_ops,
            'logistics_education': logistics_edu,
            'persona_sum': persona_sum
        }
        
        scored_candidates.append(candidate)
        
    # 4. Apply TF-IDF Semantic similarity re-ranking on the high-potential pool
    scored_candidates = apply_semantic_similarity(scored_candidates, jd_text)
    
    # Parse JD for disqualifiers dynamically
    jd_parser = JDParser(jd_text=jd_text)
    jd_disqualifiers = jd_parser.get_disqualifiers()
    
    # 5. Calculate Final Composite Scores
    for c in scored_candidates:
        persona_sum = c['scores']['persona_sum']
        boost = c.get('semantic_boost', 1.0)
        mult, reason = get_hard_disqualifier_multiplier(c, jd_disqualifiers=jd_disqualifiers)
        
        c['final_score'] = round(float(persona_sum * boost * mult), 4)
        if mult < 1.0:
            c['hard_disqualified_reason'] = reason

        
    # 6. Sort by final score descending, breaking ties by candidate_id ascending (deterministic)
    scored_candidates.sort(key=lambda x: (-x['final_score'], x.get('candidate_id', '')))
    
    # 7. Apply diversity re-ranking to prevent clustering
    scored_candidates = apply_diversity_reranking(scored_candidates)
    
    # 8. Re-sort after diversity penalty
    scored_candidates.sort(key=lambda x: (-x['final_score'], x.get('candidate_id', '')))
    
    # 9. Take top 100
    top_100 = scored_candidates[:100]
    
    # Add ranking index (1-based)
    for idx, c in enumerate(top_100):
        c['rank'] = idx + 1
    
    # Attach detail lists to stats for audit logging
    stats['honeypot_details'] = honeypot_details
    stats['stuffer_details'] = stuffer_details
        
    return top_100, stats
