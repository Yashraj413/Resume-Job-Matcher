from flask import Blueprint, jsonify, request
from app.services.parser import extract_text
from app.services.matcher import match_resumes, get_local_insights
import io

api_bp = Blueprint('api', __name__)

@api_bp.route('/match', methods=['POST'])
def api_match():
    """
    Programmatic API endpoint to match resumes against a job description.
    Supports both JSON and Multipart-form payloads.
    """
    # 1. Handle multipart form uploads
    if not request.is_json:
        job_desc = request.form.get('job_description')
        files = request.files.getlist('resumes')
        
        if not job_desc or not files or files[0].filename == '':
            return jsonify({'error': 'Missing job_description or resumes files.'}), 400
            
        parsed_resumes = []
        for file in files:
            try:
                file_bytes = file.read()
                if not file_bytes:
                    continue
                text = extract_text(file.filename, io.BytesIO(file_bytes))
                if text.strip():
                    parsed_resumes.append({
                        'filename': file.filename,
                        'text': text
                    })
            except Exception as e:
                return jsonify({'error': f"Failed to parse '{file.filename}': {str(e)}"}), 400
                
        if not parsed_resumes:
            return jsonify({'error': 'No valid text could be parsed from the files.'}), 400
            
        resumes_payload = [{'id': idx, 'text': item['text']} for idx, item in enumerate(parsed_resumes)]
        scores = match_resumes(job_desc, resumes_payload)
        scores_map = {item['id']: item['score'] for item in scores}
        
        results = []
        for idx, item in enumerate(parsed_resumes):
            results.append({
                'filename': item['filename'],
                'score': scores_map.get(idx, 0.0),
                'insights': get_local_insights(job_desc, item['text'])
            })
            
        return jsonify({'results': results})

    # 2. Handle JSON payloads
    data = request.get_json()
    job_desc = data.get('job_description')
    resumes = data.get('resumes')
    
    if not job_desc or not resumes:
        return jsonify({'error': 'Missing job_description or resumes list in request body.'}), 400
        
    resumes_payload = []
    for idx, item in enumerate(resumes):
        if isinstance(item, str):
            resumes_payload.append({
                'id': idx,
                'text': item,
                'filename': f'candidate_{idx + 1}.txt'
            })
        elif isinstance(item, dict):
            resumes_payload.append({
                'id': idx,
                'text': item.get('text', ''),
                'filename': item.get('filename', f'candidate_{idx + 1}.txt')
            })
            
    if not resumes_payload:
        return jsonify({'error': 'No valid resume texts provided.'}), 400
        
    scores = match_resumes(job_desc, resumes_payload)
    scores_map = {item['id']: item['score'] for item in scores}
    
    results = []
    for item in resumes_payload:
        idx = item['id']
        results.append({
            'filename': item['filename'],
            'score': scores_map.get(idx, 0.0),
            'insights': get_local_insights(job_desc, item['text'])
        })
        
    return jsonify({'results': results})
