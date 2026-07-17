import os
from app import create_app

# Instantiate the application factory
app = create_app()

if __name__ == '__main__':
    # Retrieve port from environment, defaulting to 10000 for local/Render deployment
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
