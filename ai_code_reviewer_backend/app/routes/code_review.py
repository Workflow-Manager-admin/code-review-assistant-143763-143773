import os
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
from functools import wraps

# For demonstration, we use the OpenAI API. In real scenarios, you might want to adapt this to the LLM or AI provider of your choice.
import requests

blp = Blueprint(
    "Code Review",
    "code_review",
    url_prefix="/api",
    description="Routes for submitting code, retrieving AI-generated code reviews, and getting improvement suggestions."
)


def require_auth(f):
    """
    Decorator to require API Key authentication via an Authorization header.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        expected_token = os.getenv("API_AUTH_TOKEN")
        header = request.headers.get("Authorization", "")
        if not expected_token or not header.startswith("Bearer "):
            abort(401, message="Missing or invalid authorization header.")
        token = header.removeprefix("Bearer ").strip()
        if token != expected_token:
            abort(403, message="Forbidden: Invalid token.")
        return f(*args, **kwargs)
    return decorated


def call_openai_model(prompt, temperature=0.2, max_tokens=512):
    """
    Helper function to call the OpenAI GPT model for code review.
    Replace with your actual model provider if needed.
    """
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OpenAI credentials in environment variable OPENAI_API_KEY")
    api_url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-3.5-turbo",  # You might want to allow model customization.
        "messages": [
            {"role": "system", "content": "You are an expert code reviewer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=40)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI model error: {str(e)}"


# ---- Schemas ----

from marshmallow import Schema, fields

class CodeSubmissionSchema(Schema):
    code = fields.String(required=True, description="The code snippet to review.")
    language = fields.String(required=True, description="Programming language of the code.")

class CodeReviewResponseSchema(Schema):
    review = fields.String(description="AI-generated review of the submitted code.")

class ImprovementSuggestionsSchema(Schema):
    suggestions = fields.String(description="AI-generated suggestions for code improvements.")

class ErrorSchema(Schema):
    code = fields.Integer()
    status = fields.String()
    message = fields.String()
    errors = fields.Dict(keys=fields.String(), values=fields.Raw())

# ---- Endpoints ----

@blp.route('/review')
class CodeReviewAPI(MethodView):
    """
    PUBLIC_INTERFACE
    POST /api/review: Submits code for review, returns AI-generated feedback.
    """
    @blp.arguments(CodeSubmissionSchema)
    @blp.response(200, CodeReviewResponseSchema)
    @blp.response(400, ErrorSchema)
    @blp.response(401, ErrorSchema)
    @blp.response(500, ErrorSchema)
    @require_auth
    def post(self, body):
        """
        Submit code for AI-powered review.

        Returns:
            review (str): AI-generated feedback on the submitted code.
        """
        code = body['code']
        language = body.get('language', 'plaintext')
        if len(code.strip()) == 0 or len(language.strip()) == 0:
            abort(400, message="Both code and language are required.")

        prompt = (
            "Please review the following {} code:\n"
            "-----------------\n"
            "{}\n"
            "-----------------\n"
            "Identify any issues, improvements, or best practices."
        ).format(language, code)
        review = call_openai_model(prompt)
        return {"review": review}


@blp.route('/suggestions')
class ImprovementSuggestionsAPI(MethodView):
    """
    PUBLIC_INTERFACE
    POST /api/suggestions: Submits code and gets improvement suggestions.
    """
    @blp.arguments(CodeSubmissionSchema)
    @blp.response(200, ImprovementSuggestionsSchema)
    @blp.response(400, ErrorSchema)
    @blp.response(401, ErrorSchema)
    @blp.response(500, ErrorSchema)
    @require_auth
    def post(self, body):
        """
        Submit code for AI-powered suggestions.

        Returns:
            suggestions (str): AI-generated suggestions for code improvement.
        """
        code = body['code']
        language = body.get('language', 'plaintext')
        if len(code.strip()) == 0 or len(language.strip()) == 0:
            abort(400, message="Both code and language are required.")

        prompt = (
            "Suggest concrete improvements to the following {} code, explain why each is needed:\n"
            "-----------------\n"
            "{}\n"
            "-----------------"
        ).format(language, code)
        suggestions = call_openai_model(prompt)
        return {"suggestions": suggestions}


@blp.route('/review/test')
class DummyGetReviewAPI(MethodView):
    """
    PUBLIC_INTERFACE
    GET /api/review/test: Return a dummy review result (for dev purpose).
    """
    @require_auth
    def get(self):
        """
        Test endpoint for developers.
        """
        return {"review": "This is a sample review. Your real reviews will appear here."}

# Note: In production, you would have endpoints to retrieve previous review results, manage users, etc.
