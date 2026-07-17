from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from app.config import Config
from app.database import db

# Rate Limiter setup (defaults to client IP address check)
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    # Specify the relative path back to root templates/static directories
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)
    
    # Bind Database
    db.init_app(app)
    
    # Bind Security Headers (HSTS, CSRF assistance, secure frame headers)
    # Content Security Policy (CSP) is set to None to allow flexible loading of Google Fonts/Icons
    # force_https is set to False to permit local development access on HTTP
    Talisman(app, content_security_policy=None, force_https=False)
    
    # Bind Rate Limiter
    limiter.init_app(app)
    
    # Register template filters
    import json
    @app.template_filter('json_loads')
    def json_loads_filter(s):
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}
            
    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create DB tables inside context if they do not exist
    with app.app_context():
        db.create_all()
        
    return app
