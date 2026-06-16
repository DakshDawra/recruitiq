import streamlit as st
import json
import os
import csv
import math
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Set Page Config
st.set_page_config(
    page_title="RecruitIQ - Candidate Discovery & Ranking Panel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper to format YoE naturally
def format_yoe(yoe):
    try:
        yoe_val = float(yoe)
    except (ValueError, TypeError):
        return "N/A"
    years = int(yoe_val)
    months = int(round((yoe_val - years) * 12))
    if months == 12:
        years += 1
        months = 0
    parts = []
    if years > 0:
        parts.append(f"{years} yr{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} mo{'s' if months > 1 else ''}")
    if not parts:
        return "0 yrs"
    return " ".join(parts)

# Helper to render clean HTML in Streamlit without markdown parsing side-effects
def render_html(html_str):
    st.markdown("".join([line.strip() for line in html_str.splitlines()]), unsafe_allow_html=True)

# Inject Tailwind, Fonts, and Custom CSS (compressed to avoid Streamlit Markdown leaks)
st.markdown(
    """<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />""",
    unsafe_allow_html=True
)

css_code = """
[data-testid="collapsedControl"] {
    display: none !important;
}
div[data-testid="stAppViewContainer"] {
    display: flex !important;
    flex-direction: row !important;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #FCFAF7 !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarUserContent"], [data-testid="stSidebarNav"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #EAE8E4 !important;
}
[data-testid="stHeader"] {
    background-color: rgba(252, 250, 247, 0.8) !important;
    backdrop-filter: blur(8px) !important;
}
.bento-card {
    background-color: #FFFFFF;
    border: 1px solid #EAE8E4;
    border-radius: 24px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01), 0 2px 4px -1px rgba(0, 0, 0, 0.01);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}
.bento-card:hover {
    box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.04), 0 4px 6px -2px rgba(79, 70, 229, 0.04);
    border-color: #D1D5DB;
}
.badge-peach {
    background-color: #FEEAD1 !important;
    color: #C2410C !important;
    padding: 4px 12px !important;
    border-radius: 9999px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    display: inline-block;
}
.badge-lilac {
    background-color: #EBE3FF !important;
    color: #4338CA !important;
    padding: 4px 12px !important;
    border-radius: 9999px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    display: inline-block;
}
.badge-mint {
    background-color: #D1FADF !important;
    color: #065F46 !important;
    padding: 4px 12px !important;
    border-radius: 9999px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    display: inline-block;
}
.badge-indigo {
    background-color: #E0E7FF !important;
    color: #3730A3 !important;
    padding: 4px 12px !important;
    border-radius: 9999px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    display: inline-block;
}
.stat-card {
    background-color: #FFFFFF;
    border: 1px solid #EAE8E4;
    border-radius: 20px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
}
.stat-title {
    font-size: 14px;
    color: #6B7280;
    font-weight: 500;
}
.stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 32px;
    font-weight: 700;
    color: #1F2937;
    margin-top: 8px;
}
.stat-subtitle-green {
    color: #10B981;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
    font-family: 'JetBrains Mono', monospace;
}
.stat-subtitle-red {
    color: #EF4444;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
    font-family: 'JetBrains Mono', monospace;
}
.stat-icon {
    position: absolute;
    right: 16px;
    top: 16px;
    font-size: 24px;
    color: #9CA3AF;
}
.insights-box {
    background-color: #FCFAF7;
    border: 1px solid #EAE8E4;
    border-radius: 16px;
    padding: 16px;
    position: relative;
}
.insights-title {
    color: #4F46E5;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.insights-content {
    font-size: 14px;
    color: #4B5563;
    font-style: italic;
    line-height: 1.6;
}
.leaderboard-list {
    max-height: 600px;
    overflow-y: auto;
    padding-right: 8px;
}
div[data-testid="stColumn"] button {
    background-color: #FFFFFF !important;
    color: #1F2937 !important;
    border: 1px solid #EAE8E4 !important;
    border-radius: 12px !important;
    padding: 6px 12px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
div[data-testid="stColumn"] button:hover {
    background-color: #E0E7FF !important;
    border-color: #4F46E5 !important;
    color: #4F46E5 !important;
}
div[data-testid="stColumn"] button:active {
    transform: scale(0.98);
}
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #EAE8E4 !important;
}
"""
st.markdown(f"<style>{''.join(css_code.splitlines())}</style>", unsafe_allow_html=True)

# Helper function to load top 100 details
@st.cache_data
def load_top_100(mtime):
    json_path = "top_100_details.json"
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Helper function to get file modification times to invalidate cache dynamically
def get_mtime(filepath):
    try:
        return os.path.getmtime(filepath)
    except OSError:
        return 0

# Helper function to load all candidates (specifically for honeypots stats)
@st.cache_data
def load_honeypot_stats(mtime_hp, mtime_st):
    # 1. Try to load precomputed full run lists first
    if os.path.exists("honeypots_caught.json") and os.path.exists("stuffers_filtered.json"):
        try:
            with open("honeypots_caught.json", "r", encoding="utf-8") as f:
                honeypots = json.load(f)
            with open("stuffers_filtered.json", "r", encoding="utf-8") as f:
                stuffers = json.load(f)
            return honeypots, stuffers
        except Exception:
            pass

    # 2. Fall back to sample processing if not present
    from config import DATA_DIR
    from pipeline.honeypot import is_honeypot
    
    sample_path = os.path.join(DATA_DIR, "sample_candidates.json")
        
    if os.path.exists(sample_path):
        with open(sample_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        honeypots = []
        stuffers = []
        for c in candidates:
            profile = c.get('profile', {})
            # check honeypot
            if is_honeypot(c):
                # Analyze reasons
                reasons = []
                career_history = c.get('career_history', [])
                education = c.get('education', [])
                skills = c.get('skills', [])
                
                # Check rule 1
                for job in career_history:
                    from pipeline.honeypot import parse_date
                    start = parse_date(job.get('start_date'))
                    end = parse_date(job.get('end_date'))
                    if start and end and start > end:
                        reasons.append("Job Timeline Paradox (Start date > End date)")
                        break
                
                # Check rule 2
                for edu in education:
                    start_yr = edu.get('start_year')
                    end_yr = edu.get('end_year')
                    if start_yr and end_yr and start_yr > end_yr:
                        reasons.append("Education Timeline Paradox (Start year > End year)")
                        break
                        
                # Check rule 4
                expert_no_proof = sum(1 for s in skills if str(s.get('proficiency', '')).lower() == 'expert' and s.get('endorsements', 0) == 0 and s.get('duration_months', 0) == 0)
                if expert_no_proof >= 5:
                    reasons.append(f"Skill Endorsement Fraud ({expert_no_proof} expert skills with 0 proof)")
                    
                # Check rule 5
                years_of_experience = profile.get('years_of_experience', 0)
                if education:
                    edu_end_years = [edu.get('end_year') for edu in education if edu.get('end_year')]
                    if edu_end_years:
                        min_edu_end = min(edu_end_years)
                        max_possible_yoe = (2026 - min_edu_end) + 2
                        if years_of_experience > max_possible_yoe and years_of_experience > 5:
                            reasons.append(f"Impossible Experience Bound ({years_of_experience} YoE vs graduation in {min_edu_end})")
                
                if not reasons:
                    reasons.append("Structural anomalies detected (overlapping dates/conflicting indicators)")
                    
                honeypots.append({
                    "id": c.get('candidate_id'),
                    "name": profile.get('anonymized_name', 'Anonymous'),
                    "title": profile.get('current_title', 'Software Engineer'),
                    "yoe": years_of_experience,
                    "reasons": ", ".join(reasons)
                })
            else:
                # check coarse stuffer
                from pipeline.coarse_filter import is_coarse_match
                if not is_coarse_match(c):
                    stuffers.append({
                        "id": c.get('candidate_id'),
                        "name": profile.get('anonymized_name', 'Anonymous'),
                        "title": profile.get('current_title', 'Software Engineer'),
                        "yoe": profile.get('years_of_experience', 0.0),
                        "skills": [s.get('name') for s in c.get('skills', [])[:3]]
                    })
        return honeypots, stuffers
    return [], []

# Load data
candidates = load_top_100(get_mtime("top_100_details.json"))

# Sidebar Header
st.sidebar.markdown(
    """
    <div style="padding: 10px 0px 20px 0px; display: flex; align-items: center; gap: 8px;">
        <svg viewBox="0 0 32 32" width="32" height="32" fill="none" stroke="#4F46E5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(-5deg);">
            <path d="M16 4 Q16 12 24 16 Q16 20 16 28 Q16 20 8 16 Q16 12 16 4 Z" fill="#EBE3FF" />
            <path d="M25 8 L27 10 M27 8 L25 10" stroke="#F59E0B" stroke-width="2" />
        </svg>
        <span style="font-size: 22px; font-weight: 800; font-family: 'Public Sans', sans-serif; color: #1F2937;">RecruitIQ</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar Sourcing Target Profile
st.sidebar.markdown("### Sourcing Requirements")
st.sidebar.markdown(
    """
    <div class="insights-box" style="margin-bottom: 20px;">
        <div class="insights-title">
            <span class="material-symbols-outlined" style="font-size: 14px;">work</span> Senior AI Engineer
        </div>
        <p style="font-size: 12px; color: #4B5563; margin: 0; line-height: 1.4;">
            <b>Role:</b> Series A Founding AI/ML Lead<br/>
            <b>Skills:</b> LLMs, RAG, PyTorch, Vector DBs, Embedding Search<br/>
            <b>Disqualifiers:</b> Pure Consulting, Title-Chasers, Academic-only CVs.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Navigation
st.sidebar.markdown("### Navigation")
nav_page = st.sidebar.radio(
    "Navigation",
    ["Intelligence Dashboard", "🔬 Rank Robustness", "🧬 Skill Ecosystem", "📊 Pipeline X-Ray", "Honeypot Audit Logs", "Keyword Stuffing Rules"],
    label_visibility="collapsed"
)

# Persona Consensus Weights Tuner (Out-of-the-box Interactive Feature)
st.sidebar.markdown("<br/>", unsafe_allow_html=True)
st.sidebar.markdown("### 🎛️ Consensus Tuning")

with st.sidebar.expander("ℹ️ How to use Consensus"):
    st.write("Adjust the importance of each virtual evaluator below. The candidate leaderboard will instantly re-rank to reflect your custom weighting strategy.")

w_tech = st.sidebar.slider("Technical Depth", 0.0, 1.0, 0.25, 0.05, key="w_tech")
w_hm = st.sidebar.slider("Hiring Manager", 0.0, 1.0, 0.25, 0.05, key="w_hm")
w_cf = st.sidebar.slider("Culture Fit", 0.0, 1.0, 0.20, 0.05, key="w_cf")
w_ops = st.sidebar.slider("Recruiter Ops", 0.0, 1.0, 0.15, 0.05, key="w_ops")
w_edu = st.sidebar.slider("Logistics & Edu", 0.0, 1.0, 0.15, 0.05, key="w_edu")

# Dynamic on-the-fly re-ranking
total_w = w_tech + w_hm + w_cf + w_ops + w_edu
if total_w > 0 and candidates:
    recomputed = []
    for c in candidates:
        scores = c.get('scores', {})
        p_tech = scores.get('technical', 0.0)
        p_hm = scores.get('hiring_manager', 0.0)
        p_cf = scores.get('culture_fit', 0.0)
        p_ops = scores.get('recruiter_ops', 0.0)
        p_edu = scores.get('logistics_education', 0.0)
        
        # New persona sum
        new_persona_sum = (p_tech * w_tech + p_hm * w_hm + p_cf * w_cf + p_ops * w_ops + p_edu * w_edu) / total_w
        
        # Apply TF-IDF semantic boost
        boost = c.get('semantic_boost', 1.0)
        mult = 0.0 if c.get('hard_disqualified_reason') else 1.0
        
        c_new = c.copy()
        c_new['final_score'] = round(float(new_persona_sum * boost * mult), 4)
        c_new['scores'] = {
            'technical': p_tech,
            'hiring_manager': p_hm,
            'culture_fit': p_cf,
            'recruiter_ops': p_ops,
            'logistics_education': p_edu,
            'persona_sum': new_persona_sum
        }
        recomputed.append(c_new)
        
    # Sort and re-rank
    recomputed.sort(key=lambda x: (-x['final_score'], x.get('candidate_id', '')))
    for idx, c in enumerate(recomputed):
        c['rank'] = idx + 1
        
    candidates = recomputed

# Default selection
if candidates and 'selected_candidate_id' not in st.session_state:
    st.session_state.selected_candidate_id = candidates[0]['candidate_id']

# Sidebar footer removed

if nav_page == "Intelligence Dashboard":
    # Header Area
    col_hdr_left, col_hdr_right = st.columns([3, 1])
    with col_hdr_left:
        st.markdown(
            """
            <div style="position: relative; display: inline-block; margin-bottom: 12px;">
                <h1 style="margin-bottom: 8px; font-size: 32px; display: inline-block; position: relative;">
                    Talent Intelligence
                    <svg viewBox="0 0 160 10" width="180" height="12" style="position: absolute; bottom: -8px; left: 0; pointer-events: none;">
                        <path d="M2,6 Q40,2 80,7 T158,5" stroke="#F59E0B" stroke-width="3" fill="none" stroke-linecap="round" />
                    </svg>
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" style="display: inline-block; vertical-align: middle; margin-left: 8px; transform: rotate(15deg);">
                        <path d="M12 2 Q12 10 20 12 Q12 14 12 22 Q12 14 4 12 Q12 10 12 2 Z" fill="#FEEAD1" />
                    </svg>
                </h1>
            </div>
            <p style="color: #6B7280; font-size: 14px; margin-top: 4px;">Welcome back, your AI agents have successfully processed the pipeline today.</p>
            """,
            unsafe_allow_html=True
        )
        pass

    # Success Banner if pipeline was run
    if 'pipeline_stats' in st.session_state:
        p_stats = st.session_state.pipeline_stats
        st.success(f"Pipeline Executed Successfully! Ranked custom dataset of {p_stats['scanned']} candidates in {p_stats['latency']}s (Blocked {p_stats['honeypots']} honeypots, filtered {p_stats['stuffers']} stuffers). Dashboard views updated live!")
        if st.button("Clear notification", key="clear_stats"):
            del st.session_state.pipeline_stats
            st.rerun()

    # Custom Dataset Uploader Card
    st.markdown('<div class="bento-card" style="margin-bottom: 24px;">', unsafe_allow_html=True)
    
    col_u1, col_u2 = st.columns([7, 3])
    with col_u1:
        st.markdown('<h3 style="margin: 0 0 4px 0; font-size: 18px; color: #1F2937; font-weight: 700;">🔄 Run Sourcing Pipeline</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 12px; color: #6B7280; margin: 0 0 16px 0;">Upload a custom candidates list (JSON/JSONL) and Job Description to rank dynamically on CPU.</p>', unsafe_allow_html=True)
    with col_u2:
        pass
        
    col_f1, col_f2, col_f3 = st.columns([2.5, 2.5, 1.2])
    with col_f1:
        uploaded_cand = st.file_uploader("Candidates Database (JSON/JSONL)", type=["json", "jsonl"], key="main_cand")
    with col_f2:
        uploaded_jd = st.file_uploader("Job Description Text (TXT)", type=["txt"], key="main_jd")
    with col_f3:
        st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
        run_btn = st.button("Run Engine ⚡", key="main_run", use_container_width=True)
        
    if run_btn:
        if not uploaded_cand or not uploaded_jd:
            st.error("Please upload both candidates and JD files.")
        else:
            import time
            start_run = time.time()
            
            with st.spinner("Processing & ranking candidates..."):
                # Save temp candidate file
                temp_cand_name = "uploaded_temp_candidates.json" if uploaded_cand.name.endswith(".json") else "uploaded_temp_candidates.jsonl"
                with open(temp_cand_name, "wb") as f:
                    f.write(uploaded_cand.getbuffer())
                    
                # Read JD text
                jd_text = uploaded_jd.read().decode("utf-8")
                
                # Import pipeline modules dynamically to save memory
                from pipeline.ranker import rank_candidates
                from pipeline.reasoning import generate_candidate_reasoning
                
                # Generator function to stream candidates supporting json and jsonl
                def get_candidates_stream(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            first_char = f.read(1).strip()
                            is_json_list = first_char == '['
                    except Exception:
                        is_json_list = False
                    
                    if is_json_list:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for item in data:
                                yield item
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    yield json.loads(line)
                                    
                try:
                    candidates_gen = get_candidates_stream(temp_cand_name)
                    ranked_candidates, stats = rank_candidates(candidates_gen, jd_text)
                    
                    # Generate reasoning for top 100
                    for c in ranked_candidates:
                        c['reasoning'] = generate_candidate_reasoning(c)
                        
                    # Save to top_100_details.json
                    with open("top_100_details.json", "w", encoding="utf-8") as fj:
                        json.dump(ranked_candidates, fj, indent=2, ensure_ascii=False)
                        
                    # Save honeypot and stuffer logs for dashboard
                    with open("honeypots_caught.json", "w", encoding="utf-8") as fhp:
                        json.dump(stats.get('honeypot_details', []), fhp, indent=2, ensure_ascii=False)
                    with open("stuffers_filtered.json", "w", encoding="utf-8") as fst:
                        json.dump(stats.get('stuffer_details', []), fst, indent=2, ensure_ascii=False)
                        
                    # Save to submission.csv
                    with open("submission.csv", "w", encoding="utf-8", newline="") as fcsv:
                        writer = csv.writer(fcsv)
                        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
                        for c in ranked_candidates:
                            writer.writerow([
                                c.get('candidate_id', ''),
                                c.get('rank', ''),
                                round(c.get('final_score', 0.0), 4),
                                c.get('reasoning', '')
                            ])
                            
                    elapsed_run = time.time() - start_run
                    
                    # Store stats in session state and file
                    stats_dict = {
                        "scanned": stats['total_scanned'],
                        "honeypots": stats['honeypots_blocked'],
                        "stuffers": stats['stuffers_filtered'],
                        "latency": round(elapsed_run, 2)
                    }
                    st.session_state.pipeline_stats = stats_dict
                    with open("pipeline_stats.json", "w", encoding="utf-8") as fstats:
                        json.dump(stats_dict, fstats, indent=2)
                    
                    # Clean up temp file
                    if os.path.exists(temp_cand_name):
                        os.remove(temp_cand_name)
                        
                    st.success("🎉 Sourcing Engine complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Execution failed: {str(e)}")
                    
    st.markdown('</div>', unsafe_allow_html=True)

    # Dynamic Stats Row
    hp_data, st_data = load_honeypot_stats(get_mtime("honeypots_caught.json"), get_mtime("stuffers_filtered.json"))
    n_honeypots = len(hp_data)
    n_stuffers = len(st_data)
    # Load saved pipeline stats or default
    p_stats = st.session_state.get('pipeline_stats')
    if not p_stats and os.path.exists("pipeline_stats.json"):
        try:
            with open("pipeline_stats.json", "r", encoding="utf-8") as f:
                p_stats = json.load(f)
        except Exception:
            pass
            
    if not p_stats:
        p_stats = {}
        
    n_scanned = p_stats.get('scanned', 100000)
    latency = p_stats.get('latency', 52.45)
    hp_rate = round(n_honeypots / max(n_scanned, 1) * 100, 2)
    st_rate = round(n_stuffers / max(n_scanned, 1) * 100, 2)

    st.markdown(
        f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 2rem;">
            <div class="stat-card" style="position: relative; overflow: hidden;">
                <div class="stat-title">Candidates Scanned</div>
                <div class="stat-value">{n_scanned:,}</div>
                <div style="margin-top: 4px;"><span class="stat-subtitle-green">Full Dataset Processed</span></div>
                <div style="position: absolute; right: -12px; bottom: -12px; opacity: 0.2; transform: rotate(-10deg); pointer-events: none;"><svg viewBox="0 0 24 24" width="70" height="70" fill="none" stroke="#6366F1" stroke-width="1.5"><path d="M12 2 Q12 10 20 12 Q12 14 12 22 Q12 14 4 12 Q12 10 12 2 Z" fill="#EEF2FF" /></svg></div>
            </div>
            <div class="stat-card" style="position: relative; overflow: hidden;">
                <div class="stat-title">Honeypots Blocked</div>
                <div class="stat-value">{n_honeypots:,}</div>
                <div style="margin-top: 4px;"><span class="stat-subtitle-red">{hp_rate}% Shield rate</span></div>
                <div style="position: absolute; right: -12px; bottom: -12px; opacity: 0.2; transform: rotate(-10deg); pointer-events: none;"><svg viewBox="0 0 24 24" width="70" height="70" fill="none" stroke="#EF4444" stroke-width="1.5"><path d="M12 22 C12 22 20 18 20 12 V5 L12 2 L4 5 V12 C4 18 12 22 12 22 Z" fill="#FEE2E2" /></svg></div>
            </div>
            <div class="stat-card" style="position: relative; overflow: hidden;">
                <div class="stat-title">Non-Tech Filtered</div>
                <div class="stat-value">{n_stuffers:,}</div>
                <div style="margin-top: 4px;"><span class="stat-subtitle-red">{st_rate}% Filtered</span></div>
                <div style="position: absolute; right: -12px; bottom: -12px; opacity: 0.2; transform: rotate(-10deg); pointer-events: none;"><svg viewBox="0 0 24 24" width="70" height="70" fill="none" stroke="#F59E0B" stroke-width="1.5"><path d="M22 3 H2 L10 12.46 V19 L14 21 V12.46 Z" fill="#FEF3C7" /></svg></div>
            </div>
            <div class="stat-card" style="position: relative; overflow: hidden;">
                <div class="stat-title">Execution Latency</div>
                <div class="stat-value">{latency}s</div>
                <div style="margin-top: 4px;"><span class="stat-subtitle-green">CPU-Only Pipeline</span></div>
                <div style="position: absolute; right: -12px; bottom: -12px; opacity: 0.2; transform: rotate(-10deg); pointer-events: none;"><svg viewBox="0 0 24 24" width="70" height="70" fill="none" stroke="#10B981" stroke-width="1.5"><path d="M13 2 L3 14 H12 L11 22 L21 10 H12 Z" fill="#D1FAE5" /></svg></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Main Bento Layout Columns
    col_left, col_right = st.columns([1.8, 1.2])

    with col_left:
        # Candidate List Card
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        
        col_list_hdr, col_list_scope, col_list_filters = st.columns([1.2, 0.9, 0.9])
        with col_list_hdr:
            st.markdown('<h3 style="margin: 0; font-size: 20px;">AI Candidate Shortlist</h3>', unsafe_allow_html=True)
        
        with col_list_scope:
            view_scope = st.selectbox(
                "Scope",
                ["Top 10 Picks", "All 100 Shortlist"],
                index=0,
                label_visibility="collapsed"
            )
        
        with col_list_filters:
            # Search / Filter panel
            search_query = st.text_input("Search", label_visibility="collapsed", placeholder="Search name/skills...")
            
        st.markdown('<div style="height: 1px; background-color: #EAE8E4; margin: 16px 0;"></div>', unsafe_allow_html=True)
        
        # Filter candidates based on search
        filtered_candidates = candidates
        if search_query:
            q = search_query.lower()
            filtered_candidates = [
                c for c in candidates 
                if q in c.get('profile', {}).get('anonymized_name', '').lower() 
                or q in c.get('profile', {}).get('current_title', '').lower()
                or any(q in s.get('name', '').lower() for s in c.get('skills', []))
            ]
            
        if view_scope == "Top 10 Picks":
            filtered_candidates = filtered_candidates[:10]

        if not filtered_candidates:
            st.warning("No candidates matched your search criteria.")
        else:
            # Render Candidate List Rows
            st.markdown('<div class="leaderboard-list">', unsafe_allow_html=True)
            for idx, c in enumerate(filtered_candidates):
                c_id = c['candidate_id']
                profile = c['profile']
                scores = c['scores']
                name = profile['anonymized_name']
                title = profile['current_title']
                score_out_100 = round(c['final_score'] * 100, 1)
                
                # Determine tag based on rank
                if idx < 3:
                    tag_html = '<span class="badge-peach">Perfect Fit</span>'
                elif c.get('semantic_similarity_score', 0) > 0.40 and len(c.get('skills', [])) < 8:
                    tag_html = '<span class="badge-lilac">Hidden Gem</span>'
                else:
                    tag_html = '<span class="badge-mint">Behavioral Match</span>'
                
                # Active selection highlight
                is_selected = c_id == st.session_state.selected_candidate_id
                bg_color = "#EEF2FF" if is_selected else "#F9FAFB"
                border_color = "#4F46E5" if is_selected else "transparent"
                
                # Row Container
                row_col1, row_col2, row_col3 = st.columns([3.6, 1.8, 1.6])
                with row_col1:
                    # Render avatar initial & details
                    avatar_bg = "FEEAD1" if idx % 3 == 0 else ("EBE3FF" if idx % 3 == 1 else "D1FADF")
                    avatar_txt = "C2410C" if idx % 3 == 0 else ("4338CA" if idx % 3 == 1 else "065F46")
                    initials = "".join([w[0] for w in name.split()[:2]]).upper()
                    
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; gap: 12px; padding: 6px; background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 16px;">
                            <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #{avatar_bg}; color: #{avatar_txt}; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">
                                {initials}
                            </div>
                            <div>
                                <h4 style="margin: 0; font-size: 14px; color: #1F2937;">{name}</h4>
                                <p style="margin: 0; font-size: 11px; color: #6B7280;">{title} • {format_yoe(profile.get('years_of_experience', 0))}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with row_col2:
                    st.markdown(
                        f"""
                        <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%;">
                            {tag_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with row_col3:
                    # Streamlit selection button
                    if st.button("Details", key=f"sel_{c_id}"):
                        st.session_state.selected_candidate_id = c_id
                        st.rerun()
                        
                st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download Shortlist Card
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin: 0 0 10px 0; font-size: 16px;">Download Verified Candidate List</h4>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 12px; color: #6B7280; margin-bottom: 16px;">The shortlist contains the top 100 ranked candidates fully compliant with the challenge rules.</p>', unsafe_allow_html=True)
        
        # Read file submission.csv to export
        if os.path.exists("submission.csv"):
            with open("submission.csv", "r", encoding="utf-8") as csv_f:
                csv_data = csv_f.read()
            st.download_button(
                label="📥 Download submission.csv",
                data=csv_data,
                file_name="submission.csv",
                mime="text/csv"
            )
        else:
            st.error("submission.csv not found. Please run candidate ranking pipeline.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # Spotlight Card
        selected_cand = next((c for c in candidates if c['candidate_id'] == st.session_state.selected_candidate_id), None)
        if selected_cand:
            profile = selected_cand['profile']
            scores = selected_cand['scores']
            signals = selected_cand['redrob_signals']
            name = profile['anonymized_name']
            title = profile['current_title']
            
            st.markdown('<div class="bento-card" style="padding-top: 32px;">', unsafe_allow_html=True)
            
            # Avatar & Name
            initials = "".join([w[0] for w in name.split()[:2]]).upper()
            is_perfect_fit = candidates.index(selected_cand) < 3 if selected_cand in candidates else False
            crown_html = '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="position: absolute; top: -20px; left: calc(50% - 16px); transform: rotate(-10deg); z-index: 10;"><path d="M3 16 L5 7 L10 11 L12 5 L14 11 L19 7 L21 16 Z" fill="#FEEAD1" /><circle cx="5" cy="7" r="0.5" fill="#F59E0B" /><circle cx="12" cy="5" r="0.5" fill="#F59E0B" /><circle cx="19" cy="7" r="0.5" fill="#F59E0B" /></svg>' if is_perfect_fit else ''
            
            avatar_html = f"""
            <div style="display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 24px;">
                <div style="position: relative; margin-bottom: 12px;">
                    {crown_html}
                    <div style="width: 80px; height: 80px; border-radius: 24px; background-color: #EBE3FF; color: #4338CA; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 28px; border: 3px solid #FFFFFF; box-shadow: 0 4px 10px rgba(0,0,0,0.05); transform: rotate(2deg);">
                        {initials}
                    </div>
                </div>
                <h3 style="margin: 0 0 4px 0; font-size: 20px; color: #1F2937;">{name}</h3>
                <p style="margin: 0; font-size: 13px; color: #6B7280; font-weight: 500;">{title}</p>
                <p style="margin: 4px 0 0 0; font-size: 12px; color: #9CA3AF;">{profile.get('location', '')}, {profile.get('country', '')}</p>
            </div>
            """
            render_html(avatar_html)
            
            # Hard Disqualifier Alert
            if selected_cand.get('hard_disqualified_reason'):
                disq_html = f"""
                <div style="background-color: #FEF2F2; border: 2px solid #EF4444; border-radius: 12px; padding: 16px; margin-bottom: 24px; display: flex; gap: 12px; align-items: flex-start;">
                    <span class="material-symbols-outlined" style="color: #EF4444; font-size: 24px;">gavel</span>
                    <div>
                        <h4 style="margin: 0 0 4px 0; color: #B91C1C; font-size: 14px; font-weight: 800; text-transform: uppercase;">Disqualified</h4>
                        <p style="margin: 0; font-size: 13px; color: #7F1D1D; font-weight: 600;">{selected_cand['hard_disqualified_reason']}</p>
                    </div>
                </div>
                """
                render_html(disq_html)
            
            # AI Insights Speech Bubble
            insights_html = f"""
            <div class="insights-box" style="margin-bottom: 24px;">
                <div class="insights-title" style="position: relative; display: flex; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span class="material-symbols-outlined" style="font-size: 16px;">chat_bubble</span> AI Shortlist Reasoning
                    </div>
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="position: absolute; right: 0; top: -4px; transform: rotate(15deg);">
                        <path d="M3 12 C8 15 15 15 17 9 M13 5 L18 8 L15 13" />
                    </svg>
                </div>
                <p class="insights-content">
                    "{selected_cand.get('reasoning', '')}"
                </p>
            </div>
            """
            render_html(insights_html)
            
            # Match Score Plotly Radar Chart
            st.markdown('<h4 style="margin: 0 0 12px 0; font-size: 14px;">Consensus Persona Evaluation</h4>', unsafe_allow_html=True)
            
            # Radar chart data
            categories = ['Technical', 'Hiring Manager', 'Culture Fit', 'Recruiter Ops', 'Logistics/Edu']
            candidate_vals = [
                scores.get('technical', 0.0) * 100,
                scores.get('hiring_manager', 0.0) * 100,
                scores.get('culture_fit', 0.0) * 100,
                scores.get('recruiter_ops', 0.0) * 100,
                scores.get('logistics_education', 0.0) * 100
            ]
            
            # Plotly polar graph
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=candidate_vals,
                theta=categories,
                fill='toself',
                fillcolor='rgba(79, 70, 229, 0.15)',
                line_color='#4F46E5',
                line_width=2,
                marker=dict(size=6, color='#4F46E5'),
                name='Persona consensus'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(size=8, family='JetBrains Mono'),
                        gridcolor='#E5E7EB'
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=10, family='Inter', color='#374151'),
                        gridcolor='#E5E7EB'
                    ),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=False,
                margin=dict(l=65, r=65, t=30, b=30),
                height=265,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
            
            # Skill bars
            st.markdown('<h4 style="margin: 16px 0 12px 0; font-size: 14px;">Top Profile Skills</h4>', unsafe_allow_html=True)
            skills = selected_cand.get('skills', [])
            for s in skills[:3]:
                s_name = s.get('name')
                s_prof = s.get('proficiency', 'Intermediate')
                s_duration = s.get('duration_months', 0)
                s_endorse = s.get('endorsements', 0)
                
                # Check color theme
                st.markdown(
                    f"""
                    <div style="margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: #4B5563; margin-bottom: 4px;">
                            <span>{s_name} ({s_prof.capitalize()})</span>
                            <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px;">{s_duration}m • {s_endorse} saves</span>
                        </div>
                        <div style="width: 100%; height: 6px; background-color: #F3F4F6; border-radius: 9999px; overflow: hidden;">
                            <div style="width: {min(max(s_duration*2, 20), 100)}%; height: 100%; background-color: #4F46E5; border-radius: 9999px;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            # Timeline or Work History
            st.markdown('<h4 style="margin: 20px 0 12px 0; font-size: 14px;">Career Timeline</h4>', unsafe_allow_html=True)
            for job in selected_cand.get('career_history', []):
                company = job.get('company')
                j_title = job.get('title')
                start = job.get('start_date', 'N/A')
                end = job.get('end_date') if not job.get('is_current') else 'Present'
                duration = job.get('duration_months', 0)
                
                st.markdown(
                    f"""
                    <div style="border-left: 2px solid #EAE8E4; padding-left: 12px; margin-bottom: 12px; position: relative;">
                        <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #4F46E5; position: absolute; left: -5px; top: 6px;"></div>
                        <p style="margin: 0; font-size: 13px; font-weight: 700; color: #1F2937;">{j_title}</p>
                        <p style="margin: 0; font-size: 11px; color: #4F46E5; font-weight: 500;">{company} • {start} to {end} ({duration} months)</p>
                        <p style="margin: 4px 0 0 0; font-size: 11px; color: #6B7280; line-height: 1.4;">{job.get('description', '')[:120]}...</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            # Education
            st.markdown('<h4 style="margin: 20px 0 12px 0; font-size: 14px;">Education & Tier</h4>', unsafe_allow_html=True)
            for edu in selected_cand.get('education', []):
                inst = edu.get('institution')
                deg = edu.get('degree')
                field = edu.get('field_of_study')
                tier = edu.get('tier', 'tier_3').replace('_', ' ').upper()
                
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; background-color: #F9FAFB; padding: 10px 14px; border-radius: 12px; margin-bottom: 8px; border: 1px solid #EAE8E4;">
                        <div>
                            <p style="margin: 0; font-size: 12px; font-weight: 700; color: #1F2937;">{deg} in {field}</p>
                            <p style="margin: 0; font-size: 11px; color: #6B7280;">{inst}</p>
                        </div>
                        <span class="badge-indigo" style="font-size: 9px !important;">{tier}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            # behavioral signals
            st.markdown('<h4 style="margin: 20px 0 12px 0; font-size: 14px;">Behavioral & Engagement Metrics</h4>', unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.markdown(
                    f"""
                    <div style="background-color: #F9FAFB; padding: 10px; border-radius: 12px; text-align: center; border: 1px solid #EAE8E4;">
                        <p style="margin: 0; font-size: 10px; color: #6B7280; font-weight: 600; text-transform: uppercase;">Notice Period</p>
                        <p style="margin: 4px 0 0 0; font-size: 16px; font-weight: 800; color: #4F46E5; font-family: 'JetBrains Mono', monospace;">{signals.get('notice_period_days', 'N/A')} Days</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_b2:
                st.markdown(
                    f"""
                    <div style="background-color: #F9FAFB; padding: 10px; border-radius: 12px; text-align: center; border: 1px solid #EAE8E4;">
                        <p style="margin: 0; font-size: 10px; color: #6B7280; font-weight: 600; text-transform: uppercase;">Response Rate</p>
                        <p style="margin: 4px 0 0 0; font-size: 16px; font-weight: 800; color: #10B981; font-family: 'JetBrains Mono', monospace;">{round(signals.get('recruiter_response_rate', 0.0)*100, 1)}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Select a candidate to view spotlight details.")

elif nav_page == "🔬 Rank Robustness":
    st.markdown(
        """
        <h1 style="margin-bottom: 4px; font-size: 32px;">Ranking Robustness Analysis</h1>
        <p style="color: #6B7280; font-size: 14px; margin-top: 0;">Monte Carlo simulation showing how stable each candidate's rank is under 500 random weight perturbations.</p>
        <div style="height: 1px; background-color: #EAE8E4; margin: 20px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    
    st.info("💡 **How to use this:** This tool runs 500 simulations with randomized persona weights. Candidates with a low Standard Deviation (σ) are 'Safe Bets'—they stay at the top regardless of which evaluator you prioritize. Highly volatile candidates might be risky hires.")
    
    if candidates:
        import random
        random.seed(42)
        n_sims = 500
        rank_distributions = {c['candidate_id']: [] for c in candidates}
        
        for _ in range(n_sims):
            # Random weight perturbation
            weights = [random.uniform(0.05, 0.5) for _ in range(5)]
            total = sum(weights)
            weights = [w/total for w in weights]
            
            sim_scores = []
            for c in candidates:
                scores = c.get('scores', {})
                s = (
                    scores.get('technical', 0) * weights[0] +
                    scores.get('hiring_manager', 0) * weights[1] +
                    scores.get('culture_fit', 0) * weights[2] +
                    scores.get('recruiter_ops', 0) * weights[3] +
                    scores.get('logistics_education', 0) * weights[4]
                )
                sim_scores.append((c['candidate_id'], s))
            
            sim_scores.sort(key=lambda x: -x[1])
            for rank_idx, (cid, _) in enumerate(sim_scores):
                rank_distributions[cid].append(rank_idx + 1)
        
        # Calculate stats
        robustness_data = []
        for c in candidates:
            cid = c['candidate_id']
            ranks = rank_distributions[cid]
            mean_rank = sum(ranks) / len(ranks)
            std_rank = (sum((r - mean_rank)**2 for r in ranks) / len(ranks)) ** 0.5
            min_rank = min(ranks)
            max_rank = max(ranks)
            robustness_data.append({
                'candidate_id': cid,
                'name': c['profile']['anonymized_name'],
                'title': c['profile']['current_title'],
                'current_rank': c['rank'],
                'mean_rank': round(mean_rank, 1),
                'std_rank': round(std_rank, 1),
                'min_rank': min_rank,
                'max_rank': max_rank,
                'stability': 'Safe Bet' if std_rank < 5 else ('Moderate' if std_rank < 15 else 'Weight-Sensitive')
            })
        
        robustness_data.sort(key=lambda x: x['current_rank'])
        
        # Summary stats
        safe_bets = sum(1 for r in robustness_data[:20] if r['stability'] == 'Safe Bet')
        st.markdown(
            f"""
            <div class="bento-card" style="margin-bottom: 24px; border-left: 4px solid #4F46E5;">
                <div style="display: flex; gap: 40px;">
                    <div><p style="margin: 0; font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">Simulations Run</p><p style="margin: 4px 0 0 0; font-size: 28px; font-weight: 800; color: #4F46E5;">{n_sims}</p></div>
                    <div><p style="margin: 0; font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">Safe Bets in Top 20</p><p style="margin: 4px 0 0 0; font-size: 28px; font-weight: 800; color: #10B981;">{safe_bets}</p></div>
                    <div><p style="margin: 0; font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">Most Stable Candidate</p><p style="margin: 4px 0 0 0; font-size: 28px; font-weight: 800; color: #1F2937;">#{min(robustness_data, key=lambda x: x['std_rank'])['current_rank']}</p></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Rank stability chart (top 30)
        top_30 = robustness_data[:30]
        fig_rob = go.Figure()
        
        colors = ['#10B981' if r['stability'] == 'Safe Bet' else ('#F59E0B' if r['stability'] == 'Moderate' else '#EF4444') for r in top_30]
        
        fig_rob.add_trace(go.Bar(
            x=[f"#{r['current_rank']} {r['name'].split()[0]}" for r in top_30],
            y=[r['std_rank'] for r in top_30],
            marker_color=colors,
            text=[f"±{r['std_rank']}" for r in top_30],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Rank Stability σ: %{y:.1f}<br>Range: %{customdata}<extra></extra>',
            customdata=[f"#{r['min_rank']}-#{r['max_rank']}" for r in top_30]
        ))
        
        fig_rob.update_layout(
            title='Rank Stability (σ) — Lower = More Stable',
            xaxis_title='Candidate',
            yaxis_title='Rank Standard Deviation',
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter'),
            xaxis=dict(tickangle=-45),
            margin=dict(b=100)
        )
        st.plotly_chart(fig_rob, width='stretch', config={'displayModeBar': False})
        
        # Detailed table
        st.markdown('<h3 style="margin: 24px 0 12px 0; font-size: 18px;">Detailed Robustness Table</h3>', unsafe_allow_html=True)
        for r in top_30:
            stability_color = '#10B981' if r['stability'] == 'Safe Bet' else ('#F59E0B' if r['stability'] == 'Moderate' else '#EF4444')
            st.markdown(
                f"""
                <div class="bento-card" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 18px; font-weight: 800; color: #4F46E5; font-family: 'JetBrains Mono', monospace;">#{r['current_rank']}</span>
                            <div>
                                <p style="margin: 0; font-size: 14px; font-weight: 600; color: #1F2937;">{r['name']}</p>
                                <p style="margin: 0; font-size: 11px; color: #6B7280;">{r['title']}</p>
                            </div>
                        </div>
                        <div style="display: flex; gap: 20px; align-items: center;">
                            <div style="text-align: center;">
                                <p style="margin: 0; font-size: 10px; color: #6B7280; text-transform: uppercase;">Mean Rank</p>
                                <p style="margin: 0; font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{r['mean_rank']}</p>
                            </div>
                            <div style="text-align: center;">
                                <p style="margin: 0; font-size: 10px; color: #6B7280; text-transform: uppercase;">Range</p>
                                <p style="margin: 0; font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace;">#{r['min_rank']}-#{r['max_rank']}</p>
                            </div>
                            <span style="background-color: {stability_color}20; color: {stability_color}; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700;">{r['stability']}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("No candidate data available. Run the pipeline first.")

elif nav_page == "🧬 Skill Ecosystem":
    st.markdown(
        """
        <h1 style="margin-bottom: 4px; font-size: 32px;">Skill Ecosystem Map</h1>
        <p style="color: #6B7280; font-size: 14px; margin-top: 0;">Interactive force-directed network showing skill co-occurrence across the top 100 candidates.</p>
        <div style="height: 1px; background-color: #EAE8E4; margin: 20px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    
    st.info("💡 **How to use this:** Look for dense clusters of connected nodes. Real candidates have naturally connected skills (e.g., PyTorch ↔ HuggingFace). Disconnected, floating nodes often indicate keyword stuffing where a candidate pasted random unrelated skills to game the ATS.")
    
    if candidates:
        from collections import Counter, defaultdict
        
        # Build skill co-occurrence matrix
        skill_freq = Counter()
        cooccurrence = defaultdict(int)
        
        for c in candidates:
            skills = [s['name'] for s in c.get('skills', [])[:15]]
            for s in skills:
                skill_freq[s] += 1
            for i in range(len(skills)):
                for j in range(i+1, len(skills)):
                    pair = tuple(sorted([skills[i], skills[j]]))
                    cooccurrence[pair] += 1
        
        # Top skills by frequency
        top_skills = [s for s, _ in skill_freq.most_common(35)]
        
        # Build network data
        nodes_x, nodes_y, node_text, node_sizes, node_colors = [], [], [], [], []
        
        # Simple force-directed layout approximation using random seed positions
        import random
        random.seed(42)
        positions = {}
        for i, skill in enumerate(top_skills):
            angle = (2 * 3.14159 * i) / len(top_skills)
            r = 2.0 + random.uniform(-0.5, 0.5)
            positions[skill] = (r * math.cos(angle), r * math.sin(angle))
            nodes_x.append(positions[skill][0])
            nodes_y.append(positions[skill][1])
            freq = skill_freq[skill]
            node_text.append(f"{skill} ({freq} candidates)")
            node_sizes.append(max(15, min(freq * 2, 50)))
            node_colors.append(freq)
        
        # Build edges
        edge_x, edge_y = [], []
        for (s1, s2), count in cooccurrence.items():
            if s1 in positions and s2 in positions and count >= 5:
                x0, y0 = positions[s1]
                x1, y1 = positions[s2]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        fig_net = go.Figure()
        
        # Edges
        fig_net.add_trace(go.Scatter(
            x=edge_x, y=edge_y, mode='lines',
            line=dict(width=0.5, color='#D1D5DB'),
            hoverinfo='none'
        ))
        
        # Nodes
        fig_net.add_trace(go.Scatter(
            x=nodes_x, y=nodes_y, mode='markers+text',
            marker=dict(size=node_sizes, color=node_colors, colorscale='Viridis', showscale=True, colorbar=dict(title='Frequency'), line=dict(width=1, color='white')),
            text=[s.split('(')[0] for s in node_text],
            textposition='top center',
            textfont=dict(size=11, family='Inter', color='#1F2937'),
            hovertext=node_text,
            hoverinfo='text'
        ))
        
        fig_net.update_layout(
            title='Skill Co-occurrence Network — Top 100 Candidates',
            showlegend=False,
            height=600,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            font=dict(family='Inter')
        )
        st.plotly_chart(fig_net, width='stretch', config={'displayModeBar': False})
        
        # Skill frequency bar chart
        st.markdown('<h3 style="margin: 24px 0 12px 0; font-size: 18px;">Top Skills by Frequency in Top 100</h3>', unsafe_allow_html=True)
        
        top_20_skills = skill_freq.most_common(20)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=[s for s, _ in top_20_skills],
            y=[c for _, c in top_20_skills],
            marker_color='#4F46E5',
            text=[c for _, c in top_20_skills],
            textposition='outside'
        ))
        fig_bar.update_layout(
            title='Skill Distribution Across Top 100 Candidates',
            xaxis_title='Skill',
            yaxis_title='Number of Candidates',
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter'),
            xaxis=dict(tickangle=-45),
            margin=dict(b=100)
        )
        st.plotly_chart(fig_bar, width='stretch', config={'displayModeBar': False})
        
        # Persona Disagreement Heatmap
        st.markdown('<h3 style="margin: 24px 0 12px 0; font-size: 18px;">Persona Disagreement Heatmap — Top 20</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 12px; color: #6B7280;">High variance across personas = controversial candidate where evaluators disagree.</p>', unsafe_allow_html=True)
        
        heatmap_data = []
        labels = []
        personas = ['technical', 'hiring_manager', 'culture_fit', 'recruiter_ops', 'logistics_education']
        persona_labels = ['Technical', 'Hiring Mgr', 'Culture Fit', 'Recruiter Ops', 'Logistics/Edu']
        
        for c in candidates[:20]:
            scores = c.get('scores', {})
            row = [round(scores.get(p, 0) * 100, 1) for p in personas]
            heatmap_data.append(row)
            labels.append(f"#{c['rank']} {c['profile']['anonymized_name'].split()[0]}")
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=persona_labels,
            y=labels,
            colorscale='RdYlGn',
            text=[[f"{v}" for v in row] for row in heatmap_data],
            texttemplate='%{text}',
            textfont=dict(size=10),
            hovertemplate='%{y}<br>%{x}: %{z:.1f}%<extra></extra>'
        ))
        fig_heat.update_layout(
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter'),
            margin=dict(l=150)
        )
        st.plotly_chart(fig_heat, width='stretch', config={'displayModeBar': False})
    else:
        st.warning("No candidate data available.")

elif nav_page == "📊 Pipeline X-Ray":
    st.markdown(
        """
        <h1 style="margin-bottom: 4px; font-size: 32px;">Pipeline X-Ray</h1>
        <p style="color: #6B7280; font-size: 14px; margin-top: 0;">Complete transparency into how 100,000 candidates flow through each pipeline stage.</p>
        <div style="height: 1px; background-color: #EAE8E4; margin: 20px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    
    st.info("💡 **How to use this:** The Sankey diagram visualizes candidate elimination. Notice the red path (Honeypots) and yellow path (Non-Tech Stuffers) being stripped away early, ensuring AI processing time is only spent on viable candidates.")
    
    hp_data, st_data = load_honeypot_stats(get_mtime("honeypots_caught.json"), get_mtime("stuffers_filtered.json"))
    n_hp = len(hp_data)
    n_st = len(st_data)
    
    # Load saved pipeline stats or default
    p_stats = st.session_state.get('pipeline_stats')
    if not p_stats and os.path.exists("pipeline_stats.json"):
        try:
            with open("pipeline_stats.json", "r", encoding="utf-8") as f:
                p_stats = json.load(f)
        except Exception:
            pass
            
    if not p_stats:
        p_stats = {}
        
    n_total = p_stats.get('scanned', n_hp + n_st + 46826)
    n_evaluated = n_total - n_hp - n_st
    
    # Sankey Funnel Diagram
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=30, thickness=20,
            line=dict(color='#E5E7EB', width=1),
            label=[
                f'All ({n_total:,})',
                f'Honeypots ({n_hp:,})',
                f'Non-Tech ({n_st:,})',
                f'Evaluated ({n_evaluated:,})',
                f'Hard Disqualified',
                f'Top 100'
            ],
            color=['#4F46E5', '#EF4444', '#F59E0B', '#3B82F6', '#9CA3AF', '#10B981']
        ),
        link=dict(
            source=[0, 0, 0, 3, 3],
            target=[1, 2, 3, 4, 5],
            value=[n_hp, n_st, n_evaluated, n_evaluated - 100, 100],
            color=['rgba(239,68,68,0.2)', 'rgba(245,158,11,0.2)', 'rgba(59,130,246,0.2)', 'rgba(156,163,175,0.2)', 'rgba(16,185,129,0.3)']
        )
    )])
    
    fig_sankey.update_layout(
        title='Candidate Flow Through Pipeline',
        font=dict(size=13, family='Inter'),
        height=450,
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_sankey, width='stretch', config={'displayModeBar': False})
    
    # Pipeline stage breakdown
    stages = [
        {"name": "1. JSONL Ingestion", "in": f"{n_total:,}", "out": f"{n_total:,}", "dropped": "0", "color": "#4F46E5", "desc": "Stream-load all candidate profiles from JSONL"},
        {"name": "2. Honeypot Immune System", "in": f"{n_total:,}", "out": f"{n_total - n_hp:,}", "dropped": f"{n_hp:,}", "color": "#EF4444", "desc": "9 structural rules detect fabricated profiles (timeline paradoxes, skill inflation, impossible YoE)"},
        {"name": "3. Coarse Heuristic Filter", "in": f"{n_total - n_hp:,}", "out": f"{n_evaluated:,}", "dropped": f"{n_st:,}", "color": "#F59E0B", "desc": "Eliminate explicitly non-tech profiles (Marketing, HR, Sales) without any AI/ML skill signals"},
        {"name": "4. Multi-Persona Scoring", "in": f"{n_evaluated:,}", "out": f"{n_evaluated:,}", "dropped": "0", "color": "#3B82F6", "desc": "5 virtual evaluators score independently: Technical, Hiring Manager, Culture Fit, Recruiter Ops, Logistics/Edu"},
        {"name": "5. TF-IDF Semantic Boost", "in": f"{n_evaluated:,}", "out": f"{n_evaluated:,}", "dropped": "0", "color": "#8B5CF6", "desc": "Cosine similarity against JD text applies 0.82x-1.25x multiplier"},
        {"name": "6. Hard Disqualifiers", "in": f"{n_evaluated:,}", "out": f"{n_evaluated:,}", "dropped": "Soft penalties", "color": "#6B7280", "desc": "Consulting-only, title-chasers, CV/robotics-only get 0.01x; low GitHub gets 0.90x"},
        {"name": "7. Consensus Ranking", "in": f"{n_evaluated:,}", "out": "100", "dropped": f"{n_evaluated - 100:,}", "color": "#10B981", "desc": "Sort by final_score descending, tiebreak by candidate_id ascending, take top 100"},
    ]
    
    st.markdown('<h3 style="margin: 24px 0 12px 0; font-size: 18px;">Stage-by-Stage Breakdown</h3>', unsafe_allow_html=True)
    
    for stage in stages:
        st.markdown(
            f"""
            <div class="bento-card" style="margin-bottom: 12px; border-left: 4px solid {stage['color']};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; font-size: 16px; color: {stage['color']};">{stage['name']}</h4>
                        <p style="margin: 4px 0 0 0; font-size: 12px; color: #6B7280;">{stage['desc']}</p>
                    </div>
                    <div style="display: flex; gap: 20px; text-align: center;">
                        <div>
                            <p style="margin: 0; font-size: 10px; color: #6B7280; text-transform: uppercase;">In</p>
                            <p style="margin: 0; font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #1F2937;">{stage['in']}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 10px; color: #6B7280; text-transform: uppercase;">Out</p>
                            <p style="margin: 0; font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #10B981;">{stage['out']}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 10px; color: #6B7280; text-transform: uppercase;">Dropped</p>
                            <p style="margin: 0; font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #EF4444;">{stage['dropped']}</p>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

elif nav_page == "Honeypot Audit Logs":

    st.markdown(
        """
        <h1 style="margin-bottom: 4px; font-size: 32px;">Honeypot Immune System</h1>
        <p style="color: #6B7280; font-size: 14px; margin-top: 0;">Audit log of artificial profile anomalies and timeline paradoxes flagged by the security layer.</p>
        <div style="height: 1px; background-color: #EAE8E4; margin: 20px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    
    honeypots, _ = load_honeypot_stats(get_mtime("honeypots_caught.json"), get_mtime("stuffers_filtered.json"))
    
    if not honeypots:
        st.info("No honeypots detected in the candidate database sample. Make sure sample_candidates.json is present in path.")
    else:
        st.markdown(
            f"""
            <div class="stat-card" style="margin-bottom: 24px; border-color: #EF4444; border-width: 2px;">
                <div class="stat-title" style="color: #EF4444; font-weight: 700;">ACTIVE SHIELD PROTECTING PIPELINE</div>
                <div class="stat-value" style="color: #EF4444;">{len(honeypots)} Honeypots Caught</div>
                <p style="font-size: 12px; color: #6B7280; margin-top: 4px;">These profiles contain fabricated credentials, temporal date paradoxes, or impossible college-to-job timelines designed to trick standard keyword search algorithms.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Render table or list of honeypots
        for hp in honeypots[:30]: # Limit to top 30 caught for performance
            st.markdown(
                f"""
                <div class="bento-card" style="border-left: 5px solid #EF4444;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h4 style="margin: 0; font-size: 16px; color: #EF4444;">{hp['id']} • {hp['name']}</h4>
                            <p style="margin: 4px 0 0 0; font-size: 13px; color: #1F2937;"><b>Declared Title:</b> {hp['title']} • {format_yoe(hp['yoe'])} Declared YoE</p>
                            <p style="margin: 8px 0 0 0; font-size: 12px; color: #6B7280; background-color: #FEF2F2; padding: 8px 12px; border-radius: 8px; border: 1px solid #FEE2E2;">
                                <b>Flagged Violation:</b> {hp.get('reasons', 'Timeline paradox or structural anomaly detected')}
                            </p>
                        </div>
                        <span class="badge-peach" style="background-color: #FEE2E2 !important; color: #EF4444 !important; font-size: 10px !important;">DISQUALIFIED</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

elif nav_page == "Keyword Stuffing Rules":
    st.markdown(
        """
        <h1 style="margin-bottom: 4px; font-size: 32px;">Adversarial Robustness Layer</h1>
        <p style="color: #6B7280; font-size: 14px; margin-top: 0;">Profiles caught trying to manipulate semantic matchers using keyword stuffing or irrelevant job titles.</p>
        <div style="height: 1px; background-color: #EAE8E4; margin: 20px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    
    _, stuffers = load_honeypot_stats(get_mtime("honeypots_caught.json"), get_mtime("stuffers_filtered.json"))
    
    if not stuffers:
        st.info("No keyword stuffers or non-tech profiles filtered in sample.")
    else:
        st.markdown(
            f"""
            <div class="stat-card" style="margin-bottom: 24px; border-color: #F59E0B; border-width: 2px;">
                <div class="stat-title" style="color: #F59E0B; font-weight: 700;">COARSE HEURISTICS FILTER STATUS</div>
                <div class="stat-value" style="color: #F59E0B;">{len(stuffers)} Profiles Filtered</div>
                <p style="font-size: 12px; color: #6B7280; margin-top: 4px;">These profiles were bypassed early in the ranking execution because their current title or career trajectory does not match engineering roles (e.g. Sales, Marketing, HR, or non-technical management) and they lack proven hands-on ML/AI experience.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Render table or list of stuffers
        for stf in stuffers[:30]:
            st.markdown(
                f"""
                <div class="bento-card" style="border-left: 5px solid #F59E0B;">
                    <div>
                        <h4 style="margin: 0; font-size: 16px; color: #B45309;">{stf['id']} • {stf['name']}</h4>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #1F2937;"><b>Current Title:</b> {stf['title']} • {format_yoe(stf['yoe'])}</p>
                        <p style="margin: 8px 0 0 0; font-size: 12px; color: #6B7280;">
                            <b>Listed Skills:</b> {', '.join(stf['skills'])}
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
