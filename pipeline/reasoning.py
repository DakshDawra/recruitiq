from config import REQUIRED_SKILLS

def generate_candidate_reasoning(candidate):
    """
    Generates unique, fact-dense reasoning for each candidate.
    Uses specific profile data points to ensure diversity across similar profiles.
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
    completeness = signals.get('profile_completeness_score', 0)
    saved_count = signals.get('saved_by_recruiters_30d', 0)
    interview_rate = float(signals.get('interview_completion_rate', 0.0))
    assessment_scores = signals.get('skill_assessment_scores', {})
    
    # Collect matched JD skills
    matched_skills = []
    for s in skills:
        s_name = str(s.get('name', ''))
        if any(req in s_name.lower() for req in REQUIRED_SKILLS):
            prof = s.get('proficiency', 'intermediate')
            dur = s.get('duration_months', 0)
            matched_skills.append((s_name, prof, dur))
    
    # Build skill evidence string (top 3)
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
    
    # Assessment scores context (unique per candidate)
    assess_parts = []
    for skill_name, score_val in sorted(assessment_scores.items(), key=lambda x: -float(x[1]))[:2]:
        assess_parts.append(f"{skill_name}: {float(score_val):.0f}/100")
    assess_str = "; ".join(assess_parts) if assess_parts else None
    
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
    
    # Build strengths (pick diverse signals)
    strengths = []
    if skills_str:
        strengths.append(f"JD-aligned expertise in {skills_str}")
    if assess_str:
        strengths.append(f"verified assessments ({assess_str})")
    if career_str:
        strengths.append(f"career trajectory: {career_str}")
    if industry and any(kw in industry.lower() for kw in ['tech', 'software', 'ai', 'fintech', 'saas', 'platform']):
        strengths.append(f"product-company background ({industry})")
    if github > 20:
        strengths.append(f"active GitHub (score: {github:.0f}/100)")
    if notice <= 30:
        strengths.append(f"immediately available ({notice}d notice)")
    if response_rate > 0.8:
        strengths.append(f"highly responsive ({response_rate*100:.0f}% rate)")
    if saved_count > 10:
        strengths.append(f"high recruiter interest ({saved_count} saves in 30d)")
    if interview_rate > 0.8:
        strengths.append(f"strong interview follow-through ({interview_rate*100:.0f}%)")
    if edu_str and rank <= 30:
        strengths.append(f"education: {edu_str}")
    
    # Build concerns
    concerns = []
    if not matched_skills:
        concerns.append("limited AI/ML skill keywords")
    if github <= 0:
        concerns.append("no public GitHub activity")
    if notice > 60:
        concerns.append(f"extended notice ({notice}d)")
    if yoe < 5:
        concerns.append(f"below target YoE ({yoe:.1f} vs 5-9yr)")
    elif yoe > 12:
        concerns.append(f"above target YoE ({yoe:.1f}yr)")
    if response_rate < 0.3 and response_rate > 0:
        concerns.append(f"low response rate ({response_rate*100:.0f}%)")
    if completeness < 60:
        concerns.append(f"incomplete profile ({completeness:.0f}% filled)")
    
    # Compose reasoning
    parts = [f"{title} at {company} with {yoe:.1f} yrs"]
    if location:
        parts.append(f"based in {location}")
    opening = ", ".join(parts) + "."
    
    if strengths:
        body = " Strengths: " + "; ".join(strengths[:3]) + "."
    else:
        body = " General software engineering background without strong JD-specific signals."
    
    if concerns and rank > 50:
        concern_str = " Gaps: " + "; ".join(concerns[:2]) + "."
    elif concerns:
        concern_str = " Notes: " + "; ".join(concerns[:2]) + "."
    else:
        concern_str = ""
    
    reasoning = opening + body + concern_str
    
    if len(reasoning) > 500:
        reasoning = reasoning[:497] + "..."
    
    return reasoning
