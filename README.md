# RecruitIQ — AI-Powered Candidate Discovery & Ranking Engine

> **Team AlphaBeta** | Daksh Dawra, Adhya Varshney  
> India Runs Data & AI Challenge 2026

## Overview

RecruitIQ is a multi-persona consensus ranking engine that processes 100,000 candidate profiles to produce an optimally ranked top-100 shortlist for a Senior AI Engineer position. The system uses 5 virtual evaluators, 23 behavioral signals, TF-IDF semantic matching, a 9-rule honeypot immune system, and a diversity re-ranker — all running on CPU in under 60 seconds.

## Architecture

```
candidates.jsonl (100K)
    │
    ├── Honeypot Immune System (9 rules)
    │   ├── Timeline paradoxes
    │   ├── Skill inflation (≥10 expert, 0 proof)
    │   ├── Impossible YoE vs graduation
    │   ├── Future dates
    │   ├── Unrealistic skill count (>40)
    │   └── Perfect assessment scores
    │
    ├── Coarse Heuristic Filter
    │   └── Remove non-tech profiles (Marketing, HR, Sales)
    │
    ├── Multi-Persona Scoring Engine (5 evaluators)
    │   ├── Technical Interviewer (title relevance + skills + proficiency + assessments + GitHub + certs)
    │   ├── Hiring Manager (YoE + tenure + progression + company quality)
    │   ├── Culture Fit Assessor (stability + consulting penalty + academic check)
    │   ├── Recruiter Ops (all 23 redrob behavioral signals)
    │   └── Logistics/Education (notice + location + salary + work mode + degree)
    │
    ├── TF-IDF Semantic Similarity Boost (0.82x – 1.25x)
    │
    ├── Hard Disqualifier Modifiers
    │   ├── Pure consulting-only → 0.01x
    │   ├── Serial title-chasers → 0.01x
    │   └── CV/Robotics-only without NLP → 0.01x
    │
    ├── Diversity Re-Ranking
    │   └── Diminishing returns for same company+title clusters (>3 duplicates penalized)
    │
    └── Consensus Ranking → Top 100 with per-candidate reasoning
```

## Reproduce Submission

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place candidates.jsonl in project root or use default data path
# 3. Run ranking pipeline (produces submission.csv)
python rank.py --out ./submission.csv

# 4. Validate output
python validate_submission.py submission.csv

# 5. Launch interactive dashboard
streamlit run app.py
```

> [!NOTE]
> The interactive dashboard uses Tailwind CSS and Google Fonts via CDN for the premium visual experience. A local fallback stylesheet is embedded so the app remains fully functional and structured when offline, but an active internet connection is recommended for the best experience.

## Innovative Features

1. **Ranking Robustness Score** — Monte Carlo simulation (500 runs) showing rank stability under random weight perturbations. "Safe Bet" vs "Weight-Sensitive" candidates.

2. **Skill Ecosystem Map** — Interactive force-directed network showing skill co-occurrence. Connected skills form natural clusters; isolated keywords signal stuffing.

3. **Pipeline X-Ray** — Sankey funnel diagram showing candidate flow: 100K → Honeypot Shield → Coarse Filter → Scoring → Top 100. Full stage-by-stage transparency.

4. **Persona Disagreement Heatmap** — Visual showing where virtual evaluators disagree on candidates. High variance = controversial hire needing recruiter judgment.

5. **Interactive Consensus Tuning** — Live weight sliders to adjust persona weights and see leaderboard re-rank in real-time.

## Scoring Formula

```
Final Score = Persona Sum × Semantic Boost × Hard Disqualifier Multiplier

Persona Sum = Technical × 0.30 + Hiring Manager × 0.25 + Culture Fit × 0.15 
            + Recruiter Ops × 0.15 + Logistics/Education × 0.15
```

## Compute Environment

- **Platform**: Windows 11, Intel i5
- **RAM**: 16 GB
- **Python**: 3.11
- **Runtime**: ~38 seconds (well within 5-minute budget)
- **GPU**: None (CPU only)
- **Network**: None during ranking

## Files

| File | Description |
|------|-------------|
| `rank.py` | CLI entry point — produces submission.csv |
| `app.py` | Streamlit dashboard with 5 innovative features |
| `config.py` | All weights, skill lists, constants |
| `submission.csv` | Final top-100 ranking output |
| `submission_metadata.yaml` | Team metadata |
| `pipeline/` | Core ranking engine modules |

## AI Tools Used

- Gemini (code scaffolding, debugging)
- Claude (architecture review)
- Cursor (development environment)

All ranking logic, scoring formulas, and architectural decisions were designed and validated by the team. The pipeline runs fully offline with no AI API calls during ranking.
