from datetime import datetime
from app.database import db

class JobDescription(db.Model):
    __tablename__ = 'job_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, default="Untitled Position")
    description_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cascade delete matches if job description is deleted
    matches = db.relationship('MatchResult', backref='job', cascade='all, delete-orphan')


class CandidateResume(db.Model):
    __tablename__ = 'candidate_resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    skills_extracted = db.Column(db.Text, nullable=True)  # Stored as comma-separated values or JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    matches = db.relationship('MatchResult', backref='resume', cascade='all, delete-orphan')


class MatchResult(db.Model):
    __tablename__ = 'match_results'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('candidate_resumes.id', ondelete='CASCADE'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    ai_analysis = db.Column(db.Text, nullable=True)  # JSON-formatted detailed ATS feedback and suggestions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
