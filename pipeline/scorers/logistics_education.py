from config import PREFERRED_LOCATIONS, get_notice_period_weight

def calculate_logistics_education_score(candidate):
    """
    Evaluates notice period days, preferred locations / relocation willingness,
    work mode preference, salary alignment, education fields, and institution tier quality.
    Returns a score between 0.0 and 1.0.
    """
    profile = candidate.get('profile', {})
    education = candidate.get('education', [])
    signals = candidate.get('redrob_signals', {})
    
    # 1. Notice Period Score (30 days or less is ideal, 30+ has higher bar, >90 penalized)
    notice_days = float(signals.get('notice_period_days', 60))
    notice_score = get_notice_period_weight(notice_days)
    
    # 2. Location Alignment
    location = str(profile.get('location', '')).lower()
    country = str(profile.get('country', '')).lower()
    willing_to_relocate = signals.get('willing_to_relocate', False)
    
    is_preferred_loc = any(loc in location for loc in PREFERRED_LOCATIONS)
    # Open to relocation from Tier-1 Indian cities or India general
    is_india = country.strip().lower() in ['india', 'in']
    
    if is_preferred_loc:
        location_score = 1.0
    elif is_india and willing_to_relocate:
        location_score = 0.90
    elif willing_to_relocate:
        location_score = 0.75
    else:
        location_score = 0.60  # Local preference, but not strict blocker

    # 2b. Preferred Work Mode
    work_mode = str(signals.get('preferred_work_mode', '')).lower()
    if work_mode in ['hybrid', 'onsite']:
        work_mode_score = 1.0
    elif work_mode == 'flexible':
        work_mode_score = 0.9
    else:
        work_mode_score = 0.7

    # 2c. Salary Alignment
    salary = signals.get('expected_salary_range_inr_lpa', {})
    sal_min = float(salary.get('min', 0)) if isinstance(salary, dict) else 0
    sal_max = float(salary.get('max', 100)) if isinstance(salary, dict) else 100
    if sal_max <= 55 and sal_min >= 15:
        salary_score = 1.0
    elif sal_max <= 70:
        salary_score = 0.8
    else:
        salary_score = 0.5

    # 3. Education Score (Field of Study + Tier)
    edu_score = 0.50
    if education:
        tier_scores = []
        field_scores = []
        for edu in education:
            # Tier: tier_1 (1.0), tier_2 (0.85), tier_3 (0.7)
            tier = str(edu.get('tier', 'tier_3')).lower()
            if 'tier_1' in tier:
                tier_scores.append(1.0)
            elif 'tier_2' in tier:
                tier_scores.append(0.85)
            else:
                tier_scores.append(0.70)
                
            # Field of Study
            field = str(edu.get('field_of_study', '')).lower()
            if any(f in field for f in ['computer science', 'data science', 'artificial intelligence', 'machine learning', 'information technology', 'mathematics', 'statistics']):
                field_scores.append(1.0)
            elif any(f in field for f in ['engineering', 'physics', 'electrical']):
                field_scores.append(0.75)
            else:
                field_scores.append(0.50)
                
        max_tier = max(tier_scores) if tier_scores else 0.70
        max_field = max(field_scores) if field_scores else 0.50
        edu_score = 0.5 * max_tier + 0.5 * max_field

    # Combine Logistics (Notice + Location + Work Mode + Salary)
    logistics_score = 0.40 * notice_score + 0.25 * location_score + 0.20 * work_mode_score + 0.15 * salary_score
    
    # Combined score (weighted: Logistics 70%, Education 30%)
    final_score = 0.70 * logistics_score + 0.30 * edu_score
    return final_score
