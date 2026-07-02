from config import REQUIRED_SKILLS

# AI/ML title keywords that signal strong alignment with Senior AI Engineer JD
AI_TITLE_KEYWORDS = {
    'ml', 'machine learning', 'ai', 'data scientist', 'nlp',
    'deep learning', 'research scientist', 'applied scientist',
    'data science', 'artificial intelligence'
}

SENIOR_AI_TITLE_KEYWORDS = {
    'senior ml', 'lead ml', 'principal ml', 'senior ai', 'lead ai',
    'ml platform', 'ai platform', 'founding', 'head of ai', 'head of ml',
    'staff ml', 'staff ai', 'principal ai'
}

def calculate_technical_score(candidate):
    """
    Evaluates technical skills with title relevance, skill depth differentiation,
    Redrob assessment scores, skill evidence in descriptions, and GitHub contributions.
    Returns a score between 0.0 and 1.0.
    """
    profile = candidate.get('profile', {})
    career_history = candidate.get('career_history', [])
    skills = candidate.get('skills', [])
    signals = candidate.get('redrob_signals', {})
    assessment_scores = signals.get('skill_assessment_scores', {})
    
    # 1. Title Relevance Score (NEW — critical for differentiating AI engineers from backend devs)
    current_title = str(profile.get('current_title', '')).lower()
    headline = str(profile.get('headline', '')).lower()
    
    title_score = 0.3  # baseline for generic tech title
    
    # Check for senior AI/ML titles (highest value)
    if any(kw in current_title for kw in SENIOR_AI_TITLE_KEYWORDS):
        title_score = 1.0
    elif any(kw in current_title for kw in AI_TITLE_KEYWORDS):
        title_score = 0.85
    elif any(kw in headline for kw in AI_TITLE_KEYWORDS):
        title_score = 0.70
    elif 'engineer' in current_title or 'developer' in current_title:
        title_score = 0.40
    
    # Check career history for AI/ML roles (compound signal)
    ai_role_count = 0
    for job in career_history:
        job_title = str(job.get('title', '')).lower()
        if any(kw in job_title for kw in AI_TITLE_KEYWORDS):
            ai_role_count += 1
    
    career_ai_boost = min(ai_role_count * 0.15, 0.30)  # up to 0.30 boost for multiple AI roles
    
    # 2. Gather text content to find evidence of skills and map mentions to durations
    text_corpus = (
        str(profile.get('summary', '')) + " " +
        str(profile.get('headline', ''))
    ).lower()
    
    skill_job_durations = {}
    
    for job in career_history:
        desc = str(job.get('description', '')).lower()
        text_corpus += " " + desc
        dur = float(job.get('duration_months', 0))
        for req in REQUIRED_SKILLS:
            if req in desc:
                skill_job_durations[req] = skill_job_durations.get(req, 0.0) + dur
                
    # Apply technology limits (cannot have more experience than the tech has existed)
    if 'rag' in skill_job_durations:
        skill_job_durations['rag'] = min(skill_job_durations['rag'], 60.0)
    if 'peft' in skill_job_durations:
        skill_job_durations['peft'] = min(skill_job_durations['peft'], 48.0)
        
    # 3. Score each skill listed in the profile
    proven_skills_scores = []
    matched_required_count = 0
    explicit_reqs = set()
    
    for s in skills:
        name = str(s.get('name', '')).lower()
        
        # Find which required keyword matched
        matched_req = None
        for req in REQUIRED_SKILLS:
            if req in name:
                matched_req = req
                explicit_reqs.add(req)
                break
                
        is_required = matched_req is not None
        
        in_desc = 1.0 if name in text_corpus else 0.0
        
        # Proof of Competence: Cross-validate duration claimed vs duration in job descriptions
        if is_required:
            if matched_req in skill_job_durations:
                job_dur_sum = skill_job_durations[matched_req]
                claimed_dur = float(s.get('duration_months', 0))
                
                if matched_req == 'rag' or 'rag' in name:
                    claimed_dur = min(claimed_dur, 60.0)
                if matched_req == 'peft' or 'peft' in name:
                    claimed_dur = min(claimed_dur, 48.0)
                    
                if claimed_dur > 0:
                    ratio = min(job_dur_sum / claimed_dur, 1.0)
                    # Downscale in_desc if the career history doesn't support the claimed duration
                    in_desc = in_desc * (0.70 + 0.30 * ratio)
            else:
                # Claimed skill has zero mention in any job description (keyword stuffing warning)
                in_desc = in_desc * 0.70
        
        assess_val = 0.0
        for ass_name, score in assessment_scores.items():
            if ass_name.lower() in name or name in ass_name.lower():
                assess_val = float(score) / 100.0
                break
                
        endorsements = float(s.get('endorsements', 0))
        duration = float(s.get('duration_months', 0))
        if matched_req == 'rag' or 'rag' in name:
            duration = min(duration, 60.0)
        if matched_req == 'peft' or 'peft' in name:
            duration = min(duration, 48.0)
        proficiency = str(s.get('proficiency', '')).lower()
        
        # Proficiency multiplier (differentiates expert vs intermediate)
        prof_mult = {'expert': 1.0, 'advanced': 0.85, 'intermediate': 0.60, 'beginner': 0.30}.get(proficiency, 0.50)
        
        # Evidence formula with proficiency weighting
        evidence_score = (
            0.30 * in_desc +
            0.25 * assess_val +
            0.15 * min(endorsements / 20.0, 1.0) +
            0.15 * min(duration / 36.0, 1.0) +
            0.15 * prof_mult
        )
        
        if is_required:
            matched_required_count += 1
            proven_skills_scores.append(evidence_score)
            
    # 4. Discover Hidden Gems: Required skills mentioned in career history but NOT explicitly listed in skills list
    for req, job_dur in skill_job_durations.items():
        if req not in explicit_reqs and job_dur > 0:
            # Candidate has proven experience with 'req' via career history description
            in_desc = 1.0
            assess_val = 0.0
            endorsements = 0.0
            duration = job_dur
            proficiency = 'intermediate'  # default fallback for implicit skills
            prof_mult = 0.60
            
            evidence_score = (
                0.30 * in_desc +
                0.25 * assess_val +
                0.15 * min(endorsements / 20.0, 1.0) +
                0.15 * min(duration / 36.0, 1.0) +
                0.15 * prof_mult
            )
            
            matched_required_count += 1
            proven_skills_scores.append(evidence_score)
            
    # 5. Overall Skill score
    if proven_skills_scores:
        skill_score = sum(proven_skills_scores) / len(proven_skills_scores)
    else:
        skill_score = 0.0
        
    # Coverage multiplier — lowered denominator so partial matches aren't crushed
    coverage = min(matched_required_count / 6.0, 1.0)
    skill_score = skill_score * coverage
    
    # 5. GitHub activity bonus (0.0 to 0.10)
    github_score = float(signals.get('github_activity_score', -1))
    github_bonus = 0.0
    if github_score > 0:
        github_bonus = (github_score / 100.0) * 0.10

    # 6. Certification bonus
    certs = candidate.get('certifications', [])
    cert_bonus = 0.0
    ml_cert_keywords = ['machine learning', 'deep learning', 'ai', 'data science', 'tensorflow', 'aws ml', 'gcp ml', 'azure ai']
    for cert in certs:
        cert_name = str(cert.get('name', '')).lower()
        if any(kw in cert_name for kw in ml_cert_keywords):
            cert_bonus = 0.05
            break

    # 7. Composite: weighted blend of title relevance, skill depth, and bonuses
    # Title relevance matters a LOT — a "Senior ML Platform Engineer" should score
    # much higher than a "Backend Developer" even if both have PyTorch listed
    final_tech_score = (
        0.30 * title_score +
        0.15 * career_ai_boost / 0.30 +  # normalize to 0-1 range
        0.40 * skill_score +
        0.10 * github_bonus / 0.10 +  # normalize to 0-1 range
        0.05 * (cert_bonus / 0.05)  # normalize to 0-1 range
    )
    
    return min(max(final_tech_score, 0.0), 1.0)
