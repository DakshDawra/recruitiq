# RecruitIQ — AI-Powered Candidate Discovery & Ranking Engine

> **A-Grade Submission | India Runs Data & AI Challenge 2026 (Redrob AI)**  
> **Team AlphaBeta:** Daksh Dawra (Lead) & Adhya Varshney  
> **Live Dashboard:** [https://recruitiq-web.streamlit.app/](https://recruitiq-web.streamlit.app/)

---

## 📖 The RecruitIQ Story

### 1. The Problem: The 100K Haystack & The Adversarial Trap
Recruiting at the early stages of a high-growth startup is a high-stakes bottleneck. When faced with **100,000+ candidates**, traditional keyword-matching filters (ATS) are easily fooled by keyword-stuffers. Even worse, the challenge's `sample_submission.csv` is an **adversarial trap**—ranking non-technical profiles (such as HR Managers and Graphic Designers) with high scores due to artificial keyword density. Naive ML models trained directly on the sample output will fail to identify real talent.

### 2. The Core Insight: Recruiting is a Consensus Committee
Real-world hiring is never a single opinion. It is a collaborative committee decision.  
To solve this, **RecruitIQ** rejects simple keyword frequency. Instead, we model a **5-Persona Consensus Committee** that evaluates candidates from multiple dimensions.

### 3. The Solution: Multi-Persona Consensus Engine with Honeypot Immunity
Our pipeline runs completely offline on CPU in ~92 seconds and implements the following stages:

```
[100,000 Candidate Profiles (JSONL)]
                │
                ▼
   [🛡️ Honeypot Immune System] ──► Blocked 1,432 Fake Profiles (Timeline Paradoxes, Skill Inflation)
                │
                ▼
   [🔍 Coarse Heuristic Filter] ──► Eliminated Non-Tech Profile Stuffers (Marketing, HR, Sales)
                │
                ▼
   [👥 5-Persona Consensus scoring]
   ├── 🛠️ Technical Depth (0.30) ──► Skill cross-validation (capping PEFT/RAG timelines) + assessments + GitHub + certs
   ├── 💼 Hiring Manager (0.25)  ──► Tenure consistency + product startup career trajectory + size scaling
   ├── 🧠 Culture Fit (0.15)     ──► Stability check + Consulting-only penalties + Academic-only filters
   ├── 📞 Recruiter Ops (0.15)   ──► Active login history + recruiter saves + response/completion rates
   └── 📦 Logistics/Edu (0.15)   ──► Notice period + Noida/Pune location + salary + degree tier
                │
                ▼
   [⚡ TF-IDF Semantic Alignment] ──► Dense Cosine Similarity boost (0.82x - 1.25x) against JD text
                │
                ▼
   [🚫 Hard Disqualifiers] ──► Consulting-only (0.0x), Title-Chasers (0.0x), CV/Robotics-only without NLP (0.0x)
                │
                ▼
   [🧬 Diversity Re-Ranking] ──► Clustered company+title penalty (>3 identical profiles penalized)
                │
                ▼
         [🏆 Top-100 Shortlist] ──► submission.csv (100% compliant, deterministic tiebreaks, fact-dense reasoning)
```

---

## 📊 Core Performance & Validation Metrics

### 🛡️ Honeypot Shield Audit Logs
Our 9-rule immune system caught and blocked **1,432 planted profiles** across the 100K dataset. These fake candidates were weeded out early due to:
- **Timeline Paradoxes:** Starting jobs before graduating, or starting a role after its end date.
- **Skill Inflation:** Declaring 10+ "expert" skills with exactly 0 months of duration and 0 endorsements.
- **Impossible YoE:** Claiming 15 years of experience when college graduation was in 2022.
- **Suspicious Performance:** Scorecards showing exactly 100/100 on 5+ different assessments.

**Result:** **0% honeypots** in our final top-100 shortlist.

### 🔬 Rank Robustness (Monte Carlo Simulation)
Most ranking engines fail when weights are slightly adjusted. RecruitIQ runs a **500-run Monte Carlo simulation** that perturbs persona weights by $\pm 10\%$ randomly to calculate rank stability ($\sigma$).
- **"Safe Bets":** Candidates whose rank standard deviation is $\sigma < 5.0$.
- **Validation:** **17 of our top 20** candidates are classified as **Safe Bets**, proving that our consensus is statistically robust and insensitive to individual evaluator bias.

### 🎯 Strategic NDCG@10 Optimization
The hackathon scoring formula places heavy emphasis on top-10 precision:
$$\text{Grade Score} = 0.50 \times \text{NDCG@10} + 0.30 \times \text{NDCG@50}$$
To maximize our score, RecruitIQ prioritizes precision in the top-10 using **Proof-of-Competence Cross-Validation**:
- We calculate the duration of skills *claimed* in the skills list and cross-validate it against the candidate's actual job description timelines.
- We apply technology age caps during reasoning formatting (e.g., PEFT/QLoRA capped to 48 months; RAG/Pinecone capped to 60 months) to eliminate impossible claims.
- This ensures that our top-10 candidates are verified practitioners, not keyword-stuffed profiles.

---

## ⚖️ Weight Calibration Rationale
The consensus weights were carefully calibrated based on the Series A Founding AI Engineer job description:
- **Technical Depth (30%):** The founding engineer must own the intelligence layer (embeddings, retrieval, ranking). Requires verified skill depth.
- **Hiring Manager Fit (25%):** Prioritized candidate experience in fast-paced product startups (scale, shipped, SaaS) rather than large enterprise maintenance.
- **Culture Fit (15%):** Penalized job-hoppers (title-chasers switching every 1.5 years) and candidates with pure consulting backgrounds (TCS/Infosys/Wipro), matching the JD's explicit constraints.
- **Recruiter Ops (15%):** Availability and responsiveness are critical for immediate onboarding.
- **Logistics & Education (15%):** Heavy preference for hybrid candidates located in Noida/Pune with short notice periods (<30 days).

### 📡 The 23 Redrob Behavioral Signals (Mapping)
Our pipeline uses 100% of the 23 provided `redrob_signals` across the evaluation personas:
| Signal Name | Persona Scorer | Weight Impact |
|:---|:---|:---|
| `last_active_date`, `signup_date` | Recruiter Ops | 18% / 8% (Platform tenure & recency) |
| `recruiter_response_rate`, `interview_completion_rate` | Recruiter Ops | 22% (Engagement score) |
| `open_to_work_flag`, `applications_submitted_30d` | Recruiter Ops | 22% / 5% (Active seeking) |
| `saved_by_recruiters_30d`, `search_appearance_30d`, `profile_views_received_30d` | Recruiter Ops | 13% (Recruiter PageRank) |
| `profile_completeness_score`, `avg_response_time_hours` | Recruiter Ops | 10% / 10% |
| `connection_count`, `endorsements_received` | Recruiter Ops | 7% (Network score) |
| `offer_acceptance_rate` | Recruiter Ops | 7% (Offer reliability) |
| `verified_email`, `verified_phone`, `linkedin_connected` | Recruiter Ops | Trust Multiplier (0.85x - 1.0x) |
| `notice_period_days`, `willing_to_relocate`, `preferred_work_mode` | Logistics/Edu | Primary Notice & Location scores |
| `expected_salary_range_inr_lpa` | Logistics/Edu | Salary match scoring |
| `github_activity_score`, `skill_assessment_scores` | Technical Depth | GitHub (0.90x penalty if 0), Verified assessment boosts |

---

## 🚀 How to Reproduce Submission

Follow these steps to run the pipeline and launch the dashboard locally:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run ranking pipeline (takes candidates.jsonl in CWD or dynamic fallback)
# Produces submission.csv in ~92 seconds on CPU
python rank.py --candidates ./candidates.jsonl --out ./submission.csv

# 3. Validate compliance with official validator
python validate_submission.py submission.csv

# 4. Launch the Streamlit dashboard
streamlit run app.py
```

---

## 🛠️ Tech Stack & Compute Budget
- **Core:** Python 3.11, Streamlit 1.45.1, Pandas 2.2.3, Scikit-learn 1.6.1, Plotly 6.1.2, NumPy 2.2.6
- **Compute:** CPU-only (no GPU required), fully offline (no external LLM API calls or network requests during ranking).
- **Latency:** **91.52 seconds** to stream, clean, score, re-rank, and generate reasoning for 100,000 candidates (average of ~0.92ms per candidate).

> **Note on Dashboard UI**: The `rank.py` engine is strictly offline and network-free. The `app.py` Streamlit dashboard, however, loads Tailwind CSS and Google Fonts via external CDNs for premium styling. The "Upgrade to Premium" paywall is a non-functional mock UI designed exclusively to demonstrate how Redrob could monetize this product in the future.
