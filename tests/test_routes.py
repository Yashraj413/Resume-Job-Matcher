import io
import pytest
from app import create_app
from app.database import db
from app.models import JobDescription, CandidateResume, MatchResult

@pytest.fixture
def app():
    """Create a Flask application instance configured for tests."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "GEMINI_API_KEY": ""  # Leave empty to test standard local NLP fallback flows
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create an HTTP test client."""
    return app.test_client()

def test_index_dashboard_loads(client):
    """Verify that the dashboard loads successfully and contains title cues."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Active Job Openings" in response.data
    assert b"Initialize Recruitment Pipeline" in response.data

def test_create_job_stores_record_correctly(client):
    """Verify that submitting the job creation form persists a new JobDescription."""
    response = client.post('/job/create', data={
        'title': 'QA Automation Specialist',
        'description_text': 'Selenium Python pytest integration testing'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"QA Automation Specialist" in response.data

def test_upload_resumes_performs_matching(client):
    """Verify that multipart uploads parse files, compute scores, and save matches."""
    # 1. Initialize a job position description
    client.post('/job/create', data={
        'title': 'Golang Architect',
        'description_text': 'Go backend microservices Kubernetes Docker gRPC'
    })
    
    # 2. Package resumes as file uploads
    data = {
        'resumes': [
            (io.BytesIO(b"Golang backend developer building microservices in Kubernetes"), "go_dev.txt"),
            (io.BytesIO(b"Frontend React designer focused on Tailwind and CSS grid"), "react_dev.txt")
        ]
    }
    
    # 3. Post uploads to matcher route
    response = client.post('/job/1/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert b"Processed 2 resumes successfully" in response.data
    
    # 4. Assert database persistence & ranking logic (Golang developer must score higher for Golang job)
    job = db.session.get(JobDescription, 1)
    assert len(job.matches) == 2
    
    matches = db.session.scalars(
        db.select(MatchResult)
        .filter_by(job_id=1)
        .order_by(MatchResult.similarity_score.desc())
    ).all()
    assert matches[0].resume.filename == "go_dev.txt"
    assert matches[1].resume.filename == "react_dev.txt"
    assert matches[0].similarity_score > matches[1].similarity_score

def test_api_match_json_endpoint(client):
    """Verify the programmatic REST JSON match API functions correctly."""
    payload = {
        "job_description": "Kubernetes Administrator DevOps",
        "resumes": [
            {"filename": "res1.txt", "text": "AWS DevOps engineer with extensive Kubernetes clusters automation experience"},
            {"filename": "res2.txt", "text": "UI Designer working with Figma sketches"}
        ]
    }
    response = client.post('/api/match', json=payload)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "results" in data
    assert len(data['results']) == 2
    assert data['results'][0]['score'] > data['results'][1]['score']
    assert "insights" in data['results'][0]
