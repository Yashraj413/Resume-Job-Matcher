import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize NLTK stopwords with a safety fallback
try:
    STOPWORDS = set(stopwords.words('english'))
except LookupError:
    try:
        nltk.download('stopwords', quiet=True)
        STOPWORDS = set(stopwords.words('english'))
    except Exception:
        # Static fallback list in case of network failures or offline environments
        STOPWORDS = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
            'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
            'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
            'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
            'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
            'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
            "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
            'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
            'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
            'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
        }

def preprocess_text(text):
    """Normalize text by lowercasing, removing symbols, and filtering stopwords."""
    if not text:
        return ""
    # Standardize spaces and remove punctuation
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = text.lower()
    words = text.split()
    filtered_words = [word for word in words if word not in STOPWORDS]
    return " ".join(filtered_words)

def match_resumes(job_description, resumes_list):
    """
    Compute similarity scores between a job description and a list of resumes.
    resumes_list format: [{'id': id, 'text': text}, ...]
    Returns: [{'id': id, 'score': float}, ...]
    """
    if not job_description or not resumes_list:
        return []

    processed_job = preprocess_text(job_description)
    processed_resumes = [preprocess_text(r['text']) for r in resumes_list]

    # Validate that we have processable tokens
    if not processed_job.strip() or not any(pr.strip() for pr in processed_resumes):
        return [{'id': r['id'], 'score': 0.0} for r in resumes_list]

    try:
        # Use TF-IDF vectorizer with unigram and bigram representation
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        vectors = vectorizer.fit_transform([processed_job] + processed_resumes)
        
        # Cosine similarity between job vector (index 0) and all resume vectors (index 1 to end)
        similarity_scores = cosine_similarity(vectors[0], vectors[1:])[0]
        
        results = []
        for idx, score in enumerate(similarity_scores):
            rounded_score = round(float(score) * 100, 2)
            results.append({
                'id': resumes_list[idx]['id'],
                'score': rounded_score
            })
        return results
    except Exception:
        # Fallback to zero similarity on error
        return [{'id': r['id'], 'score': 0.0} for r in resumes_list]

def get_local_insights(job_desc, resume_text):
    """
    Generate local word overlaps and differences for basic matching insights.
    """
    if not job_desc or not resume_text:
        return {
            'matched_keywords': [],
            'missing_keywords': [],
            'match_count': 0,
            'missing_count': 0
        }
        
    job_words = set(re.findall(r'\b[a-z]{3,}\b', job_desc.lower())) - STOPWORDS
    resume_words = set(re.findall(r'\b[a-z]{3,}\b', resume_text.lower())) - STOPWORDS
    matched = sorted(list(job_words.intersection(resume_words)))
    missing = sorted(list(job_words - resume_words)) 
    return {
        'matched_keywords': matched[:20],  # Return top 20 keywords
        'missing_keywords': missing[:20],  # Return top 20 missing keywords
        'match_count': len(matched),
        'missing_count': len(missing)
    }
