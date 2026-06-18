import datetime

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def get_honeypot_reasons(candidate):
    """
    Checks all honeypot rules and returns a list of violated rule descriptions.
    If the list is empty, the candidate is clean.
    """
    profile = candidate.get('profile', {})
    career_history = candidate.get('career_history', [])
    education = candidate.get('education', [])
    skills = candidate.get('skills', [])
    
    reasons = []
    
    # Rule 1: Job Timeline Paradox (start_date > end_date)
    for job in career_history:
        start = parse_date(job.get('start_date'))
        end = parse_date(job.get('end_date'))
        if start and end and start > end:
            reasons.append(f"Job Timeline Paradox (starts {job.get('start_date')} after ending {job.get('end_date')} at {job.get('company')})")
            break

    # Rule 2: Education Timeline Paradox (start_year > end_year)
    for edu in education:
        start_yr = edu.get('start_year')
        end_yr = edu.get('end_year')
        if start_yr and end_yr and start_yr > end_yr:
            reasons.append(f"Education Timeline Paradox (starts {start_yr} after ending {end_yr} at {edu.get('institution')})")
            break

    # Rule 3: Extreme Overlapping Full-Time Jobs
    intervals = []
    for job in career_history:
        start = parse_date(job.get('start_date'))
        end = parse_date(job.get('end_date'))
        if not end and job.get('is_current'):
            end = datetime.datetime(2026, 6, 9) # Reference date for hackathon
        if start and end:
            intervals.append((start, end))
            
    if len(intervals) >= 3:
        overlap_count = 0
        for i in range(len(intervals)):
            s1, e1 = intervals[i]
            overlaps = 0
            for j in range(len(intervals)):
                if i == j: continue
                s2, e2 = intervals[j]
                if max(s1, s2) <= min(e1, e2):
                    overlaps += 1
            if overlaps >= 2:
                overlap_count += 1
        if overlap_count >= 3:
            reasons.append("Extreme Overlapping Jobs (3+ concurrent full-time roles)")

    # Rule 4: Skill Inflation / Endorsement Fraud
    expert_no_proof = 0
    for s in skills:
        prof = str(s.get('proficiency', '')).lower()
        endorsements = s.get('endorsements', 0)
        duration = s.get('duration_months', 0)
        if prof == 'expert' and endorsements == 0 and duration == 0:
            expert_no_proof += 1
            
    if expert_no_proof >= 10:
        reasons.append(f"Skill Inflation ({expert_no_proof} expert skills declared without endorsements or duration)")

    # Rule 5: Impossible YoE relative to earliest activity start (college or career)
    years_of_experience = profile.get('years_of_experience', 0)
    years = []
    for job in career_history:
        start = parse_date(job.get('start_date'))
        if start:
            years.append(start.year)
    for edu in education:
        start_yr = edu.get('start_year')
        if start_yr:
            years.append(start_yr)
            
    if years:
        earliest_activity = min(years)
        max_possible_yoe = (2026 - earliest_activity) + 2
        if years_of_experience > max_possible_yoe and years_of_experience > 5:
            reasons.append(f"Impossible Stated YoE ({years_of_experience} yrs vs max possible {max_possible_yoe} yrs since earliest activity in {earliest_activity})")

    # Rule 6: Timeline Plausibility
    if education:
        edu_end_years = [edu.get('end_year') for edu in education if edu.get('end_year')]
        if edu_end_years:
            min_edu_end = min(edu_end_years)
            max_possible_months = (2026 - min_edu_end + 2) * 12
            for job in career_history:
                duration_months = job.get('duration_months', 0)
                if duration_months > max_possible_months:
                    reasons.append(f"Single job duration ({duration_months}mo) exceeds max possible career timeline ({max_possible_months}mo)")
                    break
    for job in career_history:
        duration_months = job.get('duration_months', 0)
        if years_of_experience > 0 and duration_months > (years_of_experience * 12 + 12):
            reasons.append(f"Single job duration ({duration_months}mo) exceeds total stated YoE ({years_of_experience} yrs)")
            break

    # Rule 7: Future dates (start date after reference)
    ref = datetime.datetime(2026, 6, 9)
    for job in career_history:
        start = parse_date(job.get('start_date'))
        if start and start > ref and not job.get('is_current'):
            reasons.append(f"Future dates detected (job starts {job.get('start_date')})")
            break

    # Rule 8: Unrealistic skill count
    if len(skills) > 40:
        reasons.append(f"Unrealistic Skill Count ({len(skills)} skills declared)")

    # Rule 9: All assessment scores exactly 100 (suspiciously perfect)
    assessments = candidate.get('redrob_signals', {}).get('skill_assessment_scores', {})
    if len(assessments) >= 5:
        try:
            if all(float(v) == 100.0 for v in assessments.values()):
                reasons.append("Suspiciously Perfect Assessment Scores (all 100.0)")
        except (TypeError, ValueError):
            pass

    return reasons

def is_honeypot(candidate):
    """
    Evaluates structural rules to identify impossible profiles (honeypots).
    Returns True if the candidate is a confirmed honeypot, False otherwise.
    """
    return len(get_honeypot_reasons(candidate)) > 0
