import os
import re
import json
import google.generativeai as genai
from app.services.matcher import get_local_insights

def generate_ai_analysis(job_desc, resume_text, api_key=None):
    """
    Generate structured ATS insights and matching score using Gemini API.
    If the key is missing or the API call fails, falls back to local NLP statistics.
    """
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY', '')

    if not api_key:
        # Graceful fallback to local analysis
        return get_fallback_analysis(job_desc, resume_text, "Gemini API key is not configured. Local parsing active.")

    try:
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash for fast and cost-effective text analysis
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
You are an expert Executive Recruiter and ATS (Applicant Tracking System) optimizer.
Compare the following Candidate Resume against the Job Description.

Job Description:
\"\"\"{job_desc}\"\"\"

Resume:
\"\"\"{resume_text}\"\"\"

Provide your analysis in a structured JSON format. You MUST return ONLY valid JSON matching this schema, without any Markdown formatting (no ```json or ``` tags):
{{
  "ats_score": <int: score between 0 and 100 representing job description fit>,
  "summary": "<str: 2-3 sentence overview of candidate suitability>",
  "matched_skills": [<list of strings: key skills matched between job and resume>],
  "missing_skills": [<list of strings: crucial skills required by the job but missing in the resume>],
  "strengths": [<list of strings: candidates key strengths relative to the role>],
  "weaknesses_or_gaps": [<list of strings: clear areas of gaps, mismatch, or missing credentials>],
  "improvement_tips": [<list of strings: concrete steps the candidate can take to align their resume with this job description>]
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean potential markdown wrappers
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n', '', text)
            text = re.sub(r'\n```$', '', text)
            text = text.strip()
            
        data = json.loads(text)
        
        # Validate critical structure keys
        required_keys = ['ats_score', 'summary', 'matched_skills', 'missing_skills', 'strengths', 'weaknesses_or_gaps', 'improvement_tips']
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required JSON response key: {key}")
                
        # Ensure ats_score is an integer in bounds
        data['ats_score'] = min(max(int(data['ats_score']), 0), 100)
        data['is_ai_powered'] = True
        return data
        
    except Exception as e:
        # Fallback to local statistics if Gemini raises error
        error_msg = f"Gemini API request failed: {str(e)}. Falling back to local NLP analysis."
        return get_fallback_analysis(job_desc, resume_text, error_msg)

def get_fallback_analysis(job_desc, resume_text, info_message=""):
    """Generate a structured response using local matching metrics as a backup."""
    local_insights = get_local_insights(job_desc, resume_text)
    
    # Calculate a proxy ATS score based on keyword overlap
    match_count = local_insights['match_count']
    total_count = match_count + local_insights['missing_count']
    ats_score = round((match_count / total_count * 100) if total_count > 0 else 0.0)
    
    # Standardize output format
    return {
        "ats_score": int(ats_score),
        "summary": f"Resume analyzed using local text patterns. {info_message}",
        "matched_skills": local_insights['matched_keywords'][:10],
        "missing_skills": local_insights['missing_keywords'][:10],
        "strengths": [f"Matches {match_count} keywords from the job description."] if match_count > 0 else ["Evaluated using keyword extraction."],
        "weaknesses_or_gaps": [f"Missing {len(local_insights['missing_keywords'])} key vocabulary terms found in the job description."] if len(local_insights['missing_keywords']) > 0 else [],
        "improvement_tips": [
            f"Incorporate missing keywords like: {', '.join(local_insights['missing_keywords'][:5])} into your profile."
        ] if len(local_insights['missing_keywords']) > 0 else ["Review requirements and add relevant domain terminology."],
        "is_ai_powered": False
    }
