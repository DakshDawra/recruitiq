import datetime

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def is_honeypot(candidate):
    """
    Evaluates structural rules to identify impossible profiles (honeypots).
    Returns True if the candidate is a confirmed honeypot, False otherwise.
    """
    profile = candidate.get('profile', {})
    career_history = candidate.get('career_history', [])
    education = candidate.get('education', [])
    skills = candidate.get('skills', [])
    
    # Rule 1: Job Timeline Paradox (start_date > end_date)
    for job in career_history:
        start = parse_date(job.get('start_date'))
        end = parse_date(job.get('end_date'))
        if start and end and start > end:
            return True

    # Rule 2: Education Timeline Paradox (start_year > end_year)
    for edu in education:
        start_yr = edu.get('start_year')
        end_yr = edu.get('end_year')
        if start_yr and end_yr and start_yr > end_yr:
            return True

    # Rule 3: Extreme Overlapping Full-Time Jobs
    # Track overlapping intervals of full-time jobs
    intervals = []
    for job in career_history:
        # Assume full-time if company_size or other details fit (we treat all listed career items as primary)
        start = parse_date(job.get('start_date'))
        end = parse_date(job.get('end_date'))
        if not end and job.get('is_current'):
            end = datetime.datetime(2026, 6, 9) # Reference date for hackathon
        if start and end:
            intervals.append((start, end))
            
    # Check if there are 3 or more overlapping intervals
    if len(intervals) >= 3:
        overlap_count = 0
        for i in range(len(intervals)):
            s1, e1 = intervals[i]
            overlaps = 0
            for j in range(len(intervals)):
                if i == j: continue
                s2, e2 = intervals[j]
                # Check intersection
                if max(s1, s2) <= min(e1, e2):
                    overlaps += 1
            if overlaps >= 2:
                # This interval overlaps with at least 2 other intervals simultaneously
                overlap_count += 1
        if overlap_count >= 3:
            return True

    # Rule 4: Skill Inflation / Endorsement Fraud
    # "expert" proficiency in 10 skills with 0 years (duration_months) used
    expert_no_proof = 0
    for s in skills:
        prof = str(s.get('proficiency', '')).lower()
        endorsements = s.get('endorsements', 0)
        duration = s.get('duration_months', 0)
        if prof == 'expert' and endorsements == 0 and duration == 0:
            expert_no_proof += 1
            
    if expert_no_proof >= 10:
        return True

    # Rule 5: Impossible YoE relative to college graduation
    years_of_experience = profile.get('years_of_experience', 0)
    if education:
        # Find the earliest education end year
        edu_end_years = [edu.get('end_year') for edu in education if edu.get('end_year')]
        if edu_end_years:
            min_edu_end = min(edu_end_years)
            # Reference year is 2026
            max_possible_yoe = (2026 - min_edu_end) + 2
            if years_of_experience > max_possible_yoe and years_of_experience > 5:
                return True

    # Rule 6: Timeline Plausibility
    # Check if a single job's duration exceeds the maximum possible timeline since graduation
    # or exceeds their own stated years of experience.
    if education:
        edu_end_years = [edu.get('end_year') for edu in education if edu.get('end_year')]
        if edu_end_years:
            min_edu_end = min(edu_end_years)
            max_possible_months = (2026 - min_edu_end + 2) * 12
            for job in career_history:
                duration_months = job.get('duration_months', 0)
                if duration_months > max_possible_months:
                    return True

    for job in career_history:
        duration_months = job.get('duration_months', 0)
        if years_of_experience > 0 and duration_months > (years_of_experience * 12 + 12):
            return True

    # Rule 7: Future dates (start or end date after reference)
    ref = datetime.datetime(2026, 6, 9)
    for job in career_history:
        start = parse_date(job.get('start_date'))
        if start and start > ref and not job.get('is_current'):
            return True

    # Rule 8: Unrealistic skill count
    if len(skills) > 40:
        return True

    # Rule 9: All assessment scores exactly 100 (suspiciously perfect)
    assessments = candidate.get('redrob_signals', {}).get('skill_assessment_scores', {})
    if len(assessments) >= 5:
        try:
            if all(float(v) == 100.0 for v in assessments.values()):
                return True
        except (TypeError, ValueError):
            pass

    return False
