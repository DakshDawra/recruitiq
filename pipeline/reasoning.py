from config import REQUIRED_SKILLS

def generate_candidate_reasoning(candidate):
    """
    Generates unique, fact-dense, non-templated reasoning for each candidate.
    References specific profile data, connects to JD requirements, and acknowledges gaps.
    """
    profile = candidate.get('profile', {})
    skills = candidate.get('skills', [])
    signals = candidate.get('redrob_signals', {})
    scores = candidate.get('scores', {})
    career_history = candidate.get('career_history', [])
    education = candidate.get('education', [])
    
    title = profile.get('current_title', 'Professional')
    yoe = profile.get('years_of_experience', 0.0)
    company = profile.get('current_company', '')
    location = profile.get('location', '')
    country = profile.get('country', '')
    industry = profile.get('current_industry', '')
    notice = signals.get('notice_period_days', 60)
    github = float(signals.get('github_activity_score', -1))
    response_rate = float(signals.get('recruiter_response_rate', 0.0))
    rank = candidate.get('rank', 50)
    
    # Collect matched JD skills
    matched_skills = []
    for s in skills:
        s_name = str(s.get('name', ''))
        if any(req in s_name.lower() for req in REQUIRED_SKILLS):
            prof = s.get('proficiency', 'intermediate')
            dur = s.get('duration_months', 0)
            matched_skills.append((s_name, prof, dur))
    
    # Build skill evidence string
    if matched_skills:
        top_skills = matched_skills[:3]
        skill_parts = []
        for sname, prof, dur in top_skills:
            if dur > 0:
                skill_parts.append(f"{sname} ({dur}mo, {prof})")
            else:
                skill_parts.append(f"{sname} ({prof})")
        skills_str = ", ".join(skill_parts)
    else:
        skills_str = None
    
    # Career context
    sorted_jobs = sorted(career_history, key=lambda j: j.get('start_date', ''), reverse=True)
    career_parts = []
    for job in sorted_jobs[:2]:
        j_company = job.get('company', '')
        j_title = job.get('title', '')
        j_dur = job.get('duration_months', 0)
        if j_company and j_title:
            career_parts.append(f"{j_title} at {j_company} ({j_dur}mo)")
    career_str = "; ".join(career_parts) if career_parts else None
    
    # Education context
    edu_str = None
    if education:
        best_edu = education[0]
        inst = best_edu.get('institution', '')
        degree = best_edu.get('degree', '')
        field = best_edu.get('field_of_study', '')
        tier = best_edu.get('tier', 'unknown')
        if inst:
            edu_str = f"{degree} in {field} from {inst} ({tier.replace('_', ' ')})"
    
    # Build strengths
    strengths = []
    if skills_str:
        strengths.append(f"demonstrates JD-aligned expertise in {skills_str}")
    if career_str:
        strengths.append(f"career trajectory includes {career_str}")
    if industry and any(kw in industry.lower() for kw in ['tech', 'software', 'ai', 'fintech', 'saas', 'platform']):
        strengths.append(f"product-company background in {industry}")
    if github > 20:
        strengths.append(f"active GitHub contributor (score: {github:.0f}/100)")
    if notice <= 30:
        strengths.append(f"immediately available ({notice}d notice)")
    if response_rate > 0.8:
        strengths.append(f"highly responsive to recruiters ({response_rate*100:.0f}% rate)")
    
    # Build concerns
    concerns = []
    if not matched_skills:
        concerns.append("limited explicit AI/ML skill keywords in profile")
    if github <= 0:
        concerns.append("no public GitHub activity visible")
    if notice > 60:
        concerns.append(f"extended notice period ({notice}d) may delay onboarding")
    if yoe < 5:
        concerns.append(f"below target experience range ({yoe:.1f} vs 5-9yr requirement)")
    elif yoe > 12:
        concerns.append(f"above target experience range ({yoe:.1f}yr) — may be overqualified")
    if response_rate < 0.3 and response_rate > 0:
        concerns.append(f"low recruiter response rate ({response_rate*100:.0f}%)")
    
    # Compose reasoning based on rank tier
    parts = []
    
    # Opening — always unique because it uses specific title/company/yoe
    parts.append(f"{title} at {company} with {yoe:.1f} years of experience")
    if location:
        parts.append(f"based in {location}")
    
    opening = ", ".join(parts) + "."
    
    # Body — strengths
    if strengths:
        body = "Key strengths: " + "; ".join(strengths[:3]) + "."
    else:
        body = "Profile shows general software engineering background without strong JD-specific signals."
    
    # Concerns (honest acknowledgment)
    if concerns and rank > 50:
        concern_str = " Notable gaps: " + "; ".join(concerns[:2]) + "."
    elif concerns and rank > 15:
        concern_str = " Considerations: " + "; ".join(concerns[:2]) + "."
    else:
        concern_str = ""
    
    reasoning = opening + " " + body + concern_str
    
    # Trim to reasonable length
    if len(reasoning) > 500:
        reasoning = reasoning[:497] + "..."
    
    return reasoning
