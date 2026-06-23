"""
RecruitIQ Engine Test Suite
Tests the pipeline with 7 carefully crafted candidate profiles to verify:
1. Perfect AI candidate ranks #1
2. Honeypot (fake profile) is blocked
3. Pure consulting candidate is hard-disqualified
4. Title chaser is hard-disqualified
5. Backend-only (no ML) candidate gets low score
6. Non-tech HR candidate is filtered by coarse filter
7. Junior ML candidate passes but ranks lower than senior
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Go up to project root
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.abspath(project_root))
os.chdir(os.path.abspath(project_root))

from pipeline.honeypot import is_honeypot
from pipeline.coarse_filter import is_coarse_match
from pipeline.scorers.technical import calculate_technical_score
from pipeline.scorers.hiring_manager import calculate_hiring_manager_score
from pipeline.scorers.culture_fit import calculate_culture_fit_score
from pipeline.scorers.recruiter_ops import calculate_recruiter_ops_score
from pipeline.scorers.logistics_education import calculate_logistics_education_score
from pipeline.modifiers.hard_disqualifiers import get_hard_disqualifier_multiplier
from pipeline.modifiers.semantic_similarity import apply_semantic_similarity
from pipeline.ranker import rank_candidates
from pipeline.reasoning import generate_candidate_reasoning
from pipeline.jd_parser import JDParser

PASS = "[PASS]"
FAIL = "[FAIL]"
tests_passed = 0
tests_failed = 0

def check(condition, test_name, details=""):
    global tests_passed, tests_failed
    if condition:
        print(f"  {PASS} {test_name}")
        tests_passed += 1
    else:
        print(f"  {FAIL} {test_name} — {details}")
        tests_failed += 1

# Load test data
test_file = os.path.join("tests", "test_candidates.jsonl")
test_jd = os.path.join("tests", "test_jd.txt")

with open(test_jd, 'r', encoding='utf-8') as f:
    jd_text = f.read()

candidates = []
with open(test_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            candidates.append(json.loads(line))

cand_map = {c['candidate_id']: c for c in candidates}

print("=" * 60)
print("  RecruitIQ Engine Test Suite")
print("=" * 60)

# ============================================================
# TEST 1: Honeypot Detection
# ============================================================
print("\n[1] HONEYPOT DETECTION")
check(
    not is_honeypot(cand_map["TEST_PERFECT_AI"]),
    "Perfect AI candidate is NOT flagged as honeypot"
)
check(
    is_honeypot(cand_map["TEST_HONEYPOT_FAKE"]),
    "Fake profile IS flagged as honeypot",
    f"Honeypot returned {is_honeypot(cand_map['TEST_HONEYPOT_FAKE'])}"
)
check(
    not is_honeypot(cand_map["TEST_CONSULTING_ONLY"]),
    "Consulting candidate is NOT a honeypot (just bad fit)"
)
check(
    not is_honeypot(cand_map["TEST_NONTECH_HR"]),
    "HR manager is NOT a honeypot (just wrong field)"
)

# ============================================================
# TEST 2: Coarse Filter
# ============================================================
print("\n[2] COARSE FILTER")
check(
    is_coarse_match(cand_map["TEST_PERFECT_AI"]),
    "Perfect AI passes coarse filter"
)
check(
    not is_coarse_match(cand_map["TEST_NONTECH_HR"]),
    "HR manager BLOCKED by coarse filter",
    f"Returned {is_coarse_match(cand_map['TEST_NONTECH_HR'])}"
)
check(
    is_coarse_match(cand_map["TEST_JUNIOR_ML"]),
    "Junior ML passes coarse filter"
)

# ============================================================
# TEST 3: Hard Disqualifiers
# ============================================================
print("\n[3] HARD DISQUALIFIERS")
mult_perfect, reason_perfect = get_hard_disqualifier_multiplier(cand_map["TEST_PERFECT_AI"])
check(mult_perfect == 1.0, "Perfect AI has no disqualification", f"mult={mult_perfect}")

mult_consulting, reason_consulting = get_hard_disqualifier_multiplier(cand_map["TEST_CONSULTING_ONLY"])
check(mult_consulting == 0.0, "Pure consulting gets 0.0x multiplier", f"mult={mult_consulting}, reason={reason_consulting}")

mult_chaser, reason_chaser = get_hard_disqualifier_multiplier(cand_map["TEST_TITLE_CHASER"])
check(mult_chaser == 0.0, "Title chaser gets 0.0x multiplier", f"mult={mult_chaser}, reason={reason_chaser}")

mult_backend, reason_backend = get_hard_disqualifier_multiplier(cand_map["TEST_BACKEND_PYSKILL"])
check(mult_backend == 1.0, "Backend engineer has no hard disqualification", f"mult={mult_backend}")

# ============================================================
# TEST 4: Technical Scorer
# ============================================================
print("\n[4] TECHNICAL SCORER")
tech_perfect = calculate_technical_score(cand_map["TEST_PERFECT_AI"])
tech_backend = calculate_technical_score(cand_map["TEST_BACKEND_PYSKILL"])
tech_junior = calculate_technical_score(cand_map["TEST_JUNIOR_ML"])
tech_consulting = calculate_technical_score(cand_map["TEST_CONSULTING_ONLY"])

check(tech_perfect > 0.7, f"Perfect AI tech score is high ({tech_perfect:.3f})")
check(tech_perfect > tech_backend, f"Perfect AI ({tech_perfect:.3f}) > Backend ({tech_backend:.3f})")
check(tech_perfect > tech_junior, f"Perfect AI ({tech_perfect:.3f}) > Junior ML ({tech_junior:.3f})")
check(tech_junior > tech_consulting, f"Junior ML ({tech_junior:.3f}) > Consulting ({tech_consulting:.3f})")
check(tech_backend < tech_perfect, f"Backend ({tech_backend:.3f}) < Perfect AI — no ML title/skills differentiation working")

# ============================================================
# TEST 5: Full Pipeline (End-to-End)
# ============================================================
print("\n[5] FULL PIPELINE (End-to-End)")

def test_generator():
    with open(test_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

ranked, stats = rank_candidates(test_generator(), jd_text)

check(stats['total_scanned'] == 7, f"Scanned all 7 candidates ({stats['total_scanned']})")
check(stats['honeypots_blocked'] >= 1, f"Blocked {stats['honeypots_blocked']} honeypot(s)")

# Check honeypot was blocked
ranked_ids = [c['candidate_id'] for c in ranked]
check("TEST_HONEYPOT_FAKE" not in ranked_ids, "Honeypot not in ranked results")
check("TEST_NONTECH_HR" not in ranked_ids, "HR manager not in ranked results")

# Check perfect AI is ranked highest
if ranked:
    check(ranked[0]['candidate_id'] == "TEST_PERFECT_AI", 
          f"Perfect AI is ranked #1 (actual: #{ranked[0]['candidate_id']})")
    
    # Check scores are in descending order
    scores = [c['final_score'] for c in ranked]
    check(all(scores[i] >= scores[i+1] for i in range(len(scores)-1)), 
          "Scores are in descending order")

# ============================================================
# TEST 6: Reasoning Generation
# ============================================================
print("\n[6] REASONING GENERATION")
for c in ranked:
    c['reasoning'] = generate_candidate_reasoning(c)

if ranked:
    reasoning_1 = ranked[0]['reasoning']
    check(len(reasoning_1) > 50, f"Reasoning has content ({len(reasoning_1)} chars)")
    check(len(reasoning_1) <= 500, f"Reasoning within 500 char limit ({len(reasoning_1)} chars)")
    
    # Check that different candidates have different reasoning
    if len(ranked) >= 2:
        r1 = ranked[0]['reasoning']
        r2 = ranked[1]['reasoning']
        check(r1 != r2, "Different candidates have different reasoning")

# ============================================================
# TEST 7: JD Parser
# ============================================================
print("\n[7] JD PARSER")
jd_parser = JDParser(test_jd)
check(len(jd_parser.raw_text) > 100, f"JD parser loaded text ({len(jd_parser.raw_text)} chars)")
disqualifiers = jd_parser.get_disqualifiers()
check('consulting_only' in disqualifiers, "Disqualifiers dict has consulting_only key")
check(len(disqualifiers['consulting_only']) > 0, f"Found {len(disqualifiers['consulting_only'])} consulting companies")

# ============================================================
# TEST 8: CSV Output Format
# ============================================================
print("\n[8] CSV OUTPUT")
import csv
import tempfile

csv_path = os.path.join(tempfile.gettempdir(), "test_output.csv")
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
    for c in ranked:
        writer.writerow([
            c['candidate_id'],
            c['rank'],
            round(c['final_score'], 4),
            c['reasoning']
        ])

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

check(len(rows) > 0, f"CSV has {len(rows)} rows")
check(rows[0]['rank'] == '1', "First row has rank 1")
check(all(k in rows[0] for k in ['candidate_id', 'rank', 'score', 'reasoning']), 
      "CSV has all required columns")

# Clean up
os.remove(csv_path)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print(f"  RESULTS: {tests_passed} passed, {tests_failed} failed")
print("=" * 60)

if ranked:
    print("\n  RANKING RESULTS:")
    for c in ranked:
        p = c.get('profile', {})
        mult, reason = get_hard_disqualifier_multiplier(c)
        disq_tag = f" [DISQ: {reason}]" if reason else ""
        print(f"    #{c['rank']} {c['candidate_id']} | {p.get('current_title', '')} @ {p.get('current_company', '')} | Score: {c['final_score']:.4f}{disq_tag}")

if tests_failed > 0:
    print(f"\n  {tests_failed} test(s) FAILED — review the output above.")
    sys.exit(1)
else:
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
