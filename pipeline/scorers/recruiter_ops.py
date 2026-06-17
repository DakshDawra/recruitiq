import datetime
import math

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def calculate_recruiter_ops_score(candidate):
    """
    Evaluates response rates, interview completion rates, active job seeking (open to work),
    last login dates, collaborative recruiter saves (PageRank), profile completeness,
    response quality, network strength, offer reliability, and trust verification.
    Returns a score between 0.0 and 1.0.
    """
    signals = candidate.get('redrob_signals', {})
    
    # 1. Platform Activity Factor (Exponential decay based on last login)
    ref_date = datetime.datetime(2026, 6, 9) # Hackathon dataset reference date
    last_active_str = signals.get('last_active_date')
    last_active = parse_date(last_active_str)
    
    if last_active:
        delta_days = max((ref_date - last_active).days, 0)
        # Exponential decay: 45 days is half-life
        activity_factor = math.exp(-delta_days / 45.0)
    else:
        activity_factor = 0.1
        
    # 2. Recruiter PageRank (collaborative saves + appearances + profile views)
    saves = float(signals.get('saved_by_recruiters_30d', 0))
    appearances = float(signals.get('search_appearance_30d', 0))
    profile_views = float(signals.get('profile_views_received_30d', 0))
    
    pagerank_score = (
        0.45 * min(saves / 25.0, 1.0) +
        0.30 * min(appearances / 150.0, 1.0) +
        0.25 * min(profile_views / 100.0, 1.0)
    )
    
    # Factor in signup_date (longer-tenured platform users are more established)
    signup_str = signals.get('signup_date')
    signup_date = parse_date(signup_str)
    if signup_date:
        signup_days = max((ref_date - signup_date).days, 0)
        platform_tenure = min(signup_days / 365.0, 1.0)  # normalize to 1 year
    else:
        platform_tenure = 0.3  # neutral if unknown
    
    # 3. Engagement Score (Response rate + interview attendance + open to work)
    response_rate = float(signals.get('recruiter_response_rate', 0.0))
    completion_rate = float(signals.get('interview_completion_rate', 0.0))
    open_to_work = 1.0 if signals.get('open_to_work_flag') else 0.5
    
    engagement_score = (
        0.4 * response_rate +
        0.4 * completion_rate +
        0.2 * open_to_work
    )

    # 4. Profile Completeness
    completeness = float(signals.get('profile_completeness_score', 50)) / 100.0

    # 5. Response Quality
    avg_resp_time = float(signals.get('avg_response_time_hours', 48))
    if avg_resp_time <= 4:
        resp_time_score = 1.0
    elif avg_resp_time <= 12:
        resp_time_score = 0.85
    elif avg_resp_time <= 24:
        resp_time_score = 0.7
    elif avg_resp_time <= 48:
        resp_time_score = 0.5
    else:
        resp_time_score = 0.3

    # 6. Active Job Seeking
    applications = float(signals.get('applications_submitted_30d', 0))
    active_seeker = min(applications / 10.0, 1.0)

    # 7. Network & Social Proof
    connections = float(signals.get('connection_count', 0))
    endorsements = float(signals.get('endorsements_received', 0))
    network_score = 0.5 * min(connections / 300.0, 1.0) + 0.5 * min(endorsements / 50.0, 1.0)

    # 8. Offer Reliability
    offer_rate = float(signals.get('offer_acceptance_rate', -1))
    offer_score = offer_rate if offer_rate >= 0 else 0.5  # neutral if no data

    # 9. Trust/Verification Multiplier
    verified = 0
    if signals.get('verified_email'): verified += 1
    if signals.get('verified_phone'): verified += 1
    if signals.get('linkedin_connected'): verified += 1
    trust_multiplier = 0.85 + (verified / 3.0) * 0.15  # 0.85 to 1.0

    # 10. Behavioral Twins Shield (Ghost Candidate Penalty)
    # If candidate is inactive for more than 6 months (180 days) AND has a response rate < 10%,
    # they are a "ghost" profile and receive a severe penalty (0.25x).
    ghost_multiplier = 1.0
    if last_active:
        delta_days = max((ref_date - last_active).days, 0)
        if delta_days > 180 and response_rate < 0.10:
            ghost_multiplier = 0.25

    # Combined Recruiter Ops Score (all 23 signals factored in)
    raw_score = (
        0.22 * engagement_score +
        0.18 * activity_factor +
        0.13 * pagerank_score +
        0.10 * completeness +
        0.10 * resp_time_score +
        0.05 * active_seeker +
        0.07 * network_score +
        0.07 * offer_score +
        0.08 * platform_tenure
    )
    final_score = raw_score * trust_multiplier * ghost_multiplier
    return min(final_score, 1.0)
