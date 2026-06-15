from config import NON_TECH_TITLES, REQUIRED_SKILLS

def is_coarse_match(candidate):
    """
    Fast, safe heuristic filter to discard completely irrelevant profiles.
    Returns True to keep the candidate, False to discard.
    """
    profile = candidate.get('profile', {})
    current_title = str(profile.get('current_title', '')).lower()
    headline = str(profile.get('headline', '')).lower()
    summary = str(profile.get('summary', '')).lower()
    
    # 1. Always keep direct AI/ML/Data/Software titles
    tech_keywords = {
        'ml', 'machine learning', 'ai', 'data', 'nlp', 'applied scientist',
        'software', 'backend', 'developer', 'engineer', 'programmer', 'tech',
        'architect', 'coding', 'coder', 'systems'
    }
    
    title_words = set(current_title.replace('/', ' ').replace('-', ' ').split())
    headline_words = set(headline.replace('/', ' ').replace('-', ' ').split())
    
    is_tech_title = any(kw in current_title for kw in tech_keywords)
    is_tech_headline = any(kw in headline for kw in tech_keywords)
    
    if is_tech_title or is_tech_headline:
        return True
        
    # 2. If the current title is explicitly in our non-tech list,
    # we only keep them if they have AI/ML keywords in their summary or skills list
    is_explicit_non_tech = any(nt in current_title for nt in NON_TECH_TITLES)
    
    if is_explicit_non_tech:
        # Check skills for AI/ML keywords
        skills = candidate.get('skills', [])
        has_ai_skill = False
        for s in skills:
            skill_name = str(s.get('name', '')).lower()
            if any(req in skill_name for req in REQUIRED_SKILLS):
                has_ai_skill = True
                break
                
        # Check summary for AI keywords
        has_ai_summary = any(req in summary for req in REQUIRED_SKILLS)
        
        if has_ai_skill or has_ai_summary:
            return True
        else:
            return False
            
    # 3. Default: if they don't have tech keywords and aren't explicitly non-tech,
    # keep them to be safe (no aggressive filtering of edge cases)
    return True
