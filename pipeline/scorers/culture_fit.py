from config import CONSULTING_COMPANIES, PRODUCT_COMPANY_KEYWORDS

def calculate_culture_fit_score(candidate):
    """
    Evaluates consulting firm limits, academic-only exclusions, framework enthusiast checks,
    and checks for product-company mindsets.
    Returns a score between 0.0 and 1.0.
    """
    career_history = candidate.get('career_history', [])
    profile = candidate.get('profile', {})
    summary = str(profile.get('summary', '')).lower()
    headline = str(profile.get('headline', '')).lower()
    
    if not career_history:
        return 0.5
        
    # 1. Consulting-Only Check
    # If 100% of their career history has been in consulting companies, they fail this gate.
    consulting_count = 0
    product_mindset_count = 0
    has_product_job = False
    
    for job in career_history:
        company = str(job.get('company', '')).lower()
        title = str(job.get('title', '')).lower()
        desc = str(job.get('description', '')).lower()
        
        is_consulting = any(c in company for c in CONSULTING_COMPANIES)
        if is_consulting:
            consulting_count += 1
        else:
            # Check if company or desc has product company signals
            has_prod_sig = any(kw in desc or kw in title for kw in PRODUCT_COMPANY_KEYWORDS)
            if has_prod_sig:
                product_mindset_count += 1
                has_product_job = True
                
    total_jobs = len(career_history)
    
    # Consulting modifier
    if consulting_count == total_jobs:
        # Consulting only
        consulting_modifier = 0.1  # Hard penalty
    elif consulting_count > 0:
        # Mixed (currently at consulting, but worked at product before)
        consulting_modifier = 0.8
    else:
        consulting_modifier = 1.0
        
    # 2. Pure Research/Academic Check
    # If all job titles are academic/research and none are engineering
    academic_titles = {'research assistant', 'phd candidate', 'postdoc', 'academic', 'researcher', 'fellow', 'intern'}
    academic_count = 0
    has_eng_job = False
    
    for job in career_history:
        title = str(job.get('title', '')).lower()
        if any(ac in title for ac in academic_titles) and 'engineer' not in title and 'developer' not in title:
            academic_count += 1
        else:
            has_eng_job = True
            
    if academic_count == total_jobs and not has_eng_job:
        academic_modifier = 0.1  # Hard penalty for research-only
    else:
        academic_modifier = 1.0
        
    # 3. Product Mindset Score
    # How much does the summary / headline reflect product shipping?
    summary_prod_matches = sum(1 for kw in PRODUCT_COMPANY_KEYWORDS if kw in summary)
    headline_prod_matches = sum(1 for kw in PRODUCT_COMPANY_KEYWORDS if kw in headline)
    
    product_score = 0.5
    if has_product_job:
        product_score += 0.2
    if summary_prod_matches >= 2:
        product_score += 0.2
    if headline_prod_matches >= 1:
        product_score += 0.1
        
    product_score = min(product_score, 1.0)
    
    # Final Culture-Fit Score is product score modified by hard rules
    final_score = product_score * consulting_modifier * academic_modifier
    return final_score
