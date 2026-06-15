def get_hard_disqualifier_multiplier(candidate):
    """
    Evaluates narrative JD disqualifiers. 
    If a candidate hits any of these hard red flags, returns a near-zero multiplier (0.01)
    and the reason. Otherwise returns (1.0, None).
    """
    profile = candidate.get('profile', {})
    career_history = candidate.get('career_history', [])
    skills = candidate.get('skills', [])
    signals = candidate.get('redrob_signals', {})
    
    years_of_experience = profile.get('years_of_experience', 0)
    
    # 1. Pure Consulting-Only
    # Check if ALL career entries belong to companies in a predefined consulting blacklist
    consulting_blacklist = {'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini', 'tech mahindra', 'hcl'}
    
    has_consulting = False
    has_product = False
    for job in career_history:
        company = str(job.get('company', '')).lower()
        is_consulting = any(c in company for c in consulting_blacklist)
        if is_consulting:
            has_consulting = True
        elif company.strip(): # non-empty company not in blacklist
            has_product = True
            
    if has_consulting and not has_product and len(career_history) > 0:
        return 0.01, "Pure Consulting-Only Career"

    # 2. Title-Chaser
    # Detect if a candidate has >= 3 jobs, each lasting < 18 months, with title progressions
    short_jobs = 0
    for job in career_history:
        if job.get('duration_months', 0) > 0 and job.get('duration_months', 0) < 18:
            short_jobs += 1
            
    if short_jobs >= 3 and len(career_history) >= 3 and short_jobs == len(career_history):
        return 0.01, "Serial Title-Chaser (Frequent job hopping)"

    # 3. CV/Speech/Robotics without NLP
    cv_keywords = {'computer vision', 'image processing', 'object detection', 'speech recognition', 'robotics'}
    nlp_keywords = {'nlp', 'natural language', 'llm', 'rag', 'text', 'language model', 'transformers', 'bert'}
    
    has_cv = False
    has_nlp = False
    for s in skills:
        skill_name = str(s.get('name', '')).lower()
        if any(kw in skill_name for kw in cv_keywords):
            has_cv = True
        if any(kw in skill_name for kw in nlp_keywords):
            has_nlp = True
            
    if has_cv and not has_nlp:
        return 0.01, "CV/Speech/Robotics pure background without NLP/IR"

    # 4. Low external visibility (soft penalty, not hard disqualification)
    github_score = float(signals.get('github_activity_score', -1))
    if years_of_experience > 5.0 and github_score >= 0 and github_score < 5.0:
        return 0.90, "Limited public code visibility for 5+ years experience"
        
    return 1.0, None
