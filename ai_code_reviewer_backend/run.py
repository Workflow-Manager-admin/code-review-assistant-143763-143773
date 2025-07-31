# PUBLIC_INTERFACE
"""
Run entrypoint for the AI Code Reviewer Flask Backend.
- Loads environment variables from a .env file (if present) for local/dev use.
- Launches the Flask app.
"""

import os

# Load environment variables from '.env' if present (for development/local runs)
try:
    from dotenv import load_dotenv

    # Load .env file if it exists in the project root or workspace
    dotenv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"
    )
    load_dotenv(dotenv_path=dotenv_path, override=True)
except ImportError:
    # If python-dotenv isn't installed, continue; assume prod already sets env vars
    pass

from app import app

if __name__ == "__main__":
    # Flask will use env var FLASK_ENV if present, default is "production"
    app.run()
