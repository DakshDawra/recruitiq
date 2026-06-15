from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def apply_semantic_similarity(candidates, jd_text):
    """
    Fits TF-IDF vectorizer on the filtered candidates text corpus and computes
    cosine similarity against the JD text. Returns candidates list with semantic scores.
    """
    if not candidates or not jd_text:
        return candidates
        
    # 1. Build the text corpus for candidates
    corpus = []
    for c in candidates:
        profile = c.get('profile', {})
        career_history = c.get('career_history', [])
        
        cand_text = (
            str(profile.get('summary', '')) + " " +
            str(profile.get('headline', ''))
        )
        for job in career_history:
            cand_text += " " + str(job.get('description', ''))
        # Add skill names to strengthen signal
        for skill in c.get('skills', []):
            cand_text += " " + str(skill.get('name', ''))
        # Add certification names
        for cert in c.get('certifications', []):
            cand_text += " " + str(cert.get('name', ''))
            
        corpus.append(cand_text.lower())
        
    # 2. Add Job Description to corpus
    corpus.append(jd_text.lower())
    
    # 3. Compute TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=2500,
        stop_words='english',
        ngram_range=(1, 2)
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Candidate vectors are rows 0 to len(candidates) - 1
        # JD vector is the last row
        jd_vector = tfidf_matrix[-1]
        cand_vectors = tfidf_matrix[:-1]
        
        # Calculate cosine similarity
        similarities = cosine_similarity(cand_vectors, jd_vector).flatten()
        
        # 4. Inject similarity score and calculate boost factor (0.9 to 1.15)
        for idx, c in enumerate(candidates):
            sim_score = float(similarities[idx])
            c['semantic_similarity_score'] = sim_score
            # Apply a safe multiplicative modifier: 0.90 baseline to 1.15 boost for highly similar text
            c['semantic_boost'] = 0.82 + (sim_score * 0.43)
            
    except Exception:
        # Fallback if TF-IDF fails
        for c in candidates:
            c['semantic_similarity_score'] = 0.0
            c['semantic_boost'] = 1.0
            
    return candidates
