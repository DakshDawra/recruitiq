import os

# Base paths
WORKSPACE_DIR = r"c:\Users\HP\OneDrive\Documents\Track1"
DATA_DIR = os.path.join(WORKSPACE_DIR, "[PUB] India_runs_data_and_ai_challenge (1)", "[PUB] India_runs_data_and_ai_challenge", "India_runs_data_and_ai_challenge")
CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.jsonl")

# JD Specific Requirements (extracted from job_description.docx)
REQUIRED_SKILLS = {
    'nlp', 'pytorch', 'tensorflow', 'machine learning', 'deep learning', 
    'bert', 'transformers', 'llm', 'fine-tuning llms', 'rag',
    'computer vision', 'embeddings', 'faiss', 'pinecone', 'milvus', 
    'weaviate', 'vector search', 'hugging face', 'lora', 'peft', 
    'qlora', 'sentence transformers', 'recommendation systems', 
    'information retrieval', 'xgboost', 'mlflow', 'weights & biases'
}

# Strong positive indicators for founding engineer mindset
PRODUCT_COMPANY_KEYWORDS = {
    'product', 'platform', 'saas', 'startup', 'founding', 'deploy', 
    'scale', 'shipped', 'production', 'pipeline', 'infrastructure'
}

# Explicit Disqualifiers (Must carry 0.0 modifier)
CONSULTING_COMPANIES = {
    'tcs', 'tata consultancy services', 'infosys', 'wipro', 'accenture', 
    'cognizant', 'capgemini', 'hcl', 'tech mahindra', 'l&t infotech'
}

NON_TECH_TITLES = {
    'marketing manager', 'hr manager', 'accountant', 'sales executive', 
    'customer support', 'graphic designer', 'content writer', 
    'civil engineer', 'mechanical engineer', 'operations manager', 
    'business analyst', 'project manager', 'recruiter'
}

# Target locations (Noida/Pune preferred, hybrid cadence)
PREFERRED_LOCATIONS = {'noida', 'pune', 'delhi ncr', 'mumbai', 'hyderabad'}

# Notice Period Weight Table
# Sub-30 days ideal, 30+ has higher bar, >90 penalized heavily
def get_notice_period_weight(days):
    if days <= 30:
        return 1.0
    elif days <= 60:
        return 0.7
    elif days <= 90:
        return 0.4
    else:
        return 0.1

# Weights for Multi-Persona Consensus Engine
PERSONA_WEIGHTS = {
    'technical': 0.25,        # Deep technical skills + assessments + github
    'hiring_manager': 0.25,   # Career trajectory, product startup background, tenure
    'culture_fit': 0.20,      # Tenure consistency, no pure consulting, no pure academic research
    'recruiter_ops': 0.15,    # Availability, response rate, saved by recruiters count
    'logistics': 0.10,        # Location, notice period, salary alignment
    'education': 0.05         # Field of study, university tier
}
