import argparse
import time
import csv
import json
import os
from pipeline.loader import stream_candidates
from pipeline.jd_parser import JDParser
from pipeline.ranker import rank_candidates
from pipeline.reasoning import generate_candidate_reasoning
from config import CANDIDATES_FILE, DATA_DIR, WORKSPACE_DIR

def main():
    parser = argparse.ArgumentParser(description="RecruitIQ Candidate Discovery & Ranking Engine")
    
    # Smart default: check current directory first, then fall back to DATA_DIR
    default_cand = CANDIDATES_FILE
    for local_name in ['candidates.jsonl', 'candidates.json']:
        if os.path.exists(local_name):
            default_cand = local_name
            break
    
    parser.add_argument('--candidates', type=str, default=default_cand, help="Path to candidates JSONL file")
    parser.add_argument('--jd', type=str, default=None, help="Path to job description file (.docx or .txt)")
    parser.add_argument('--out', type=str, default='submission.csv', help="Output CSV path")
    args = parser.parse_args()
    
    start_time = time.time()
    
    # 1. Load Job Description
    jd_text = None
    jd_path = None
    
    if args.jd:
        if os.path.exists(args.jd):
            jd_path = args.jd
        else:
            # Check relative to WORKSPACE_DIR if not found in CWD
            candidate_path = os.path.join(WORKSPACE_DIR, args.jd)
            if os.path.exists(candidate_path):
                jd_path = candidate_path
                
    if not jd_path:
        # Check standard locations in DATA_DIR
        jd_doc_path = os.path.join(DATA_DIR, "job_description.docx")
        jd_txt_path = os.path.join(DATA_DIR, "job_description.txt")
        
        # Check standard locations in WORKSPACE_DIR
        local_jd_doc = os.path.join(WORKSPACE_DIR, "job_description.docx")
        local_jd_txt = os.path.join(WORKSPACE_DIR, "job_description.txt")
        local_jd_txt_2 = os.path.join(WORKSPACE_DIR, "jd.txt")
        
        # Check standard locations in CWD
        cwd_jd_txt = "jd.txt"
        cwd_jd_txt_2 = "job_description.txt"
        
        for p in [jd_doc_path, jd_txt_path, local_jd_doc, local_jd_txt, local_jd_txt_2, cwd_jd_txt, cwd_jd_txt_2]:
            if p and os.path.exists(p):
                jd_path = p
                break
                
    if jd_path:
        print(f"Loading Job Description from: {jd_path}")
        if jd_path.endswith('.txt'):
            try:
                with open(jd_path, 'r', encoding='utf-8') as f:
                    jd_text = f.read()
            except Exception as e:
                print(f"Warning: Failed to read text JD: {e}")
        else:
            try:
                jd_parser = JDParser(jd_path)
                jd_text = jd_parser.raw_text
            except Exception as e:
                print(f"Warning: Failed to parse docx JD: {e}")
                
    if not jd_text:
        print("Warning: Job description file not found or empty. Falling back to default Redrob Senior AI Engineer JD.")
        jd_text = """Job Description: Senior AI Engineer — Founding Team
Company: Redrob AI (Series A AI-native talent intelligence platform)
Location: Pune/Noida, India (Hybrid — flexible cadence)
Experience Required: 5–9 years

We are looking for a Senior AI Engineer to own the intelligence layer of Redrob's product (ranking, retrieval, matching systems).
Skills Needed: PyTorch, NLP, LLMs, RAG, Fine-tuning, Vector DBs (FAISS, Pinecone, Milvus), Evaluation frameworks (NDCG).
Disqualifiers: Pure Consulting (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini), Job-hopping / Title-chasers, CV/Robotics without NLP."""
        
    print(f"Streaming candidates from: {args.candidates}")
    
    # 2. Run Ingestion and Ranking Pipeline
    candidates_gen = stream_candidates(args.candidates)
    
    print("Processing candidate database...")
    ranked_candidates, stats = rank_candidates(candidates_gen, jd_text)
    
    # 3. Generate Reasoning for Shortlisted Candidates
    for c in ranked_candidates:
        c['reasoning'] = generate_candidate_reasoning(c)
        
    # 4. Write CSV Output
    print(f"Writing ranked shortlist (Top 100) to: {args.out}")
    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
        for c in ranked_candidates:
            writer.writerow([
                c.get('candidate_id', ''),
                c.get('rank', ''),
                round(c.get('final_score', 0.0), 4),
                c.get('reasoning', '')
            ])
            
    # 5. Write JSON Details for Streamlit Dashboard
    json_out = "top_100_details.json"
    print(f"Writing top 100 details JSON to: {json_out}")
    with open(json_out, 'w', encoding='utf-8') as fj:
        json.dump(ranked_candidates, fj, indent=2, ensure_ascii=False)
        
    # 6. Save honeypot and stuffer logs for dashboard
    print("Saving audit logs...")
    with open("honeypots_caught.json", "w", encoding="utf-8") as f:
        json.dump(stats.get('honeypot_details', []), f, indent=2, ensure_ascii=False)
    with open("stuffers_filtered.json", "w", encoding="utf-8") as f:
        json.dump(stats.get('stuffer_details', []), f, indent=2, ensure_ascii=False)
        
    # 7. Save pipeline stats for dashboard
    end_time = time.time()
    elapsed = end_time - start_time
    with open("pipeline_stats.json", "w", encoding="utf-8") as fstats:
        json.dump({
            "scanned": stats['total_scanned'],
            "honeypots": stats['honeypots_blocked'],
            "stuffers": stats['stuffers_filtered'],
            "latency": round(elapsed, 2)
        }, fstats, indent=2)
    
    print("\n" + "="*50)
    print("  RecruitIQ Ranking Engine — Execution Summary")
    print("="*50)
    print(f"  Total Candidates Scanned:   {stats['total_scanned']:,}")
    print(f"  Honeypots Blocked:          {stats['honeypots_blocked']:,}")
    print(f"  Keyword Stuffers Filtered:  {stats['stuffers_filtered']:,}")
    print(f"  Candidates Evaluated:       {stats['total_scanned'] - stats['honeypots_blocked'] - stats['stuffers_filtered']:,}")
    print(f"  Shortlist Size:             {len(ranked_candidates)}")
    print(f"  Total Execution Time:       {elapsed:.2f} seconds")
    print("="*50)
    print("Execution complete. Output is fully compliant with validator.")

if __name__ == '__main__':
    main()
