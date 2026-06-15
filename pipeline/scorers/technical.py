from config import REQUIRED_SKILLS

def calculate_technical_score(candidate):
    """
    Evaluates technical skills, Redrob assessment scores, skill evidence in descriptions,
    and GitHub contributions.
    Returns a score between 0.0 and 1.0.
    """
    profile = candidate.get('profile', {})
    career_history = candidate.get('career_history', [])
    skills = candidate.get('skills', [])
    signals = candidate.get('redrob_signals', {})
    assessment_scores = signals.get('skill_assessment_scores', {})
    
    # 1. Gather text content to find evidence of skills
    text_corpus = (
        str(profile.get('summary', '')) + " " +
        str(profile.get('headline', ''))
    ).lower()
    for job in career_history:
        text_corpus += " " + str(job.get('description', '')).lower()
        
    # 2. Score each skill listed in the profile
    proven_skills_scores = []
    matched_required_count = 0
    
    for s in skills:
        name = str(s.get('name', '')).lower()
        # Verify if it is a required skill for the JD
        is_required = any(req in name for req in REQUIRED_SKILLS)
        
        # Calculate evidence for this skill
        in_desc = 1.0 if name in text_corpus else 0.0
        
        # Redrob assessment score (0-100)
        assess_val = 0.0
        # Find matches in assessment dict (case-insensitive)
        for ass_name, score in assessment_scores.items():
            if ass_name.lower() in name or name in ass_name.lower():
                assess_val = float(score) / 100.0
                break
                
        # Endorsements & Duration months
        endorsements = float(s.get('endorsements', 0))
        duration = float(s.get('duration_months', 0))
        
        # Evidence formula
        evidence_score = (
            0.40 * in_desc +
            0.25 * assess_val +
            0.20 * min(endorsements / 20.0, 1.0) +
            0.15 * min(duration / 36.0, 1.0)
        )
        
        if is_required:
            matched_required_count += 1
            proven_skills_scores.append(evidence_score)
            
    # 3. Overall Skill score
    # Base is the average of matched required skills' evidence
    if proven_skills_scores:
        skill_score = sum(proven_skills_scores) / len(proven_skills_scores)
    else:
        skill_score = 0.0
        
    # Scale skill score by the fraction of key JD requirements matched
    # e.g., if they match 5+ required skills, they get full coverage multiplier
    coverage = min(matched_required_count / 10.0, 1.0)
    skill_score = skill_score * coverage
    
    # 4. GitHub activity bonus (0.0 to 0.1)
    github_score = float(signals.get('github_activity_score', -1))
    github_bonus = 0.0
    if github_score > 0:
        github_bonus = (github_score / 100.0) * 0.1

    # 5. Certification bonus
    certs = candidate.get('certifications', [])
    cert_bonus = 0.0
    ml_cert_keywords = ['machine learning', 'deep learning', 'ai', 'data science', 'tensorflow', 'aws ml', 'gcp ml', 'azure ai']
    for cert in certs:
        cert_name = str(cert.get('name', '')).lower()
        if any(kw in cert_name for kw in ml_cert_keywords):
            cert_bonus = 0.05
            break

    final_tech_score = min(skill_score + github_bonus + cert_bonus, 1.0)
    return final_tech_score
