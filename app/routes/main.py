from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.database import db
from app.models import JobDescription, CandidateResume, MatchResult
from app.services.parser import extract_text
from app.services.matcher import match_resumes
from app.services.ai_insights import generate_ai_analysis
import io
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render dashboard displaying all active job descriptions and metrics."""
    jobs = db.session.scalars(db.select(JobDescription).order_by(JobDescription.created_at.desc())).all()
    total_jobs = len(jobs)
    total_resumes = db.session.scalar(db.select(db.func.count()).select_from(CandidateResume))
    
    matches = db.session.scalars(db.select(MatchResult)).all()
    avg_score = round(sum(m.similarity_score for m in matches) / len(matches), 1) if matches else 0.0
    
    return render_template(
        'dashboard.html', 
        jobs=jobs, 
        total_jobs=total_jobs, 
        total_resumes=total_resumes, 
        avg_score=avg_score
    )

@main_bp.route('/job/create', methods=['POST'])
def create_job():
    """Create a new job description entry in the database."""
    title = request.form.get('title', 'Untitled Position').strip()
    description = request.form.get('description_text', '').strip()
    
    if not description:
        flash("Job description text cannot be empty.", "danger")
        return redirect(url_for('main.index'))
        
    job = JobDescription(title=title, description_text=description)
    db.session.add(job)
    db.session.commit()
    
    flash(f"Job profile for '{title}' created successfully!", "success")
    return redirect(url_for('main.job_details', job_id=job.id))

@main_bp.route('/job/<int:job_id>')
def job_details(job_id):
    """View job description and lists of uploaded candidates with similarity scores."""
    job = db.get_or_404(JobDescription, job_id)
    matches = db.session.scalars(
        db.select(MatchResult)
        .filter_by(job_id=job_id)
        .join(CandidateResume)
        .order_by(MatchResult.similarity_score.desc())
    ).all()
    return render_template('job_details.html', job=job, matches=matches)

@main_bp.route('/job/<int:job_id>/upload', methods=['POST'])
def upload_resumes(job_id):
    """Handle resume uploads, parse text, compute scores, generate AI insights, and save matches."""
    job = db.get_or_404(JobDescription, job_id)
    files = request.files.getlist('resumes')
    
    if not files or not files[0] or files[0].filename == '':
        flash("No resume files selected for upload.", "warning")
        return redirect(url_for('main.job_details', job_id=job_id))
        
    success_count = 0
    fail_count = 0
    parsed_resumes = []
    
    for file in files:
        if not file.filename:
            continue
            
        filename = file.filename
        try:
            # Read files directly into memory streams
            file_bytes = file.read()
            if not file_bytes:
                fail_count += 1
                continue
                
            extracted_text = extract_text(filename, io.BytesIO(file_bytes))
            if not extracted_text.strip():
                fail_count += 1
                continue
                
            resume = CandidateResume(filename=filename, extracted_text=extracted_text)
            db.session.add(resume)
            db.session.flush()  # Flush to get the database auto-increment ID
            
            parsed_resumes.append({
                'id': resume.id,
                'resume_obj': resume,
                'text': extracted_text
            })
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Error parsing resume file '{filename}': {str(e)}")
            
    if not parsed_resumes:
        flash(f"Failed to process uploaded resumes. (Successful: 0, Failed: {fail_count})", "danger")
        return redirect(url_for('main.job_details', job_id=job_id))
        
    # Run batch text matching calculations
    resumes_payload = [{'id': item['id'], 'text': item['text']} for item in parsed_resumes]
    match_scores = match_resumes(job.description_text, resumes_payload)
    scores_map = {item['id']: item['score'] for item in match_scores}
    
    api_key = current_app.config.get('GEMINI_API_KEY')
    
    # Process structured insights and store matches
    for item in parsed_resumes:
        res_id = item['id']
        txt = item['text']
        base_score = scores_map.get(res_id, 0.0)
        
        # Query AI analysis (falls back to local text matches if key/connection is missing)
        analysis_report = generate_ai_analysis(job.description_text, txt, api_key)
        
        # Override score with AI ATS score if AI is active
        final_score = base_score
        if analysis_report and analysis_report.get('is_ai_powered'):
            final_score = float(analysis_report.get('ats_score', base_score))
            
        match_result = MatchResult(
            job_id=job_id,
            resume_id=res_id,
            similarity_score=final_score,
            ai_analysis=json.dumps(analysis_report)
        )
        db.session.add(match_result)
        
    db.session.commit()
    
    flash(f"Processed {success_count} resumes successfully! (Failed: {fail_count})", "success")
    return redirect(url_for('main.job_details', job_id=job_id))

@main_bp.route('/match/<int:match_id>')
def match_report(match_id):
    """Render comprehensive report for a single match (ATS score, keyword gaps, improvements)."""
    match = db.get_or_404(MatchResult, match_id)
    try:
        analysis_data = json.loads(match.ai_analysis) if match.ai_analysis else {}
    except ValueError:
        analysis_data = {}
    return render_template('match_report.html', match=match, analysis=analysis_data)

@main_bp.route('/history')
def history():
    """Display history of all candidate resume matches."""
    matches = db.session.scalars(
        db.select(MatchResult)
        .join(JobDescription)
        .join(CandidateResume)
        .order_by(MatchResult.created_at.desc())
    ).all()
    return render_template('history.html', matches=matches)

@main_bp.route('/job/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job description and its associated matches/candidate records."""
    job = db.get_or_404(JobDescription, job_id)
    db.session.delete(job)
    db.session.commit()
    flash(f"Job description for '{job.title}' deleted successfully.", "info")
    return redirect(url_for('main.index'))
