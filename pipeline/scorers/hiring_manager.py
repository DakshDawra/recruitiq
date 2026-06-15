def calculate_hiring_manager_score(candidate):
    """
    Evaluates experience alignment (5-9 years), average tenure stability (penalizes title-chasers),
    seniority progression, and target company size/type.
    Returns a score between 0.0 and 1.0.
    """
    profile = candidate.get('profile', {})
    career_history = candidate.get('career_history', [])
    
    # 1. Experience Years Alignment (Target: 5-9 years)
    yoe = float(profile.get('years_of_experience', 0))
    if 5.0 <= yoe <= 9.0:
        yoe_score = 1.0
    elif 4.0 <= yoe < 5.0:
        yoe_score = 0.85
    elif 9.0 < yoe <= 12.0:
        yoe_score = 0.90
    elif 3.0 <= yoe < 4.0:
        yoe_score = 0.60
    elif yoe > 12.0:
        yoe_score = 0.70
    else:
        yoe_score = 0.20  # Under 3 years is heavily penalized
        
    # 2. Tenure Stability (Total months divided by number of roles)
    total_months = 0
    num_jobs = len(career_history)
    for job in career_history:
        total_months += float(job.get('duration_months', 0))
        
    if num_jobs > 0:
        avg_tenure = total_months / num_jobs
        if avg_tenure >= 36: # 3+ years average
            tenure_score = 1.0
        elif avg_tenure >= 24: # 2+ years average
            tenure_score = 0.85
        elif avg_tenure >= 18: # 1.5 years average (borderline)
            tenure_score = 0.65
        else: # < 1.5 years (typical title chaser)
            tenure_score = 0.30
    else:
        tenure_score = 0.50
        
    # 3. Seniority Progression
    # Check if latest title indicates senior/lead status
    progression_score = 0.70
    if career_history:
        sorted_history = sorted(career_history, key=lambda j: j.get('start_date', ''), reverse=True)
        latest_title = str(sorted_history[0].get('title', '')).lower()
        if any(kw in latest_title for kw in ['senior', 'lead', 'principal', 'head', 'founding', 'manager', 'architect']):
            progression_score = 1.0
            
    # 4. Company Size Alignment (Preferred: mid-size product company)
    company_score = 0.70
    if career_history:
        sorted_history = sorted(career_history, key=lambda j: j.get('start_date', ''), reverse=True)
        company_size = str(sorted_history[0].get('company_size', ''))
        # Prefer sizes 51-200, 201-500, 501-1000, 1001-5000 (standard product growth stages)
        if any(sz in company_size for sz in ['51-200', '201-500', '501-1000', '1001-5000']):
            company_score = 1.0
            
    # Combine scores
    composite_score = (
        0.40 * yoe_score +
        0.30 * tenure_score +
        0.15 * progression_score +
        0.15 * company_score
    )
    
    return composite_score
