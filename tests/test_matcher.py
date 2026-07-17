from app.services.matcher import preprocess_text, match_resumes, get_local_insights

def test_preprocess_text():
    """Verify text preprocessing normalizes punctuation, cases, and filters stopwords."""
    raw_text = "Experienced Developer seeking a Python and SQL role! (Hybrid)"
    processed = preprocess_text(raw_text)
    
    tokens = processed.split()
    assert "developer" in tokens
    assert "python" in tokens
    assert "sql" in tokens
    assert "role" in tokens
    assert "hybrid" in tokens
    
    # Verify stopwords are removed
    assert "and" not in tokens
    assert "a" not in tokens

def test_match_resumes_accuracy_and_ranking():
    """Verify that match scores represent appropriate rankings and bounds (0% to 100%)."""
    job_desc = "Looking for a React developer with Tailwind CSS and TypeScript skills."
    resumes = [
        {'id': 101, 'text': "React developer specializing in TypeScript, HTML, and Tailwind CSS design."}, # High match
        {'id': 102, 'text': "Software engineer with Node.js and TypeScript background. Learning React."},  # Medium match
        {'id': 103, 'text': "Data Analyst proficient in Python, SQL, Tableau, and Excel reporting."}       # Low/No match
    ]
    
    results = match_resumes(job_desc, resumes)
    assert len(results) == 3
    
    # Verify bounds
    for r in results:
        assert 0.0 <= r['score'] <= 100.0
        
    # Verify ranking correctness
    scores_map = {item['id']: item['score'] for item in results}
    assert scores_map[101] > scores_map[102]
    assert scores_map[102] > scores_map[103]

def test_get_local_insights():
    """Verify overlapping and missing keyword logic computes statistics accurately."""
    job_desc = "React TypeScript Redux Jest Docker"
    resume_text = "React TypeScript Angular Vue Webpack Docker"
    
    insights = get_local_insights(job_desc, resume_text)
    
    # Check overlaps
    assert "react" in insights['matched_keywords']
    assert "typescript" in insights['matched_keywords']
    assert "docker" in insights['matched_keywords']
    
    # Check gaps
    assert "redux" in insights['missing_keywords']
    assert "jest" in insights['missing_keywords']
    
    # Check counts
    assert insights['match_count'] == 3
    assert insights['missing_count'] == 2
